"""Radio-bright, Euclid-dark sources: match and pixel stages (no model call).

  match <region>    per-field astrometric offset, then the Euclid sources around every radio and control position
                    -> match_<region>.csv, offsets_<region>.csv
  pix <region>      forced photometry on the Euclid VIS / NIR_H mosaics at the corrected radio position, for the
                    candidates of match, the same number of matched sources and of control positions -> pix_<region>.csv
  dark <region>     frozen selection on pix, RACS-low / RACS-high / CatWISE around the selected sources,
                    image sheets -> dark_<region>.csv, sheets/dark_<region>_*.png

region = dev (development box only) or all. Every threshold is tuned on dev only and frozen in the published amendment
before `match all` is run.
"""
from __future__ import annotations

import io
import json
import os
import sys
import time
import warnings
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
import requests

import rd

HOME = rd.HOME
SAS = "https://eas.esac.esa.int/sas-cutout/cutout"
# match
BRIGHT_H = 21.0        # mag, matches this bright define the astrometric offset of a RACS field
BRIGHT_R = 1.5         # arcsec
FIELD_MIN = 8          # bright matches needed for a per-field offset (else the offset of the whole region)
COVER_MIN = 3          # Euclid sources at 8-20 arcsec for the position to count as covered
R_DARK = 2.5           # arcsec, candidate = no catalogued Euclid source this close to the corrected position
# pixels
CUT_R = 16.5 / 3600    # deg
AP_RS = (1.0, 1.5)     # arcsec, forced aperture radii
RING = (3.5, 12.0)     # arcsec, local background and noise are measured this far from the position
SEARCH_R = 1.5         # arcsec, brightest smoothed pixel is searched this far from the position
PIX = 0.1              # arcsec per pixel
# selection (frozen in amendment R1)
BAD_MAX = 0.10         # largest fraction of missing pixels within 3 arcsec, each band
LIM_MIN = dict(VIS=23.0, NIR_H=22.3)   # AB mag, local 5 sigma limit in the 1.5 arcsec aperture must be at least this deep
SNR_MAX = 3.0          # forced 1.5 arcsec aperture S/N below this in VIS and in H
HIGH_R = 3.0           # arcsec, a RACS-high source this close to the RACS-mid catalogue position is required
TP_MAX = 1.3           # total / peak flux, RACS-mid and RACS-high: compact in both
PEAK_EMPTY = 5.0       # class "empty": smoothed peak within SEARCH_R below this in both bands, else "faint host"
FREQ = dict(low=943.5, mid=1367.5, high=1655.5)   # MHz


def mag(f):
    f = np.asarray(f, float)
    return np.where(f > 0, 23.9 - 2.5 * np.log10(np.where(f > 0, f, 1)), np.nan)


def load(region):
    S = pd.read_csv(HOME / "sample.csv", dtype={"source_id": str})
    if region == "dev":
        S = S[S.dev]
    C = {}
    for line in open(HOME / "cones.jsonl", encoding="utf-8"):
        r = json.loads(line)
        if "error" not in r:
            C[r["pid"]] = r
    return S.reset_index(drop=True), C


def around(r, ra, dec):
    """Non-spurious Euclid rows of a cone, with offsets (arcsec) from (ra, dec): east and north positive."""
    g = pd.DataFrame([x for x in r["rows"] if x["spurious_flag"] == 0])
    if not len(g):
        return g
    g["dx"] = (g.right_ascension - ra) * np.cos(np.radians(dec)) * 3600
    g["dy"] = (g.declination - dec) * 3600
    g["d"] = np.hypot(g.dx, g.dy)
    g["H"], g["V"] = mag(g.flux_h_2fwhm_aper), mag(g.flux_vis_2fwhm_aper)
    return g.sort_values("d").reset_index(drop=True)


def match(region):
    S, C = load(region)
    # 1. astrometric offset of each RACS field, from bright matches at the catalogue position
    b = []
    for s in S.itertuples():
        r = C.get(f"s:{s.source_id}")
        if r is None:
            continue
        g = around(r, s.pos_ra, s.pos_dec)
        if len(g) and g.d[0] < BRIGHT_R and g.H[0] < BRIGHT_H:
            b.append(dict(field=s.field_id, dx=g.dx[0], dy=g.dy[0]))
    B = pd.DataFrame(b)
    gx, gy = B.dx.median(), B.dy.median()
    O = B.groupby("field").agg(n=("dx", "size"), dx=("dx", "median"), dy=("dy", "median")).reset_index()
    O.loc[O.n < FIELD_MIN, ["dx", "dy"]] = [gx, gy]
    O.to_csv(HOME / f"offsets_{region}.csv", index=False)
    off = {o.field: (o.dx, o.dy) for o in O.itertuples()}
    print(f"offsets: {len(B)} bright matches, region median dx {gx:+.2f} dy {gy:+.2f}; "
          f"{int((O.n >= FIELD_MIN).sum())} of {len(O)} fields have their own offset")
    # 2. nearest Euclid sources at the corrected position, sources and controls
    out = []
    for s in S.itertuples():
        ox, oy = off.get(s.field_id, (gx, gy))
        for kind, ra0, dec0 in (("s", s.pos_ra, s.pos_dec), ("c", s.ctrl_ra, s.ctrl_dec)):
            r = C.get(f"{kind}:{s.source_id}")
            if r is None:
                continue
            dec = dec0 + oy / 3600
            ra = ra0 + ox / 3600 / np.cos(np.radians(dec0))
            g = around(r, ra, dec)
            rec = dict(kind=kind, sid=s.source_id, name=s.name, field=s.field_id, tile=int(s.tile_near), dev=bool(s.dev),
                       ra=ra, dec=dec, peak=s.peak_flux, total=s.total_flux, snr=s.snr, n=len(g),
                       n_out=int(((g.d > 8) & (g.d <= 20)).sum()) if len(g) else 0)
            if len(g):
                n = g.iloc[0]
                in3 = g[g.d <= 3.0]
                rec.update(d1=n.d, H1=n.H, V1=n.V, id1=int(n.object_id), n25=int((g.d <= R_DARK).sum()),
                           Hmin3=in3.H.min() if len(in3) else np.nan, Vmin3=in3.V.min() if len(in3) else np.nan)
            a = pd.DataFrame(r["rows"])
            if len(a):   # every catalogue row, spurious ones included: bright stars and their masks
                da = np.hypot((a.right_ascension - ra) * np.cos(np.radians(dec)), a.declination - dec) * 3600
                rec.update(d1_any=float(da.min()), Hmin_all=float(np.nanmin(mag(a.flux_h_2fwhm_aper))) if (a.flux_h_2fwhm_aper > 0).any() else np.nan,
                           Vmin_all=float(np.nanmin(mag(a.flux_vis_2fwhm_aper))) if (a.flux_vis_2fwhm_aper > 0).any() else np.nan)
            out.append(rec)
    M = pd.DataFrame(out)
    M["covered"] = M.n_out >= COVER_MIN
    M["cand"] = M.covered & ~(M.d1 <= R_DARK)
    M.to_csv(HOME / f"match_{region}.csv", index=False)
    for k, name in (("s", "radio sources"), ("c", "control positions")):
        m = M[(M.kind == k) & M.covered]
        fr = {r: round(float((m.d1 < r).mean()), 3) for r in (0.5, 1, 1.5, 2, 2.5, 3)}
        print(f"{name}: {int((M.kind == k).sum())}, covered {len(m)}, nothing within {R_DARK} arcsec: {int(m.cand.sum())}")
        print(f"   fraction with a Euclid source within r arcsec: {fr}")
        for lim in (20, 21, 22, 23, 24):
            print(f"   brightest within 3 arcsec has H < {lim}: {float((m.Hmin3 < lim).mean()):.3f}")
    s = M[(M.kind == "s") & M.covered & (M.d1 < BRIGHT_R) & (M.H1 < BRIGHT_H)]
    print(f"bright matches after correction: {len(s)}, per-axis scatter {s.d1.pow(2).mean() ** 0.5 / 2 ** 0.5:.2f} arcsec, "
          f"radius holding 95%: {s.d1.quantile(0.95):.2f}, 99%: {s.d1.quantile(0.99):.2f}")


# ---------------------------------------------------------------- pixels
def band_files(tiles):
    f = HOME / "bands.csv"
    old = pd.read_csv(f) if f.exists() else pd.DataFrame(columns=["tile_index"])
    need = sorted(set(int(t) for t in tiles) - set(old.tile_index.astype(int)))
    new = []
    for k in range(0, len(need), 100):
        ids = ",".join(str(t) for t in need[k:k + 100])
        q = ("SELECT tile_index, filter_name, purpose, creation_date, file_name, file_path FROM dr1.mosaic_product "
             f"WHERE product_type='DpdMerBksMosaic' AND filter_name IN ('VIS','NIR_H') AND tile_index IN ({ids})")
        new.append(rd.tap(rd.EUCLID, q))
    if new:
        df = pd.concat([old] + new, ignore_index=True)
        df["pref"] = (df.purpose != "DATA_RELEASE").astype(int)
        df = df.sort_values(["tile_index", "filter_name", "pref", "creation_date"], ascending=[True, True, True, False])
        old = df.drop_duplicates(["tile_index", "filter_name"]).drop(columns="pref")
        old.to_csv(f, index=False)
    return old.set_index(["tile_index", "filter_name"])


def cutout(F, tile, band, ra, dec, key):
    """Square cutout centred on (ra, dec), cached as FITS bytes. Returns (data, x, y) with the position in pixels."""
    from astropy.io import fits
    from astropy.wcs import WCS, FITSFixedWarning
    warnings.simplefilter("ignore", FITSFixedWarning)
    d = HOME / "cut"
    d.mkdir(exist_ok=True)
    f = d / f"{key}_{band}.fits"
    if not f.exists():
        try:
            r = F.loc[(int(tile), band)]
        except KeyError:
            return None
        url = f"{SAS}?filepath={r.file_path}/{r.file_name}&collection=MER&tileindex={int(tile)}&POS=CIRCLE,{ra:.7f},{dec:.7f},{CUT_R}"
        for k in range(3):
            try:
                b = requests.get(url, timeout=180)
                if b.status_code == 200 and b.content[:6] == b"SIMPLE":
                    f.write_bytes(b.content)
                    break
            except Exception:
                pass
            time.sleep(5 * (k + 1))
        else:
            return None
    h = fits.open(f)[0]
    x, y = WCS(h.header).all_world2pix([[ra, dec]], 0)[0]
    return h.data.astype(np.float32), float(x), float(y), float(h.header.get("MAGZERO", np.nan))


def forced(img, x, y, rng):
    """Aperture sum at (x, y). Background and noise are local: the median and the robust scatter of 300 equal
    apertures whose centres lie RING arcsec from the position. Also the highest peak of the 0.3 arcsec smoothed
    image within SEARCH_R, in units of the smoothed image's robust scatter in the same ring."""
    from scipy.ndimage import gaussian_filter
    ny, nx = img.shape
    bad = ~np.isfinite(img) | (img == 0)
    yy, xx = np.mgrid[:ny, :nx]
    r = np.hypot(xx - x, yy - y) * PIX
    out = dict(bad3=float(bad[r <= 3.0].mean()) if (r <= 3.0).any() else 1.0, bad_all=float(bad.mean()))
    if out["bad3"] > 0.1:
        return out
    a = np.where(bad, 0.0, img)
    ring = (r >= RING[0]) & (r <= RING[1])
    for R in AP_RS:
        ap = int(round(R / PIX))
        k = np.hypot(*np.mgrid[-ap:ap + 1, -ap:ap + 1]) <= ap

        def sumat(cx, cy):
            cx, cy = int(round(cx)), int(round(cy))
            if cx - ap < 0 or cy - ap < 0 or cx + ap >= nx or cy + ap >= ny:
                return np.nan
            return float(a[cy - ap:cy + ap + 1, cx - ap:cx + ap + 1][k].sum())
        th, rr = rng.uniform(0, 2 * np.pi, 300), rng.uniform(RING[0], RING[1], 300) / PIX
        rs = np.array([sumat(x + q * np.cos(t), y + q * np.sin(t)) for t, q in zip(th, rr)])
        rs = rs[np.isfinite(rs)]
        m0, s0 = np.median(rs), 1.4826 * np.median(np.abs(rs - np.median(rs)))
        f = sumat(x, y)
        t = f"{int(R * 10):02d}"
        out.update({f"flux{t}": f - m0, f"noise{t}": s0, f"snr{t}": (f - m0) / s0 if s0 > 0 else np.nan})
    sm = gaussian_filter(a, 0.3 / PIX / 2.355)
    sm = sm - np.median(sm[ring])
    ss = 1.4826 * np.median(np.abs(sm[ring]))
    near = r <= SEARCH_R
    j = np.argmax(np.where(near, sm, -np.inf))
    py, px = divmod(int(j), nx)
    out.update(peak_snr=float(sm[py, px] / ss) if ss > 0 else np.nan, peak_dx=(x - px) * PIX, peak_dy=(py - y) * PIX)
    return out


def pix(region):
    M = pd.read_csv(HOME / f"match_{region}.csv", dtype={"sid": str})
    rng = np.random.default_rng(20261118)
    W = M[M.covered & ((M.kind == "s") | M.dev)].reset_index(drop=True)   # controls are measured in the development box only
    W["set"] = np.where(W.kind == "s", "source", "control")
    F = band_files(W.tile.unique())

    def one(w):
        rec = dict(set=w.set, kind=w.kind, sid=w.sid, name=w.name, ra=w.ra, dec=w.dec, tile=w.tile, peak=w.peak, d1=w.d1, H1=w.H1, Hmin_all=w.Hmin_all, Vmin_all=w.Vmin_all, d1_any=w.d1_any, snr_radio=w.snr, dev=w.dev)
        for band in ("VIS", "NIR_H"):
            c = cutout(F, w.tile, band, w.ra, w.dec, f"{w.kind}_{w.sid}")
            if c is None:
                rec[f"{band}_bad3"] = np.nan
                continue
            for a, v in forced(c[0], c[1], c[2], np.random.default_rng(w.Index * 2 + (band == 'VIS'))).items():
                rec[f"{band}_{a}"] = v
            rec[f"{band}_zp"] = c[3]
        return rec

    t0, out = time.time(), []
    with ThreadPoolExecutor(6) as ex:
        for i, rec in enumerate(ex.map(one, W.itertuples()), 1):
            out.append(rec)
            if i % 200 == 0 or i == len(W):
                print(f"{i}/{len(W)} in {(time.time() - t0) / 60:.1f} min", flush=True)
    pd.DataFrame(out).to_csv(HOME / f"pix_{region}.csv", index=False)


# ---------------------------------------------------------------- selection and context
def casda_near(table, ra, dec, rad):
    q = f"SELECT * FROM {table} WHERE 1=CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS', {ra:.6f}, {dec:.6f}, {rad / 3600:.6f}))"
    d = rd.tap(rd.CASDA, q, timeout=120, tries=3)
    if len(d):
        d["sep"] = np.hypot((d.ra - ra) * np.cos(np.radians(dec)), d.dec - dec) * 3600
        d = d.sort_values("sep")
    return d


def catwise(ra, dec):
    q = ("SELECT ra, dec, w1mpro, w1sigmpro, w2mpro, w2sigmpro FROM catwise_2020 WHERE "
         f"CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS', {ra:.6f}, {dec:.6f}, {5 / 3600:.6f})) = 1")
    d = rd.tap("https://irsa.ipac.caltech.edu/TAP/sync", q, timeout=120, tries=2)
    if len(d):
        d["sep"] = np.hypot((d.ra - ra) * np.cos(np.radians(dec)), d.dec - dec) * 3600
        d = d.sort_values("sep")
    return d


def context(p, r0):
    rec = dict(sid=p.sid, ra_mid=r0.pos_ra, dec_mid=r0.pos_dec, total_mid=r0.total_flux, tp_mid=r0.total_flux / r0.peak_flux)
    try:
        h = casda_near("AS110.racs_high_sources_v01", r0.pos_ra, r0.pos_dec, 15)
        rec["high_n15"] = len(h)
        if len(h):
            rec.update(high_sep=h.sep.iloc[0], total_high=h.total_flux.iloc[0], tp_high=h.total_flux.iloc[0] / h.peak_flux.iloc[0])
        lo = casda_near("AS110.racs_low2_v02", r0.pos_ra, r0.pos_dec, 15)
        rec["low_n15"] = len(lo)
        if len(lo):
            rec.update(low_sep=lo.sep.iloc[0], total_low=lo.total_flux.iloc[0])
    except Exception as e:
        rec["radio_err"] = str(e)[:80]
    try:
        w = catwise(p.ra, p.dec)
        rec["wise_n5"] = len(w)
        if len(w):
            rec.update(wise_sep=w.sep.iloc[0], w1=w.w1mpro.iloc[0], w2=w.w2mpro.iloc[0])
    except Exception as e:
        rec["wise_err"] = str(e)[:80]
    return rec


def dark(region):
    P = pd.read_csv(HOME / f"pix_{region}.csv", dtype={"sid": str})
    S = pd.read_csv(HOME / "sample.csv", dtype={"source_id": str}).set_index("source_id")
    s = P[P.kind == "s"].copy()
    for b in ("VIS", "NIR_H"):
        s[f"{b}_lim"] = s[f"{b}_zp"] - 2.5 * np.log10(5 * s[f"{b}_noise15"])
    steps = [("radio sources on covered positions", np.ones(len(s), bool)),
             ("both mosaics fetched", s.VIS_bad3.notna() & s.NIR_H_bad3.notna()),
             (f"missing pixels within 3 arcsec <= {BAD_MAX} in both", (s.VIS_bad3 <= BAD_MAX) & (s.NIR_H_bad3 <= BAD_MAX)),
             (f"local 5 sigma limit >= {LIM_MIN['VIS']} (VIS) and {LIM_MIN['NIR_H']} (H)",
              (s.VIS_lim >= LIM_MIN["VIS"]) & (s.NIR_H_lim >= LIM_MIN["NIR_H"])),
             (f"forced S/N < {SNR_MAX} in VIS and in H", (s.VIS_snr15 < SNR_MAX) & (s.NIR_H_snr15 < SNR_MAX))]
    m = np.ones(len(s), bool)
    for name, c in steps:
        m &= np.asarray(c, bool)
        print(f"{name:62s} {int(m.sum())}", flush=True)
    D = s[m].reset_index(drop=True)
    with ThreadPoolExecutor(3) as ex:
        R = pd.DataFrame(list(ex.map(lambda p: context(p, S.loc[p.sid]), D.itertuples())))
    for c in ("high_sep", "tp_high", "total_high", "total_low", "low_sep", "wise_n5", "wise_sep", "w1", "w2", "radio_err", "wise_err"):
        if c not in R:
            R[c] = np.nan
    D = D.merge(R, on="sid")
    D["alpha_low_mid"] = np.log(D.total_mid / D.total_low) / np.log(FREQ["mid"] / FREQ["low"])
    D["alpha_mid_high"] = np.log(D.total_high / D.total_mid) / np.log(FREQ["high"] / FREQ["mid"])
    D["radio_ok"] = (D.high_sep <= HIGH_R) & (D.tp_high <= TP_MAX) & (D.tp_mid <= TP_MAX)
    D["cls"] = np.where((D.VIS_peak_snr < PEAK_EMPTY) & (D.NIR_H_peak_snr < PEAK_EMPTY), "empty", "faint host")
    print(f"{'RACS-high within ' + str(HIGH_R) + ' arcsec, compact in mid and high':62s} {int(D.radio_ok.sum())}"
          f"   (radio queries failed: {int(D.radio_err.notna().sum())}, CatWISE queries failed: {int(D.wise_err.notna().sum())})")
    C = D[D.radio_ok].sort_values("peak", ascending=False).reset_index(drop=True)
    print("classes:", C.cls.value_counts().to_dict(), "| in the development box:", int(C.dev.sum()))
    D.to_csv(HOME / f"dark_{region}_all.csv", index=False)
    C.to_csv(HOME / f"dark_{region}.csv", index=False)
    sheets(C, region)


def sheets(C, region, per=28, cols=7, n=320):
    from PIL import Image, ImageDraw
    from astropy.io import fits
    from astropy.wcs import WCS
    warnings.simplefilter("ignore")
    out = HOME / "sheets"
    out.mkdir(exist_ok=True)
    for k in range(0, len(C), per):
        c = C.iloc[k:k + per]
        rows = (len(c) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * (n + 6), rows * 2 * (n + 22)), "black")
        dr = ImageDraw.Draw(sheet)
        for i, p in enumerate(c.itertuples()):
            for j, b in enumerate(("VIS", "NIR_H")):
                h = fits.open(HOME / "cut" / f"s_{p.sid}_{b}.fits")[0]
                d = np.nan_to_num(h.data.astype(float))
                x, y = (int(round(v)) for v in WCS(h.header).all_world2pix([[p.ra, p.dec]], 0)[0])
                m = np.median(d)
                sd = 1.48 * np.median(np.abs(d - m)) + 1e-12
                pad = np.pad(d, 200, constant_values=m)[y + 200 - n // 2:y + 200 + n // 2, x + 200 - n // 2:x + 200 + n // 2]
                v = np.clip((np.arcsinh((pad - m) / sd / 3) + 1) / 5, 0, 1)[::-1]
                im = Image.fromarray((v * 255).astype(np.uint8)).convert("RGB")
                r = int(SEARCH_R / PIX)
                ImageDraw.Draw(im).ellipse((n // 2 - r, n // 2 - r, n // 2 + r, n // 2 + r), outline=(0, 255, 255))
                ox, oy = (i % cols) * (n + 6), ((i // cols) * 2 + j) * (n + 22)
                sheet.paste(im, (ox, oy + 20))
                dr.text((ox + 4, oy + 4), f"{k + i} {p.name[10:]} {b[-3:]} {p.peak:.0f} mJy", fill="white")
        sheet.save(out / f"dark_{region}_{k // per:02d}.png")


if __name__ == "__main__":
    cmd, region = sys.argv[1], (sys.argv[2:3] or ["dev"])[0]
    if region == "all" and not (HOME / "FROZEN").exists():
        sys.exit("the non-development sky is locked until the amendment is published (file FROZEN missing)")
    dict(match=match, pix=pix, dark=dark)[cmd](region)
