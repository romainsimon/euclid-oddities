"""Track M, rule F: NOIRLab Source Catalog DR2 proper motion (a third data set) for the near-infrared deficit candidates. Reported, removes nothing.
Usage: mn.py dev | mn.py all   (reads ~/trackm/sel_<mode>/irfaint.csv, writes irfaint_nsc.csv)"""
import io
import os
import sys
import time

import numpy as np
import pandas as pd
import requests

H = os.path.expanduser("~/trackm")
MODE = sys.argv[1]
if MODE == "all" and not os.path.exists(H + "/FROZEN"):
    sys.exit("refused: ~/trackm/FROZEN is missing")
OUT = f"{H}/sel_{MODE}"
DL = "https://datalab.noirlab.edu/tap/sync"
R_MATCH, DISAGREE = 2.5, 3.0      # arcsec, sigma
C = pd.read_csv(OUT + "/irfaint.csv")
rows = []
for p in C.itertuples():
    dd = R_MATCH / 3600
    dr_ = dd / np.cos(np.radians(p.declination))
    q = ("SELECT ra, dec, pmra, pmraerr, pmdec, pmdecerr, ndet, deltamjd, rmag FROM nsc_dr2.object WHERE "
         f"ra BETWEEN {p.right_ascension - dr_:.6f} AND {p.right_ascension + dr_:.6f} AND dec BETWEEN {p.declination - dd:.6f} AND {p.declination + dd:.6f}")
    n = None
    for k in range(3):
        try:
            r = requests.post(DL, data=dict(REQUEST="doQuery", LANG="ADQL", FORMAT="csv", QUERY=q), timeout=(15, 90))
            if r.status_code == 200 and not r.text.lstrip().startswith("<"):
                n = pd.read_csv(io.StringIO(r.text))
                break
        except Exception:
            pass
        time.sleep(5)
    rec = dict(object_id=p.object_id, nsc="query failed" if n is None else "no object")
    if n is not None and len(n):
        n["d"] = np.hypot((n.ra - p.right_ascension) * np.cos(np.radians(p.declination)), n.dec - p.declination) * 3600
        m = n.sort_values("d").iloc[0]
        ex, ey = np.hypot(m.pmraerr, p.e_pm), np.hypot(m.pmdecerr, p.e_pm)
        chi = float(np.hypot((m.pmra - p.pmx) / ex, (m.pmdec - p.pmy) / ey))
        rec.update(nsc="disagrees" if chi > DISAGREE else "compatible", nsc_pmra=m.pmra, nsc_e_pmra=m.pmraerr, nsc_pmdec=m.pmdec, nsc_e_pmdec=m.pmdecerr,
                   nsc_ndet=int(m.ndet), nsc_days=round(float(m.deltamjd)), nsc_dist_sigma=round(chi, 1))
    rows.append(rec)
R = C[["object_id", "right_ascension", "declination", "pmx", "pmy", "e_pm"]].merge(pd.DataFrame(rows), on="object_id")
pd.set_option("display.width", 250)
pd.set_option("display.max_rows", 200)
print(R.round(2).to_string())
print(R.nsc.value_counts().to_string())
R.to_csv(OUT + "/irfaint_nsc.csv", index=False)
