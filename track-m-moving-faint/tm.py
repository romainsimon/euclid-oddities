"""Track M: proper motions of faint Euclid DR1 point sources against Legacy Surveys DR10 (no model call).

  tm.py dev            every DR1 tile whose centre lies in the development box (RA 50-60, Dec -50..-40)
  tm.py all            every DR1 tile (tiles without Legacy Surveys DR10 south coverage stop early)
  tm.py <tile> ...     the given tiles
Output in $TRACKM_HOME (default ~/trackm): tiles/<tile>.csv.gz (one row per Euclid point-like source) and
tiles/<tile>.json (epochs, astrometric tie, Gaia check, galaxy control). Resumable: finished tiles are skipped.

Method (per tile):
  1. Euclid epoch = middle of the VIS observations of the tile (dr1.mosaic_product).
  2. Euclid MER sources with VIS (PSF) < 24, spurious_flag = 0.
  3. Legacy Surveys DR10 south Tractor catalogues of the bricks over the tile (brick_primary only).
  4. Pairs = mutual nearest neighbours within 3 arcsec. This loses motions above about 0.35 arcsec/yr.
  5. Tie: galaxies (not PSF in LS, point_like_prob < 0.2, VIS 19.5-23, pair within 0.6 arcsec, not a Gaia reference source)
     define zero motion; median offset per cell of a 4 x 4 grid, cells with fewer than 15 galaxies use the tile median.
  6. Motion = (Euclid - LS - tie) / baseline. Baseline: Euclid epoch minus the LS mid-epoch (mjd_min, mjd_max); for LS Gaia
     reference stars, whose LS position is the Gaia position at ref_epoch, Euclid epoch minus ref_epoch.
Checks stored per tile: measured minus Gaia motion for Gaia stars; the motions "measured" for galaxies, which cannot move.
"""
from __future__ import annotations

import io
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from astropy.io import fits
from astropy.time import Time
from scipy.spatial import cKDTree

HOME = Path(os.environ.get("TRACKM_HOME", Path.home() / "trackm"))
EU = "https://eas.esac.esa.int/tap-server/tap"
NERSC = "https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr10/south/tractor"
DEV = dict(ra=(50.0, 60.0), dec=(-50.0, -40.0))
VIS_FLUX_MIN = 0.9          # microJy, VIS PSF flux (mag 24.0)
BRICK_R = 0.55              # deg, bricks whose centre is this close to the tile centre
PAIR_R = 3.0                # arcsec
GRID, CELL_MIN = 4, 15
POINT_MIN = 0.5             # point_like_prob kept in the output table
ROW_CAP = 45000             # rows per Euclid query; the archive truncates answers at 50,000
CTRL_PM = 20.0              # mas/yr, extended sources above this are kept as control rows
LS_COLS = ["ra", "dec", "type", "ra_ivar", "dec_ivar", "mjd_min", "mjd_max", "ref_cat", "ref_epoch", "pmra", "pmdec", "flux_g", "flux_r", "flux_i",
           "flux_z", "flux_w1", "flux_w2", "flux_ivar_r", "flux_ivar_z", "maskbits", "fitbits", "nobs_r", "nobs_z", "nobs_i"]
EU_COLS = ("object_id, right_ascension, declination, flux_vis_psf, fluxerr_vis_psf, flux_y_2fwhm_aper, fluxerr_y_2fwhm_aper, flux_j_2fwhm_aper, "
           "fluxerr_j_2fwhm_aper, flux_h_2fwhm_aper, fluxerr_h_2fwhm_aper, point_like_prob, spurious_flag, det_quality_flag, flag_vis, gaia_id, "
           "mumax_minus_mag, semimajor_axis")
_bricks = None
_eu_lock = __import__("threading").Lock()   # the Euclid archive returns empty tables when heavy jobs run in parallel


def tap_sync(q):
    for k in range(4):
        try:
            r = requests.post(EU + "/sync", data=dict(REQUEST="doQuery", LANG="ADQL", FORMAT="csv", QUERY=q), timeout=300)
            if r.status_code == 200 and not r.text.lstrip().startswith("<"):
                return pd.read_csv(io.StringIO(r.text))
        except Exception:
            pass
        time.sleep(10 * (k + 1))
    raise RuntimeError("Euclid sync query failed")


def tap_async(q, timeout=3600):
    for k in range(3):
        try:
            r = requests.post(EU + "/async", data=dict(REQUEST="doQuery", LANG="ADQL", FORMAT="csv", PHASE="RUN", QUERY=q), timeout=120, allow_redirects=False)
            job = r.headers.get("Location") or r.url
            t0 = time.time()
            while time.time() - t0 < timeout:
                ph = requests.get(job + "/phase", timeout=60).text.strip()
                if ph == "COMPLETED":
                    return pd.read_csv(io.StringIO(requests.get(job + "/results/result", timeout=900).text))
                if ph in ("ERROR", "ABORTED"):
                    raise RuntimeError("job " + ph)
                time.sleep(5)
        except Exception as e:
            err = repr(e)[:150]
        time.sleep(30 * (k + 1))
    raise RuntimeError("Euclid async query failed: " + err)


def brick(name):
    """Reduced Tractor catalogue of one brick (primary sources), cached."""
    d = HOME / "bricks"
    d.mkdir(parents=True, exist_ok=True)
    f = d / f"{name}.csv.gz"
    if f.exists():
        try:
            return pd.read_csv(f)
        except Exception:      # half-written by another thread, or damaged: fetch again
            pass
    tmp = d / f"{name}.{os.getpid()}.{__import__('threading').get_ident()}.tmp.csv.gz"
    for k in range(4):
        try:
            r = requests.get(f"{NERSC}/{name[:3]}/tractor-{name}.fits", timeout=(15, 900))
            if r.status_code == 404:
                pd.DataFrame(columns=LS_COLS).to_csv(tmp, index=False)
                os.replace(tmp, f)
                return pd.read_csv(f)
            if r.status_code == 200:
                t = fits.open(io.BytesIO(r.content))[1].data
                k_ = t["brick_primary"]
                D = pd.DataFrame({c: (np.asarray(t[c][k_]).astype(str) if t[c].dtype.kind in "SU"
                                      else np.asarray(t[c][k_]).byteswap().view(t[c].dtype.newbyteorder("="))) for c in LS_COLS})
                D.to_csv(tmp, index=False)
                os.replace(tmp, f)
                return pd.read_csv(f)
        except Exception:
            pass
        time.sleep(15 * (k + 1))
    raise RuntimeError("brick " + name + " failed")


def rob(v):
    v = np.asarray(v, float)
    v = v[np.isfinite(v)]
    return float(1.4826 * np.median(np.abs(v - np.median(v)))) if len(v) else float("nan")


def one(tile):
    global _bricks
    out = HOME / "tiles"
    out.mkdir(parents=True, exist_ok=True)
    fj = out / f"{tile}.json"
    if fj.exists():
        return "skip"
    S = dict(tile=int(tile))
    m = tap_sync("SELECT first_observation_date_time, last_observation_date_time, ra, dec FROM dr1.mosaic_product "
                 f"WHERE tile_index = {tile} AND product_type = 'DpdMerBksMosaic' AND filter_name = 'VIS'")
    if not len(m):
        fj.write_text(json.dumps(dict(S, status="no VIS mosaic")))
        return "no mosaic"
    t1, t2 = (Time(str(m[c][0]).replace(" ", "T")).mjd for c in ("first_observation_date_time", "last_observation_date_time"))
    epoch, ra0, dec0 = (t1 + t2) / 2, float(m.ra[0]), float(m.dec[0])
    S.update(ra=ra0, dec=dec0, vis_first_mjd=t1, vis_last_mjd=t2, epoch_mjd=epoch)
    where = f"FROM dr1.mer_catalogue_wide_survey WHERE tile_index = {tile} AND flux_vis_psf > {VIS_FLUX_MIN} AND spurious_flag = 0"
    with _eu_lock:
        n_true = int(tap_sync("SELECT COUNT(*) AS n " + where).n[0])
        if n_true == 0:
            E = pd.DataFrame()
        elif n_true <= ROW_CAP:
            E = tap_async(f"SELECT {EU_COLS} " + where)
        else:   # the archive cuts an answer at 50,000 rows: read the tile in declination strips
            k = int(np.ceil(n_true / (ROW_CAP * 0.6)))
            edges = np.linspace(dec0 - 0.45, dec0 + 0.45, k + 1)
            E = pd.concat([tap_async(f"SELECT {EU_COLS} " + where + f" AND declination >= {lo:.6f} AND declination < {hi:.6f}")
                           for lo, hi in zip(edges[:-1], edges[1:])], ignore_index=True)
    S["n_euclid"] = n_true
    E = E.apply(pd.to_numeric, errors="coerce")      # strips can come back with text columns when a value is missing
    if len(E) != n_true:
        raise RuntimeError(f"Euclid returned {len(E)} rows, count says {n_true}")
    if len(E) < 2000:
        fj.write_text(json.dumps(dict(S, status="too few Euclid sources")))
        return "few"
    E["vis"] = 23.9 - 2.5 * np.log10(E.flux_vis_psf)
    b = _bricks
    d = np.hypot((b["ra"] - ra0) * np.cos(np.radians(dec0)), b["dec"] - dec0)
    L = pd.concat([brick(n) for n in b["brickname"][d < BRICK_R]], ignore_index=True)
    S["n_ls"] = len(L)
    if len(L) < 2000:
        fj.write_text(json.dumps(dict(S, status="too few LS sources")))
        return "no LS"
    L["type"] = L.type.astype(str).str.strip()
    L["ref_cat"] = L.ref_cat.fillna("").astype(str).str.strip().replace("nan", "")
    L["mjd"] = (L.mjd_min + L.mjd_max) / 2

    def xy(ra, dec):
        return np.c_[(np.asarray(ra) - ra0) * np.cos(np.radians(dec0)) * 3600, (np.asarray(dec) - dec0) * 3600]

    pe, pl = xy(E.right_ascension, E.declination), xy(L.ra, L.dec)
    dist, idx = cKDTree(pl).query(pe, k=2)
    back = cKDTree(pe).query(pl)[1]
    M = E.copy()
    M["sep"], M["sep2"] = dist[:, 0], dist[:, 1]
    M["mutual"] = back[idx[:, 0]] == np.arange(len(E))
    for c in ("ra", "dec", "type", "ref_cat", "ref_epoch", "pmra", "pmdec", "mjd", "mjd_min", "mjd_max", "flux_g", "flux_r", "flux_i", "flux_z", "flux_w1",
              "flux_w2", "flux_ivar_r", "flux_ivar_z", "ra_ivar", "dec_ivar", "maskbits", "fitbits", "nobs_r", "nobs_z"):
        M["ls_" + c] = L[c].values[idx[:, 0]]
    M["matched"] = M.mutual & (M.sep < PAIR_R)
    M["dx"] = (M.right_ascension - M.ls_ra) * np.cos(np.radians(dec0)) * 3600
    M["dy"] = (M.declination - M.ls_dec) * 3600
    gal = M[M.matched & (M.ls_type != "PSF") & (M.point_like_prob < 0.2) & (M.sep < 0.6) & (M.vis > 19.5) & (M.vis < 23.0) & (M.ls_ref_cat == "")]
    S["n_tie"] = len(gal)
    if len(gal) < 100:
        fj.write_text(json.dumps(dict(S, status="too few galaxies for the tie")))
        return "no tie"
    gx, gy = float(gal.dx.median()), float(gal.dy.median())
    half = BRICK_R * 3600
    M["cell"] = (np.clip(((pe[:, 0] + half) / (2 * half) * GRID).astype(int), 0, GRID - 1) * GRID
                 + np.clip(((pe[:, 1] + half) / (2 * half) * GRID).astype(int), 0, GRID - 1))
    off = M.loc[gal.index].groupby("cell").agg(n_cell=("dx", "size"), ox=("dx", "median"), oy=("dy", "median"),
                                              sx=("dx", rob), sy=("dy", rob))
    off.loc[off.n_cell < CELL_MIN, ["ox", "oy"]] = [gx, gy]
    M = M.join(off, on="cell")
    M["ox"], M["oy"], M["n_cell"] = M.ox.fillna(gx), M.oy.fillna(gy), M.n_cell.fillna(0)
    M["tie_err"] = np.where(M.n_cell >= CELL_MIN, np.hypot(M.sx, M.sy) / np.sqrt(2 * M.n_cell.clip(lower=1)), rob(gal.dx) / np.sqrt(CELL_MIN))
    M["ddx"], M["ddy"] = M.dx - M.ox, M.dy - M.oy
    isg = M.ls_ref_cat.str.startswith("G")
    ref = Time(np.where(M.ls_ref_epoch > 0, M.ls_ref_epoch, 2016.0), format="jyear").mjd
    M["base_yr"] = np.where(isg, (epoch - ref) / 365.25, (epoch - M.ls_mjd) / 365.25)
    M["pmx"], M["pmy"] = M.ddx / M.base_yr * 1000, M.ddy / M.base_yr * 1000
    M["pm"] = np.hypot(M.pmx, M.pmy)
    S.update(tie_dx_mas=gx * 1000, tie_dy_mas=gy * 1000, tie_cells=int((off.n_cell >= CELL_MIN).sum()),
             tie_cell_rms_mas=float(np.hypot(off.ox.std(), off.oy.std()) * 1000) if len(off) > 1 else None,
             baseline_yr=float(M.base_yr[M.matched & ~isg].median()), ls_mid_mjd=float(L.mjd[L.mjd_min > 0].median()))
    g = M.loc[gal.index]
    S["gal_scatter_mas"] = {f"{a}-{b_}": [int(((g.vis >= a) & (g.vis < b_)).sum()), rob(g.ddx[(g.vis >= a) & (g.vis < b_)]) * 1000,
                                          rob(g.ddy[(g.vis >= a) & (g.vis < b_)]) * 1000] for a, b_ in ((19.5, 21), (21, 22), (22, 23))}
    # control: every matched galaxy (not only the tie sample), same magnitude bins as the search
    ctl = M[M.matched & (M.point_like_prob < 0.2) & (M.ls_type != "PSF") & (M.ls_ref_cat == "") & (M.base_yr > 3)]
    S["control"] = {f"{a}-{b_}": dict(n=int(((ctl.vis >= a) & (ctl.vis < b_)).sum()),
                                      **{f"gt{t}": int(((ctl.vis >= a) & (ctl.vis < b_) & (ctl.pm > t)).sum()) for t in (20, 30, 50, 75, 100, 150, 250)})
                    for a, b_ in ((20.5, 21.5), (21.5, 22.5), (22.5, 23.5), (23.5, 24.0))}
    gs = M[M.matched & isg & (M.point_like_prob > 0.9) & np.isfinite(M.ls_pmra) & (np.hypot(M.ls_pmra, M.ls_pmdec) > 0) & (M.vis > 18.5)]
    if len(gs) > 10:
        S["gaia_check"] = dict(n=len(gs), med_dx=float((gs.pmx - gs.ls_pmra).median()), med_dy=float((gs.pmy - gs.ls_pmdec).median()),
                               sd_x=rob(gs.pmx - gs.ls_pmra), sd_y=rob(gs.pmy - gs.ls_pmdec))
    # control rows: extended sources that "moved", written with the same columns so that the candidate cuts can be applied to them
    G_ = ctl[ctl.pm > CTRL_PM].drop(columns=["mutual", "sx", "sy"])
    G_.insert(0, "tile", int(tile))
    G_.round(6).to_csv(out / f"{tile}_gal.csv.gz", index=False)
    S["n_control_rows"] = len(G_)
    P = M[M.point_like_prob >= POINT_MIN].drop(columns=["mutual", "sx", "sy"])
    P.insert(0, "tile", int(tile))
    P.round(6).to_csv(out / f"{tile}.csv.gz", index=False)
    S.update(status="ok", n_point=len(P), n_point_matched=int(P.matched.sum()))
    fj.write_text(json.dumps(S))
    return "ok"


def main():
    global _bricks
    _bricks = fits.open(HOME / "bricks.fits.gz")[1].data
    T = pd.read_csv(HOME / "tiles.csv").dropna()
    if sys.argv[1] == "dev":
        T = T[(T.ra >= DEV["ra"][0]) & (T.ra < DEV["ra"][1]) & (T.dec >= DEV["dec"][0]) & (T.dec < DEV["dec"][1])]
        tiles = sorted(T.tile_index.astype(np.int64))
    elif sys.argv[1] == "all":
        tiles = sorted(T.tile_index.astype(np.int64))
    else:
        tiles = [int(x) for x in sys.argv[1:]]
    print(f"{len(tiles)} tiles", flush=True)
    t0, n = time.time(), {}

    def safe(t):
        try:
            return one(t)
        except Exception as e:
            return "error: " + repr(e)[:120]
    with ThreadPoolExecutor(3) as ex:
        for i, (t, r) in enumerate(zip(tiles, ex.map(safe, tiles)), 1):
            n[r.split(":")[0]] = n.get(r.split(":")[0], 0) + 1
            if r.startswith("error"):
                print(t, r, flush=True)
            if i % 10 == 0 or i == len(tiles):
                print(f"{i}/{len(tiles)} in {(time.time() - t0) / 60:.0f} min {n}", flush=True)


if __name__ == "__main__":
    main()
