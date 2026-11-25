"""Track M, second stage: SIMBAD bibliography of the objects within a cone of the flagged sources. qr.py <fit csv> [radius arcsec]"""
import io
import sys
import time

import pandas as pd
import requests

SB = "https://simbad.idia.ac.za/simbad/sim-tap/sync"
D = pd.read_csv(sys.argv[1])
D = D[D.strong_cia] if "strong_cia" in D.columns else D
R = float(sys.argv[2]) if len(sys.argv) > 2 else 10.0
for p in D.itertuples():
    q = ("SELECT basic.main_id, ref.bibcode, ref.title FROM basic JOIN has_ref ON has_ref.oidref = basic.oid JOIN ref ON ref.oidbib = has_ref.oidbibref WHERE "
         f"1=CONTAINS(POINT('ICRS', basic.ra, basic.dec), CIRCLE('ICRS', {p.right_ascension:.6f}, {p.declination:.6f}, {R / 3600:.6f}))")
    out = "query failed"
    for _ in range(3):
        try:
            r = requests.post(SB, data=dict(REQUEST="doQuery", LANG="ADQL", FORMAT="csv", QUERY=q), timeout=(15, 60))
            if r.status_code == 200 and not r.text.lstrip().startswith("<"):
                t = pd.read_csv(io.StringIO(r.text))
                out = "\n".join(f"      {a} | {b} | {str(c)[:110]}" for a, b, c in zip(t.main_id, t.bibcode, t.title)) or "      no reference"
                break
        except Exception:
            pass
        time.sleep(3)
    print(f"{p.object_id} {p.right_ascension:.4f} {p.declination:.4f}\n{out}", flush=True)
