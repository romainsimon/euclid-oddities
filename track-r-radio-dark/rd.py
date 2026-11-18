"""Radio-bright, Euclid-dark sources: catalogue stage (no model call).

  parent            RACS-mid sources (CASDA TAP) over every 5 x 5 deg box that holds a DR1 tile -> parent.csv
  select            compact, isolated, bright subset + one control position per source -> sample.csv
  euclid [region]   one 20 arcsec cone on dr1.mer_catalogue_wide_survey per position (source and control) -> cones.jsonl
                    region "dev" = development box only; "all" = everything (resumable, answered positions are skipped)

Data folder: $RADIODARK_HOME (default ~/radiodark). tiles.csv (tile_index, ra, dec of every DR1 tile) must be there.
Positions use RACS-mid `ra` and `dec_corr` (declination after the survey's declination-dependent correction).
"""
from __future__ import annotations

import io
import json
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from scipy.spatial import cKDTree

HOME = Path(os.environ.get("RADIODARK_HOME", Path.home() / "radiodark"))
CASDA = "https://casda.csiro.au/casda_vo_tools/tap/sync"
EUCLID = "https://eas.esac.esa.int/tap-server/tap/sync"
RACS = "AS110.racs_mid_sources_v01"
MER = "dr1.mer_catalogue_wide_survey"
BOX = 5.0                      # deg, parent download boxes
TILE_R = 0.36                  # deg, a source is "on a tile" when a tile centre is this close (tile half-diagonal 0.354)
DEV = dict(ra=(50.0, 60.0), dec=(-50.0, -40.0))   # development region: every threshold is tuned here only
# selection (frozen in the amendment before the non-development sky is looked at)
PEAK_MIN = 5.0                 # mJy/beam
SNR_MIN = 20.0                 # peak / local noise
ISO = 90.0                     # arcsec, no other RACS-mid source of any flux this close
CONE = 20.0                    # arcsec, Euclid cone per position
CTRL_OFF = 60.0                # arcsec, control position = source position shifted north by this
COLS = ("object_id, right_ascension, declination, tile_index, flux_vis_psf, flux_vis_2fwhm_aper, fluxerr_vis_2fwhm_aper, "
        "flux_y_2fwhm_aper, flux_j_2fwhm_aper, flux_h_2fwhm_aper, fluxerr_h_2fwhm_aper, flux_detection_total, vis_det, "
        "spurious_flag, det_quality_flag, flag_vis, flag_h, point_like_prob, semimajor_axis, mumax_minus_mag")


def tap(url, q, timeout=300, tries=4):
    err = None
    for k in range(tries):
        try:
            r = requests.post(url, data=dict(REQUEST="doQuery", LANG="ADQL", FORMAT="csv", QUERY=q), timeout=timeout)
            if r.status_code == 200 and not r.text.lstrip().startswith("<"):
                return pd.read_csv(io.StringIO(r.text))
            err = f"{r.status_code} {r.text[:200]}"
        except Exception as e:  # network errors are retried
            err = repr(e)[:200]
        time.sleep(5 * (k + 1))
    raise RuntimeError(err)


def unit(ra, dec):
    ra, dec = np.radians(np.asarray(ra, float)), np.radians(np.asarray(dec, float))
    return np.c_[np.cos(dec) * np.cos(ra), np.cos(dec) * np.sin(ra), np.sin(dec)]


def chord(deg):
    return 2 * np.sin(np.radians(deg) / 2)


def tiles():
    return pd.read_csv(HOME / "tiles.csv").dropna()


def parent():
    T = tiles()
    boxes = sorted({(int(np.floor(r / BOX)), int(np.floor(d / BOX))) for r, d in zip(T.ra, T.dec)})
    # neighbours of tile boxes too, so isolation is right at box edges
    allb = sorted({(i + a, j + b) for i, j in boxes for a in (-1, 0, 1) for b in (-1, 0, 1)})
    out = HOME / "parent_boxes"
    out.mkdir(parents=True, exist_ok=True)
    nra = int(360 / BOX)
    for i, j in allb:
        i %= nra
        f = out / f"box_{i:02d}_{j:+03d}.csv"
        if f.exists() or j * BOX >= 50 or (j + 1) * BOX <= -90:   # RACS-mid stops near Dec +49
            continue
        q = (f"SELECT name, source_id, field_id, ra, dec, dec_corr, e_ra, e_dec_corr, total_flux, e_total_flux, peak_flux, "
             f"e_peak_flux, maj_axis, min_axis, dc_maj_axis, noise, gal_lat, s_code, n_gaussians, flag FROM {RACS} "
             f"WHERE ra >= {i * BOX} AND ra < {(i + 1) * BOX} AND dec >= {j * BOX} AND dec < {(j + 1) * BOX}")
        d = tap(CASDA, q, timeout=600)
        d.to_csv(f, index=False)
        print(f.name, len(d), flush=True)
    P = pd.concat([pd.read_csv(f) for f in sorted(out.glob("box_*.csv"))], ignore_index=True).drop_duplicates("source_id")
    tt = cKDTree(unit(T.ra, T.dec))
    d, k = tt.query(unit(P.ra, P.dec_corr))
    P["tile_near"] = T.tile_index.values[k]
    P["on_tile"] = d <= chord(TILE_R)
    P.to_csv(HOME / "parent.csv", index=False)
    print(f"parent: {len(P)} RACS-mid sources in {len(list(out.glob('box_*.csv')))} boxes; on a DR1 tile: {int(P.on_tile.sum())}")


def in_dev(ra, dec):
    return (ra >= DEV["ra"][0]) & (ra < DEV["ra"][1]) & (dec >= DEV["dec"][0]) & (dec < DEV["dec"][1])


def select():
    P = pd.read_csv(HOME / "parent.csv")
    xyz = unit(P.ra, P.dec_corr)
    tree = cKDTree(xyz)
    d2, _ = tree.query(xyz, k=2)
    P["nn_arcsec"] = 2 * np.degrees(np.arcsin(d2[:, 1] / 2)) * 3600
    P["snr"] = P.peak_flux / P.noise
    steps = [("on a DR1 tile", P.on_tile), ("flag = 0 (unresolved)", P.flag == 0), ("one Gaussian", P.n_gaussians == 1),
             (f"peak >= {PEAK_MIN} mJy/beam", P.peak_flux >= PEAK_MIN), (f"S/N >= {SNR_MIN}", P.snr >= SNR_MIN),
             (f"no other source within {ISO} arcsec", P.nn_arcsec > ISO)]
    m = np.ones(len(P), bool)
    for name, c in steps:
        m &= c.values
        print(f"{name:40s} {int(m.sum())}")
    S = P[m].copy().reset_index(drop=True)
    S["dev"] = in_dev(S.ra, S.dec_corr)
    S["pos_ra"], S["pos_dec"] = S.ra, S.dec_corr
    S["ctrl_ra"], S["ctrl_dec"] = S.ra, S.dec_corr + CTRL_OFF / 3600
    S.to_csv(HOME / "sample.csv", index=False)
    print(f"sample: {len(S)} sources, {int(S.dev.sum())} in the development region")


_lock = threading.Lock()


def one_cone(pid, ra, dec):
    q = (f"SELECT {COLS} FROM {MER} WHERE 1=CONTAINS(POINT('ICRS', right_ascension, declination), "
         f"CIRCLE('ICRS', {ra:.7f}, {dec:.7f}, {CONE / 3600:.7f}))")
    try:
        d = tap(EUCLID, q, timeout=180)
        rec = dict(pid=pid, ra=ra, dec=dec, n=len(d), rows=json.loads(d.to_json(orient="records")))
    except Exception as e:
        rec = dict(pid=pid, ra=ra, dec=dec, error=str(e)[:200])
    with _lock:
        with open(HOME / "cones.jsonl", "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec) + "\n")
    return "error" not in rec


def euclid(region="dev", workers=3):
    S = pd.read_csv(HOME / "sample.csv", dtype={"source_id": str})
    if region == "dev":
        S = S[S.dev]
    done = set()
    f = HOME / "cones.jsonl"
    if f.exists():
        for line in open(f, encoding="utf-8"):
            r = json.loads(line)
            if "error" not in r:
                done.add(r["pid"])
    jobs = []
    for r in S.itertuples():
        for kind, ra, dec in (("s", r.pos_ra, r.pos_dec), ("c", r.ctrl_ra, r.ctrl_dec)):
            pid = f"{kind}:{r.source_id}"
            if pid not in done:
                jobs.append((pid, float(ra), float(dec)))
    print(f"euclid cones: {len(jobs)} to do ({len(done)} done)", flush=True)
    t0, ok = time.time(), 0
    with ThreadPoolExecutor(workers) as ex:
        for i, good in enumerate(ex.map(lambda j: one_cone(*j), jobs), 1):
            ok += good
            if i % 100 == 0 or i == len(jobs):
                print(f"{i}/{len(jobs)} ok {ok} in {(time.time() - t0) / 60:.1f} min", flush=True)


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "parent":
        parent()
    elif cmd == "select":
        select()
    elif cmd == "euclid":
        euclid(*(sys.argv[2:3] or ["dev"]))
    else:
        sys.exit(f"unknown command {cmd}")
