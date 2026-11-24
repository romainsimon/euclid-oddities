"""Track M, rule C pixel step: 24 arcsec cutouts in VIS, Y, J, H for the near-infrared deficit candidates of ms.py.
Usage: mp.py dev | mp.py all   (reads ~/trackm/sel_<mode>/irfaint.csv; "all" refuses to run without ~/trackm/FROZEN)"""
import io
import os
import sys
import warnings

import numpy as np
import pandas as pd
import requests
from astropy.io import fits
from astropy.wcs import WCS
from PIL import Image, ImageDraw

warnings.simplefilter("ignore")
H = os.path.expanduser("~/trackm")
EU = "https://eas.esac.esa.int/tap-server/tap/sync"
SAS = "https://eas.esac.esa.int/sas-cutout/cutout"
BANDS = ["VIS", "NIR_Y", "NIR_J", "NIR_H"]
MODE = sys.argv[1]
if MODE == "all" and not os.path.exists(H + "/FROZEN"):
    sys.exit("refused: ~/trackm/FROZEN is missing")
OUT = f"{H}/sel_{MODE}"
PIX_DEFICIT, PIX_J_SNR, HOLE_R = 0.4, 5.0, 15      # rule C: mag below the blackbody value, forced J S/N, radius in 0.1 arcsec pixels
C = pd.read_csv(OUT + "/irfaint.csv").sort_values("sig_jh").reset_index(drop=True)
os.makedirs(H + "/cut", exist_ok=True)
rng = np.random.default_rng(1)
n, rows = 200, []
sheet = Image.new("RGB", (4 * (n + 4), len(C) * (n + 18)), "black")
dr = ImageDraw.Draw(sheet)
for i, p in enumerate(C.itertuples()):
    q = ("SELECT filter_name, file_name, file_path, creation_date FROM dr1.mosaic_product WHERE product_type='DpdMerBksMosaic' "
         f"AND filter_name IN ('VIS','NIR_Y','NIR_J','NIR_H') AND tile_index = {int(p.tile)}")
    F = pd.read_csv(io.StringIO(requests.post(EU, data=dict(REQUEST="doQuery", LANG="ADQL", FORMAT="csv", QUERY=q), timeout=120).text)).sort_values("creation_date", ascending=False).drop_duplicates("filter_name").set_index("filter_name")
    rec = dict(object_id=p.object_id, r=round(p.r, 2), gr=round(p.gr, 2), pm=round(p.pm, 1), cat_jh=round(p.jh, 2), bb_jh=round(p.bb_jh, 3))
    for j, b in enumerate(BANDS):
        f = f"{H}/cut/{abs(p.object_id)}_{b}.fits"
        if not os.path.exists(f):
            u = f"{SAS}?filepath={F.file_path[b]}/{F.file_name[b]}&collection=MER&tileindex={int(p.tile)}&POS=CIRCLE,{p.right_ascension:.7f},{p.declination:.7f},{12 / 3600:.6f}"
            for k in range(4):
                c = requests.get(u, timeout=180).content
                if c[:6] == b"SIMPLE":
                    open(f, "wb").write(c)
                    break
                print("retry", b, k, c[:120], flush=True)
                __import__("time").sleep(10)
        if not os.path.exists(f):
            rec[b + "_snr"] = None
            continue
        h = fits.open(f)[0]
        a = np.nan_to_num(h.data.astype(float))
        x, y = WCS(h.header).all_world2pix([[p.right_ascension, p.declination]], 0)[0]
        yy, xx = np.mgrid[:a.shape[0], :a.shape[1]]
        ap = 6 if b == "VIS" else 8          # pixels of 0.1 arcsec: radius 0.6 arcsec in VIS, 0.8 arcsec in NIR
        s = lambda cx, cy: float(a[np.hypot(xx - cx, yy - cy) <= ap].sum())
        th, rr = rng.uniform(0, 2 * np.pi, 300), rng.uniform(25, 100, 300)
        bg = np.array([s(x + q_ * np.cos(t), y + q_ * np.sin(t)) for t, q_ in zip(th, rr)])
        sd = 1.4826 * np.median(np.abs(bg - np.median(bg)))
        fl = s(x, y) - np.median(bg)
        rec[b + "_fl"], rec[b + "_sd"] = fl, sd
        zp = float(h.header.get("MAGZERO", np.nan))
        rec[b + "_snr"] = round(fl / sd, 1)
        rec[b + "_mag"] = round(zp - 2.5 * np.log10(fl), 2) if fl > 0 else None
        rec[b + "_lim3"] = round(zp - 2.5 * np.log10(3 * sd), 2)
        rec[b + "_bad"] = round(float(((a == 0) & (np.hypot(xx - x, yy - y) <= HOLE_R)).mean() / max((np.hypot(xx - x, yy - y) <= HOLE_R).mean(), 1e-9)), 3)
        m, sg = np.median(a), 1.48 * np.median(np.abs(a - np.median(a))) + 1e-12
        xi, yi = int(round(x)), int(round(y))
        pad = np.pad(a, 150, constant_values=m)[yi + 150 - 50:yi + 150 + 50, xi + 150 - 50:xi + 150 + 50]
        v = np.clip((np.arcsinh((pad - m) / sg / 2) + 1) / 5, 0, 1)[::-1]
        im = Image.fromarray((v * 255).astype(np.uint8)).resize((n, n), Image.NEAREST).convert("RGB")
        ImageDraw.Draw(im).ellipse((n // 2 - 20, n // 2 - 20, n // 2 + 20, n // 2 + 20), outline=(90, 220, 255))
        sheet.paste(im, (j * (n + 4), i * (n + 18) + 16))
        dr.text((j * (n + 4) + 3, i * (n + 18) + 2), f"{i} {b[-3:]} S/N {rec[b + '_snr']}", fill="white")
    rows.append(rec)
sheet.save(OUT + "/irfaint.png")
R = pd.DataFrame(rows)
num = lambda c: pd.to_numeric(R[c], errors="coerce") if c in R else pd.Series(np.nan, index=R.index)
fj, fh, sh = num("NIR_J_fl"), num("NIR_H_fl"), num("NIR_H_sd")
R["pix_h_limit"] = fh < 2 * sh
R["pix_jh"] = -2.5 * np.log10(fj.where(fj > 0) / np.maximum(fh, 2 * sh))     # H below 2 sigma: the 2 sigma value is used (upper limit on J - H)
R["pix_d_jh"] = R.pix_jh - R.bb_jh
hole = (num("NIR_Y_bad") > 0) | (num("NIR_J_bad") > 0) | (num("NIR_H_bad") > 0)
miss = num("NIR_Y_snr").isna() | num("NIR_J_snr").isna() | num("NIR_H_snr").isna()
R["verdict"] = np.select([miss, hole, num("NIR_J_snr") < PIX_J_SNR, ~(R.pix_d_jh <= -PIX_DEFICIT)],
                         ["rejected: cutout missing", "rejected: missing pixels within 1.5 arcsec", "rejected: J not confirmed on the pixels", "rejected: forced J-H not 0.4 mag below the blackbody"], "passes")
pd.set_option("display.width", 250)
pd.set_option("display.max_rows", 200)
print(R.drop(columns=[c for c in R if c.endswith(("_fl", "_sd", "_lim3"))]).round(2).to_string())
print(R.verdict.value_counts().to_string())
R.to_csv(OUT + "/irfaint_pix.csv", index=False)
