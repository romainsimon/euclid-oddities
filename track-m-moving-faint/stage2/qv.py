"""Track M, second stage: what the literature says about the sources flagged by the fit (SIMBAD cone and VizieR catalogue list).
qv.py <fit csv> [radius arcsec]"""
import io
import sys
import time

import pandas as pd
import requests

SB = "https://simbad.idia.ac.za/simbad/sim-tap/sync"
VIZ = ("https://vizier.cfa.harvard.edu", "http://vizier.nao.ac.jp", "https://vizier.idia.ac.za")
D = pd.read_csv(sys.argv[1])
D = D[D.strong_cia] if "strong_cia" in D.columns else D
R = float(sys.argv[2]) if len(sys.argv) > 2 else 10.0
for p in D.itertuples():
    s = "query failed"
    for _ in range(3):
        try:
            r = requests.post(SB, data=dict(REQUEST="doQuery", LANG="ADQL", FORMAT="csv", QUERY="SELECT b.main_id, b.otype, b.sp_type FROM basic AS b WHERE "
                              f"1=CONTAINS(POINT('ICRS', b.ra, b.dec), CIRCLE('ICRS', {p.right_ascension:.6f}, {p.declination:.6f}, {R / 3600:.6f}))"), timeout=(15, 60))
            if r.status_code == 200 and not r.text.lstrip().startswith("<"):
                t = pd.read_csv(io.StringIO(r.text))
                s = "; ".join(f"{a} ({b}, {c})" for a, b, c in zip(t.main_id, t.otype, t.sp_type)) or "none"
                break
        except Exception:
            pass
        time.sleep(3)
    v = "query failed"
    for h in VIZ:
        try:
            r = requests.get(h + "/viz-bin/asu-tsv", params={"-source": "J/ApJ/934/36", "-c": f"{p.right_ascension:.6f} {p.declination:.6f}", "-c.rs": R, "-out.max": 3, "-out.all": ""}, timeout=(10, 60))
            if r.status_code == 200:
                rows = [x for x in r.text.splitlines() if x.strip() and not x.startswith("#")]
                v = "in J/ApJ/934/36: " + " | ".join(rows[3:5])[:160] if len(rows) > 3 else "not in J/ApJ/934/36"
                break
        except Exception:
            pass
    print(f"{p.object_id} {p.right_ascension:.4f} {p.declination:.4f} {p.comp_best} {p.teff_best:.0f} K, dchi2 {p.chi2_weak - p.chi2_best:.0f} | SIMBAD: {s} | {v}", flush=True)
