"""Radio-bright, Euclid-dark sources: low-frequency radio fluxes and unWISE forced photometry (no model call).

  rd5.py      every source of dark_all.csv -> sed.jsonl (one line per source, resumable), then sed.csv

Descriptive columns only (PREREG_R.md rule 8); nothing here adds or removes a source.

Radio, nearest catalogue row around the RACS-mid position (VizieR mirrors, classic interface):
  GLEAM EGC (VIII/100/gleamegc, 72-231 MHz, 60 arcsec)   wide-band 200 MHz flux, fitted 200 MHz flux, in-band index, 76/151/227 MHz
  TGSS ADR1 (J/A+A/598/A78/table3, 150 MHz, 30 arcsec)   total flux
  SUMSS (VIII/81B/sumss212, 843 MHz, 30 arcsec)          total flux
  NVSS (VIII/65/nvss, 1.4 GHz, 30 arcsec)                flux
GLEAM's beam is about 2 arcmin, so a GLEAM flux can include neighbours.

unWISE (neo7 coadds, unwise.me cutouts, 2.75 arcsec pixels, Vega zero point 22.5), W1 and W2, at the corrected radio position:
  flux in a 2 pixel (5.5 arcsec) radius aperture, background and noise from 200 equal apertures centred 5 to 17 pixels away
  (median and 1.4826 x MAD), S/N, and the 5 sigma limit in Vega mag for that aperture (no aperture correction).
The WISE beam is 6 arcsec: a neighbour within about 6 arcsec contributes to the aperture.
"""
from __future__ import annotations

import io
import json
import tarfile
import time

import numpy as np
import pandas as pd
import requests

import rd
import rd4

HOME = rd.HOME
UNWISE = "http://unwise.me/cutout_fits"
AP, RING, NAP = 2.0, (5.0, 17.0), 200       # pixels
CATS = [("gleam", "VIII/100/gleamegc", 60, ["GLEAM", "Fintwide", "Fintfit200", "alpha", "Fint076", "Fint151", "Fint227"]),
        ("tgss", "J/A+A/598/A78/table3", 30, ["TGSSADR", "Stotal", "e_Stotal"]),
        ("sumss", "VIII/81B/sumss212", 30, ["St", "e_St"]),
        ("nvss", "VIII/65/nvss", 30, ["NVSS", "S1.4", "e_S1.4"])]


def cat(src, ra, dec, rs, cols):
    t = rd4.asu({"-source": src, "-c": f"{ra:.6f} {dec:+.6f}", "-c.rs": rs, "-out": ",".join(cols + ["_r"]), "-sort": "_r", "-out.max": 3}, timeout=90)
    if t is None:
        return None
    r = rd4.rows(t)
    if not r:
        return {}
    out = dict(n=len(r))
    for k, v in zip(cols + ["_r"], r[0]):
        v = v.strip()
        try:
            out[k] = float(v)
        except ValueError:
            out[k] = v
    return out


def unwise(ra, dec):
    from astropy.io import fits
    from astropy.wcs import WCS
    r = None
    for k in range(3):
        try:
            r = requests.get(UNWISE, params=dict(version="neo7", ra=f"{ra:.6f}", dec=f"{dec:.6f}", size=41, bands=12, file_img_m="on"), timeout=(10, 90))
            if r.status_code == 200 and len(r.content) > 1000:
                break
        except Exception:
            pass
        r = None
        time.sleep(5 * (k + 1))
    if r is None:
        return None
    out = {}
    tf = tarfile.open(fileobj=io.BytesIO(r.content))
    rng = np.random.default_rng(int(abs(ra * 1e4)) + int(abs(dec * 1e4)))
    for m in tf.getmembers():
        band = "w1" if "-w1-" in m.name else "w2" if "-w2-" in m.name else None
        if band is None or "img-m" not in m.name or band in out:
            continue
        h = fits.open(io.BytesIO(tf.extractfile(m).read()))[0]
        a = np.nan_to_num(h.data.astype(float))
        x, y = WCS(h.header).all_world2pix([[ra, dec]], 0)[0]
        ny, nx = a.shape
        yy, xx = np.mgrid[:ny, :nx]

        def sumat(cx, cy):
            m_ = np.hypot(xx - cx, yy - cy) <= AP
            return float(a[m_].sum()) if m_.sum() >= 9 else np.nan
        th, rr = rng.uniform(0, 2 * np.pi, NAP), rng.uniform(RING[0], RING[1], NAP)
        s = np.array([sumat(x + q * np.cos(t), y + q * np.sin(t)) for t, q in zip(th, rr)])
        s = s[np.isfinite(s)]
        if len(s) < 50 or not (AP <= x < nx - AP and AP <= y < ny - AP):
            out[band] = dict(ok=False)
            continue
        bg, sd = float(np.median(s)), float(1.4826 * np.median(np.abs(s - np.median(s))))
        f = sumat(x, y) - bg
        out[band] = dict(ok=True, flux=f, noise=sd, snr=f / sd if sd > 0 else None, lim5=22.5 - 2.5 * np.log10(5 * sd) if sd > 0 else None,
                         mag=22.5 - 2.5 * np.log10(f) if f > 0 else None)
    return out


def main():
    C = pd.read_csv(HOME / "dark_all.csv", dtype={"sid": str})
    f = HOME / "sed.jsonl"
    done = {json.loads(x)["sid"] for x in open(f, encoding="utf-8")} if f.exists() else set()
    for i, p in enumerate(C.itertuples(), 1):
        if p.sid in done:
            continue
        rec = dict(sid=p.sid, name=p.name, peak_mid=p.peak, total_mid=p.total_mid, total_low=p.total_low, total_high=p.total_high)
        for tag, src, rs, cols in CATS:
            rec[tag] = cat(src, p.ra_mid, p.dec_mid, rs, cols)
        rec["unwise"] = unwise(p.ra, p.dec)
        failed = [k for k, v in rec.items() if v is None and k in ("gleam", "tgss", "sumss", "nvss", "unwise")]
        if failed:
            print(f"{i}/{len(C)} {p.name[10:]} failed: {failed} (not saved, a rerun retries)", flush=True)
            continue
        with open(f, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec) + chr(10))
        if i % 20 == 0:
            print(f"{i}/{len(C)}", flush=True)
    rows = []
    for x in open(f, encoding="utf-8"):
        r = json.loads(x)
        g, t, s, n, u = r["gleam"], r["tgss"], r["sumss"], r["nvss"], r["unwise"] or {}
        w1, w2 = u.get("w1", {}), u.get("w2", {})
        row = dict(name=r["name"], total_mid_mJy=r["total_mid"], gleam=g.get("GLEAM", ""), gleam_sep=g.get("_r"), gleam_200_mJy=1000 * g["Fintwide"] if "Fintwide" in g else None,
                   gleam_alpha=g.get("alpha"), gleam_076_mJy=1000 * g["Fint076"] if isinstance(g.get("Fint076"), float) else None,
                   gleam_227_mJy=1000 * g["Fint227"] if isinstance(g.get("Fint227"), float) else None,
                   tgss_150_mJy=t.get("Stotal"), sumss_843_mJy=s.get("St"), nvss_1400_mJy=n.get("S1.4"),
                   w1_snr=w1.get("snr"), w1_mag=w1.get("mag"), w1_lim5=w1.get("lim5"), w2_snr=w2.get("snr"), w2_mag=w2.get("mag"), w2_lim5=w2.get("lim5"))
        lo = row["gleam_200_mJy"] or None
        if lo and isinstance(row["total_mid_mJy"], float) and row["total_mid_mJy"] > 0:
            row["alpha_200_1367"] = float(np.log(row["total_mid_mJy"] / lo) / np.log(1367.5 / 200.5))
        rows.append(row)
    S = pd.DataFrame(rows)
    S.to_csv(HOME / "sed.csv", index=False)
    print(f"DONE {len(S)} of {len(C)}: GLEAM {int(S.gleam_200_mJy.notna().sum())}, TGSS {int(S.tgss_150_mJy.notna().sum())}, SUMSS {int(S.sumss_843_mJy.notna().sum())}, "
          f"NVSS {int(S.nvss_1400_mJy.notna().sum())}; unWISE W1 S/N > 3: {int((S.w1_snr > 3).sum())}, > 5: {int((S.w1_snr > 5).sum())}", flush=True)


if __name__ == "__main__":
    main()
