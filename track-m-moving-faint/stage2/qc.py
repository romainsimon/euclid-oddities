"""Track M, second stage, check made after the results were read: the VIS band, which is not fitted.
Observed VIS - r (Euclid 2024-25 against Legacy Surveys 2013-19) minus the value of the best model. A source that faded between the two surveys,
or a wrong pairing, would show here; so would a model that is wrong between 0.55 and 0.9 micron."""
import os

import numpy as np
import pandas as pd

H = os.path.expanduser("~/trackm")
S = pd.read_csv(H + "/models/synth.csv")
O = pd.read_csv(H + "/m2/out/fit_all.csv.gz", low_memory=False)


def vis_r(comp, teff, mass=0.6):
    out = []
    for t, g in S[S.comp == comp].groupby("teff"):
        g = g.sort_values("mass")
        out.append((t, np.interp(mass, g.mass, g.vis - g.r)))
    a = np.array(out)
    return np.interp(teff, a[:, 0], a[:, 1])


O["vr_obs"] = -2.5 * np.log10((O.f_vis / O.f_r).where((O.f_vis > 0) & (O.f_r > 0)))
O["vr_best"] = [vis_r(c, t) for c, t in zip(O.comp_best, O.teff_best)]
O["vr_ord"] = [vis_r(c, t) for c, t in zip(O.comp_weak, O.teff_weak)]
O["d_best"], O["d_ord"] = O.vr_obs - O.vr_best, O.vr_obs - O.vr_ord
q = O[O.quality]
mad = lambda v: 1.4826 * (v - v.median()).abs().median()
print(f"quality candidates {len(q)}: observed minus best-model VIS - r, median {q.d_best.median():+.3f}, robust scatter {mad(q.d_best):.3f}")
for lo, hi in ((2500, 4000), (4000, 5000), (5000, 7000), (7000, 20000)):
    m = q[(q.teff_best >= lo) & (q.teff_best < hi) & ~q.strong_cia]
    print(f"   not flagged, best Teff {lo}-{hi}: n {len(m)}, median {m.d_best.median():+.3f}, scatter {mad(m.d_best):.3f}")
K = pd.read_csv(H + "/pub2/interesting_candidates.csv")
k = O[O.object_id.isin(K.object_id[K.kept])].merge(K[["object_id", "row", "class"]], on="object_id")
print(f"the {len(k)} kept strong-absorption candidates: against the best model, median {k.d_best.median():+.3f}, scatter {mad(k.d_best):.3f}, min {k.d_best.min():+.3f}, max {k.d_best.max():+.3f}; "
      f"against the best ordinary model, median {k.d_ord.median():+.3f}, scatter {mad(k.d_ord):.3f}")
for c, g in k.groupby("class"):
    print(f"   {c}: n {len(g)}, best model {g.d_best.median():+.3f}, ordinary {g.d_ord.median():+.3f}")
ref = q.d_best.median()
out = k[(k.d_best - ref).abs() > 0.25]
print("more than 0.25 mag from the population median:", out[["row", "comp_best", "teff_best", "d_best", "d_ord"]].round(2).to_dict("records"))
k[["object_id", "row", "vr_obs", "vr_best", "vr_ord", "d_best", "d_ord"]].round(3).to_csv(H + "/pub2/vis_check.csv", index=False)
