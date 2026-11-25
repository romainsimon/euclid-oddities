"""Track M, second stage: summary of the fit outputs (after the freeze). Overlap with stage one, warm-candidate residuals in magnitudes, table of the strong-absorption candidates,
and the list handed to the pixel step (written as sel_m2/irfaint.csv, the input format of mp.py)."""
import os

import numpy as np
import pandas as pd

H = os.path.expanduser("~/trackm")
O = pd.read_csv(H + "/m2/out/fit_all.csv.gz", low_memory=False)
q = O[O.quality]
warm = q[(q.teff_best > 7000) & (q.teff_best < 15000)]
print("warm candidates, median observed minus ordinary-model magnitude:")
for b in ["g", "r", "i", "z", "y", "j", "h"]:
    sig = np.sqrt(warm["e_" + b] ** 2)
    model = warm["f_" + b] - warm["z_" + b] * np.sqrt(warm["e_" + b] ** 2 + (0.921 * (0.03 if b in "griz" else 0.05) * warm["f_" + b].clip(lower=0)) ** 2)
    dm = -2.5 * np.log10((warm["f_" + b] / model).where((warm["f_" + b] > 0) & (model > 0)))
    print(f"   {b}: {dm.median():+.3f} mag (median S/N {np.median(warm['f_' + b] / sig):.0f}, n {dm.notna().sum()})")
vis = -2.5 * np.log10(warm.f_vis / warm.vis_pred)
print(f"   VIS (not fitted): {vis.median():+.3f} mag; the Gaia calibrators gave +0.141")
S = O[O.strong_cia].copy()
P = pd.read_csv(H + "/pub/posthoc.csv")
C = pd.read_csv(H + "/pub/ir_deficit_candidates.csv")
S["stage1"] = np.where(S.object_id.isin(P.object_id[P.local_firm]), "firm 49", np.where(S.object_id.isin(P.object_id), "kept 143", np.where(S.object_id.isin(C.object_id), "catalogue 221, rejected", "not selected")))
print(f"strong absorption: {len(S)}; stage one status:", S.stage1.value_counts().to_dict())
print(f"of the 143 kept in stage one: quality {int(q.object_id.isin(P.object_id).sum())}, strong absorption {int(S.object_id.isin(P.object_id).sum())}; of the 49 firm: {int(S.object_id.isin(P.object_id[P.local_firm]).sum())}")
k143 = O[O.object_id.isin(P.object_id)]
print("the 143 by best composition:", k143.comp_best.value_counts().to_dict(), "| median dchi2 ordinary - best:", round(float((k143.chi2_weak - k143.chi2_best).median()), 1),
      "| with p_best < 0.001:", int((k143.p_best < 1e-3).sum()), "| failing on the other flux type only:", int((k143.strong_cia_primary & ~k143.strong_cia_other).sum()))
S["dchi2"] = S.chi2_weak - S.chi2_best
S["r"] = 22.5 - 2.5 * np.log10(S.flux_r)
S["snr_j"], S["snr_h"] = S.f_j / S.e_j, S.f_h / S.e_h
S = S.sort_values("dchi2", ascending=False).reset_index(drop=True)
pd.set_option("display.width", 320)
pd.set_option("display.max_rows", 100)
c = ["object_id", "right_ascension", "declination", "r", "pm", "comp_best", "teff_best", "tmax_near", "chi2_best", "dchi2", "chi2_H", "chi2_He", "teff_H", "n", "snr_j", "snr_h", "z_y", "z_j", "z_h", "d_pc", "vtan", "vtan_cons", "ultracool", "stage1"]
print(S[c].round(2).to_string())
os.makedirs(H + "/sel_m2", exist_ok=True)
W = pd.read_csv(H + "/sel_all/wd.csv.gz")
I = pd.read_csv(H + "/sel_all/irfaint.csv")
X = W[W.object_id.isin(S.object_id)].merge(S[["object_id", "teff_best", "comp_best", "dchi2"]], on="object_id").sort_values("dchi2", ascending=False)
for col in I.columns:
    if col not in X.columns:
        X[col] = np.nan
X["bb_jh"] = 0.0
X[list(I.columns) + ["teff_best", "comp_best", "dchi2"]].to_csv(H + "/sel_m2/irfaint.csv", index=False)
hal = O[O.halo]
print(f"halo candidates {len(hal)}: quality {int(hal.quality.sum())}; median Teff(H) {hal.teff_H.median():.0f} K; r median {np.median(22.5 - 2.5 * np.log10(hal.flux_r)):.1f}; chi2_H/(n-2) median {np.median(hal.chi2_H / (hal.n - 2)):.1f}; "
      f"above 500 km/s: {int(hal.unbound.sum())}, of which pm > 100 mas/yr {int((hal.unbound & (hal.pm > 100)).sum())}, Teff(H) > 10000 K {int((hal.unbound & (hal.teff_H > 10000)).sum())}")
print("all candidates: median Teff of the better of H/He:", float(np.where(O.chi2_H <= O.chi2_He, O.teff_H, O.teff_He).mean().round()), "| below 5000 K:", int((np.where(O.chi2_H <= O.chi2_He, O.teff_H, O.teff_He) < 5000).sum()),
      "| below 4000 K:", int((np.where(O.chi2_H <= O.chi2_He, O.teff_H, O.teff_He) < 4000).sum()), "| reduced chi2 of the best model, median:", round(float((q.chi2_best / (q.n - 2)).median()), 2), "| p_best < 0.001:", int((q.p_best < 1e-3).sum()))
