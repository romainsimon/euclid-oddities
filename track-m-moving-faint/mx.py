"""Track M, checks made AFTER the results were read (post hoc, they change no list):
1. is the blackbody reference biased with colour or magnitude? Residuals of the white dwarf candidates in bins, and the candidates re-scored against the local median.
2. SIMBAD cone (10 arcsec) for the kept near-infrared deficit candidates; retry of the failed NOIRLab Source Catalog queries.
3. where the unmeasured tiles are.
Writes ~/trackm/pub/posthoc.csv."""
import csv
import io
import os
import re
import time

import numpy as np
import pandas as pd
import requests

H = os.path.expanduser("~/trackm")
SB = "https://simbad.idia.ac.za/simbad/sim-tap/sync"
DL = "https://datalab.noirlab.edu/tap/sync"


def bb(T):
    f = lambda lam: (14388 / (lam * T)) ** 3 / np.expm1(14388 / (lam * T))
    m = lambda a, b: -2.5 * np.log10(f(a) / f(b))
    return m(0.475, 0.635), m(1.08, 1.37), m(1.37, 1.77)


def tap(u, q):
    for _ in range(3):
        try:
            r = requests.post(u, data=dict(REQUEST="doQuery", LANG="ADQL", FORMAT="csv", QUERY=q), timeout=(15, 90))
            if r.status_code == 200 and not r.text.lstrip().startswith("<"):
                return pd.read_csv(io.StringIO(r.text))
        except Exception:
            pass
        time.sleep(5)
    return None


# 1. the sample of rule C, rebuilt exactly as in ms.py
W = pd.read_csv(H + "/sel_all/wd.csv.gz")
for b_ in "yjh":
    W[b_ + "_snr"] = W[f"flux_{b_}_2fwhm_aper"] / W[f"fluxerr_{b_}_2fwhm_aper"]
W = W[(W.j_snr > 8) & np.isfinite(W.gr)].copy()
T = np.arange(3000, 15000, 100)
B = np.array([bb(t) for t in T])
fh = np.maximum(W.flux_h_2fwhm_aper, 2 * W.fluxerr_h_2fwhm_aper)
fy = W.flux_y_2fwhm_aper
W["jh"] = -2.5 * np.log10(W.flux_j_2fwhm_aper / fh)
W["yj"] = -2.5 * np.log10(fy.where(fy > 0) / W.flux_j_2fwhm_aper)
W["T_bb"] = np.interp(W.gr, B[::-1, 0], T[::-1])
W["d_jh"] = W.jh - np.interp(W.T_bb, T, B[:, 2])
W["d_yj"] = W.yj - np.interp(W.T_bb, T, B[:, 1])
W["e_jh"] = np.hypot(1.086 * np.hypot(1 / W.j_snr, 1 / W.h_snr.clip(lower=2)), 0.08)
W["e_yj"] = np.hypot(1.086 * np.hypot(1 / W.j_snr, 1 / W.y_snr.clip(lower=0.5)), 0.08)
mad = lambda v: 1.4826 * (v - v.median()).abs().median()
print(f"sample {len(W)}; global median d_jh {W.d_jh.median():+.3f}, d_yj {W.d_yj.median():+.3f}")
print("residuals against the blackbody by g-r (count, median J-H, scatter, median Y-J, scatter):")
edges = [-1, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 3]
W["bin"] = pd.cut(W.gr, edges)
for k, g in W.groupby("bin", observed=True):
    print(f"   g-r {k}: {len(g):5d}  J-H {g.d_jh.median():+.3f} ({mad(g.d_jh):.3f})   Y-J {g.d_yj.median():+.3f} ({mad(g.d_yj):.3f})")
print("by r:")
for k, g in W.groupby(pd.cut(W.r, [19, 21, 21.5, 22, 22.5, 23, 25]), observed=True):
    print(f"   r {k}: {len(g):5d}  J-H {g.d_jh.median():+.3f} ({mad(g.d_jh):.3f})   Y-J {g.d_yj.median():+.3f} ({mad(g.d_yj):.3f})")
# local reference: running median in g-r (window of 401 sources)
W = W.sort_values("gr").reset_index(drop=True)
W["loc_jh"] = W.d_jh.rolling(401, center=True, min_periods=100).median()
W["loc_yj"] = W.d_yj.rolling(401, center=True, min_periods=100).median()
W["lsig_jh"] = (W.d_jh - W.loc_jh) / W.e_jh
W["lsig_yj"] = (W.d_yj - W.loc_yj) / W.e_yj
D = pd.read_csv(H + "/pub/ir_deficit_candidates.csv")
K = D[D.verdict == "passes"].merge(W[["object_id", "loc_jh", "loc_yj", "lsig_jh", "lsig_yj"]], on="object_id", how="left")
rule = lambda a, b: (a < -3) | ((a < -2) & (b < -2))
K["local_rule"] = rule(K.lsig_jh, K.lsig_yj)
K["firm"] = (K.sig_jh < -3) & (K.sig_yj < -2) & (K.nsc != "disagrees")
K["local_firm"] = (K.lsig_jh < -3) & (K.lsig_yj < -2) & (K.nsc != "disagrees")
print(f"kept candidates {len(K)}: still selected against the local median {int(K.local_rule.sum())}; 'two colours' subset {int(K.firm.sum())} -> {int((K.firm & K.local_firm).sum())} still in it")
print(f"whole sample against the local median: deficit side {int(rule(W.lsig_jh, W.lsig_yj).sum())}, excess side {int(rule(-W.lsig_jh, -W.lsig_yj).sum())}; "
      f"two colours: deficit {int(((W.lsig_jh < -3) & (W.lsig_yj < -2)).sum())}, excess {int(((W.lsig_jh > 3) & (W.lsig_yj > 2)).sum())}")
print("g-r of the kept candidates:", K.gr.quantile([0, .25, .5, .75, 1]).round(2).tolist())
# 2. SIMBAD and the failed NSC queries
sim, nsc2 = [], []
for p in K.itertuples():
    s = tap(SB, f"SELECT main_id, otype FROM basic WHERE 1=CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS', {p.right_ascension:.6f}, {p.declination:.6f}, {10 / 3600:.6f}))")
    sim.append("query failed" if s is None else ("; ".join(f"{a} ({b})" for a, b in zip(s.main_id, s.otype)) or "none"))
    v = p.nsc
    if p.nsc == "query failed":
        dd = 2.5 / 3600
        dr_ = dd / np.cos(np.radians(p.declination))
        n = tap(DL, "SELECT ra, dec, pmra, pmraerr, pmdec, pmdecerr FROM nsc_dr2.object WHERE "
                    f"ra BETWEEN {p.right_ascension - dr_:.6f} AND {p.right_ascension + dr_:.6f} AND dec BETWEEN {p.declination - dd:.6f} AND {p.declination + dd:.6f}")
        if n is None:
            v = "query failed"
        elif not len(n):
            v = "no object"
        else:
            m = n.iloc[0]
            chi = float(np.hypot((m.pmra - p.pmx) / np.hypot(m.pmraerr, p.e_pm), (m.pmdec - p.pmy) / np.hypot(m.pmdecerr, p.e_pm)))
            v = f"{'disagrees' if chi > 3 else 'compatible'} ({m.pmra:+.1f} {m.pmdec:+.1f} +- {m.pmraerr:.1f}, {chi:.1f} sigma)"
    nsc2.append(v)
K["simbad_10as"], K["nsc_retry"] = sim, nsc2
print("SIMBAD within 10 arcsec:", pd.Series(sim).map(lambda x: x if x in ("none", "query failed") else "has an entry").value_counts().to_dict())
print(K[~K.simbad_10as.isin(["none", "query failed"])][["object_id", "right_ascension", "declination", "simbad_10as"]].to_string())
print("NSC retry:", K[K.nsc == "query failed"].nsc_retry.tolist())
K[["object_id", "right_ascension", "declination", "gr", "sig_jh", "sig_yj", "lsig_jh", "lsig_yj", "firm", "local_rule", "local_firm", "simbad_10as", "nsc", "nsc_retry"]].round(3).to_csv(H + "/pub/posthoc.csv", index=False)
# 3. unmeasured tiles
TL = {r["tile_index"]: float(r["dec"]) for r in csv.DictReader(open(H + "/tiles.csv"))}
done = {os.path.basename(f)[:-5] for f in __import__("glob").glob(H + "/tiles/*.json")}
miss = [d for t, d in TL.items() if t not in done]
print(f"tiles with no output: {len(miss)}; Dec from {min(miss):.1f} to {max(miss):.1f}; south of Dec +30: {sum(d < 30 for d in miss)}")
ok_dec = [TL[t] for t in done if t in TL]
print(f"tiles with an output: Dec from {min(ok_dec):.1f} to {max(ok_dec):.1f}")
