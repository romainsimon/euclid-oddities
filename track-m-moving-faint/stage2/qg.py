"""Track M, second stage: the calibration sample. Gaia white dwarfs of Gentile Fusillo et al. 2021 (VizieR J/MNRAS/508/3877, Pwd > 0.75)
that are point sources in the measured Euclid tiles. They are never candidates (candidates are absent from Gaia).
Writes ~/trackm/m2/gf21.csv (catalogue rows) and ~/trackm/m2/gwd.csv (tile rows + catalogue parameters)."""
import glob
import io
import json
import os
import time

import numpy as np
import pandas as pd
import requests
from scipy.spatial import cKDTree

H = os.path.expanduser("~/trackm")
VZ = ["https://tapvizier.cds.unistra.fr/TAPVizieR/tap/sync", "https://tapvizier.u-strasbg.fr/TAPVizieR/tap/sync"]
TB = '"J/MNRAS/508/3877/maincat"'


def tap(q, t=600):
    for u in VZ * 2:
        try:
            r = requests.post(u, data=dict(REQUEST="doQuery", LANG="ADQL", FORMAT="csv", QUERY=q), timeout=(15, t))
            if r.status_code == 200 and not r.text.lstrip().startswith("<"):
                return pd.read_csv(io.StringIO(r.text))
            print("VizieR:", r.status_code, r.text[:200])
        except Exception as e:
            print("VizieR error", repr(e)[:100])
        time.sleep(5)
    raise SystemExit("VizieR unreachable")


VIZ = ("https://vizier.cfa.harvard.edu", "http://vizier.nao.ac.jp", "https://vizier.idia.ac.za")


def asu(params):
    """Classic VizieR query on the first mirror that answers (the Strasbourg TAP service is not reachable from this server)."""
    for h in VIZ * 2:
        try:
            r = requests.get(h + "/viz-bin/asu-tsv", params=params, timeout=(15, 900))
            if r.status_code == 200 and "#INFO\tError" not in r.text and "QUERY_STATUS=ERROR" not in r.text:
                L = [x for x in r.text.splitlines() if x.strip() and not x.startswith("#")]
                k = next(i for i, x in enumerate(L) if x.startswith("---"))
                return pd.DataFrame([x.split("\t") for x in L[k + 1:]], columns=[c.strip() for c in L[k - 2].split("\t")])
        except Exception as e:
            print("VizieR", h, repr(e)[:80])
        time.sleep(5)
    raise SystemExit("VizieR unreachable")


f = H + "/m2/gf21.csv"
if not os.path.exists(f):
    names = list(asu({"-source": "J/MNRAS/508/3877/maincat", "-out.all": "", "-out.max": 1}).columns)
    print("columns:", names)
    want = [n for n in names if n in ("WDJname", "GaiaEDR3", "RA_ICRS", "DE_ICRS", "Plx", "e_Plx", "pmRA", "pmDE", "Gmag", "BPmag", "RPmag", "Pwd", "excessFlux", "AG",
                                      "TeffH", "e_TeffH", "loggH", "e_loggH", "MassH", "e_MassH", "chi2H", "TeffHe", "e_TeffHe", "loggHe", "e_loggHe", "MassHe", "e_MassHe", "chisqHe", "chi2He", "meanAV")]
    parts = []
    for lo in range(-90, -15, 15):
        parts.append(asu({"-source": "J/MNRAS/508/3877/maincat", "-out": ",".join(want), "-out.max": "unlimited", "Pwd": ">0.75", "DE_ICRS": f"{lo}..{lo + 14.999999}"}))
        print("  Dec", lo, len(parts[-1]), flush=True)
    G = pd.concat(parts, ignore_index=True)
    for c in G.columns:
        if c != "WDJname":
            G[c] = pd.to_numeric(G[c], errors="coerce") if c != "GaiaEDR3" else G[c].str.strip()
    G.dropna(subset=["RA_ICRS", "DE_ICRS"]).to_csv(f, index=False)
G = pd.read_csv(f)
print(f"catalogue rows with Pwd > 0.75 south of Dec -15: {len(G)}")
unit = lambda ra, dec: np.c_[np.cos(np.radians(dec)) * np.cos(np.radians(ra)), np.cos(np.radians(dec)) * np.sin(np.radians(ra)), np.sin(np.radians(dec))]
tree = cKDTree(unit(G.RA_ICRS.values, G.DE_ICRS.values))
J = [json.load(open(x)) for x in sorted(glob.glob(H + "/tiles/*.json"))]
J = [j for j in J if j.get("status") == "ok"]
out, seen = [], set()
for i, j in enumerate(J):
    k0 = tree.query_ball_point(unit(np.array([j["ra"]]), np.array([j["dec"]]))[0], 2 * np.sin(np.radians(0.6) / 2))
    if not k0:
        continue
    P = pd.read_csv(f"{H}/tiles/{j['tile']}.csv.gz")
    P = P[P.matched & P.ls_ref_cat.fillna("").astype(str).str.startswith("G") & ~P.object_id.isin(seen)].drop_duplicates("object_id")
    if not len(P):
        continue
    d, k = tree.query(unit(P.ls_ra.values, P.ls_dec.values))
    ok = d < 2 * np.sin(np.radians(1.5 / 3600) / 2)
    if ok.any():
        Q = P[ok].reset_index(drop=True)
        Q = pd.concat([Q, G.iloc[k[ok]].reset_index(drop=True)], axis=1)
        seen.update(Q.object_id)
        out.append(Q)
    if i % 500 == 0:
        print("  ", i, len(J), sum(len(o) for o in out), flush=True)
O = pd.concat(out, ignore_index=True)
O.to_csv(H + "/m2/gwd.csv", index=False)
print(f"Gaia white dwarfs matched to Euclid point sources: {len(O)}")
print(O[["vis", "Gmag", "TeffH", "Plx", "pm"]].describe().round(2).to_string())
print("TeffH below 5000 K:", int((O.TeffH < 5000).sum()), "; below 6000 K:", int((O.TeffH < 6000).sum()), "; det_quality_flag 0:", int((O.det_quality_flag == 0).sum()))
