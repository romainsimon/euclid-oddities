"""Track M, second stage: checks made AFTER the results were read (they change no list).
1. Does the near-infrared carry the verdict? Pure-hydrogen and pure-helium fits on g, r, i, z only, Y, J, H predicted; the smaller of the two deficits.
2. NOIRLab Source Catalog DR2: does it exclude zero motion? Motion S/N of the 41 against the whole sample.
3. Sources that meet rule H except for the acceptability of the best model ("fits no model").
4. Positive control of the simulation, and the null distribution of the chi2 difference.
5. Motion during the Legacy Surveys epochs (smear) of the 41.
6. VISTA Hemisphere Survey photometry of the five Gaia white dwarfs.
Writes ~/trackm/pub2/posthoc_m2.csv and fits_no_model.csv."""
import json
import os
import re

import numpy as np
import pandas as pd
import requests

import qf

H = qf.H
C = json.load(open(H + "/m2/cal.json"))
T, TR, cia = qf.tracks()
D, F, K = qf.both("wd", C, T, TR, cia)
A = pd.concat([D, F, K], axis=1)
A["dchi2"] = A.chi2_weak - A.chi2_best
I = pd.read_csv(H + "/pub2/interesting_candidates.csv")
kept = set(I.object_id[I.kept])
# 1. optical-only prediction
Fo = qf.fit(D, T, TR, cia, C["sys"], bands=qf.OPT)
tix = lambda t: ((T[None, :] - np.asarray(t)[:, None]) == 0).argmax(1)
res = {}
for c in ("H", "He"):
    a = (10 / Fo["d_" + c].values) ** 2
    k = tix(Fo["teff_" + c].values)
    pj, ph = a * TR[c, qf.MASS][k, 5], a * TR[c, qf.MASS][k, 6]
    sig = np.sqrt(D.e_j ** 2 + D.e_h ** 2 + (0.921 * C["sys"]["j"] * pj) ** 2 + (0.921 * C["sys"]["h"] * ph) ** 2)
    res[c + "_sig"] = ((D.f_j + D.f_h) - (pj + ph)) / sig
    res[c + "_mag"] = -2.5 * np.log10(((D.f_j + D.f_h) / (pj + ph)).clip(lower=1e-3))
R = pd.DataFrame(res)
A["nir_sig"] = np.maximum(R.H_sig, R.He_sig)          # the smaller deficit (closest to zero or positive)
A["nir_mag"] = np.minimum(R.H_mag, R.He_mag)
A["opt_teff_H"], A["opt_teff_He"] = Fo.teff_H, Fo.teff_He
q = A[A.quality]
k41 = A[A.object_id.isin(kept)]
print(f"1. J+H against the optical-only prediction, smaller deficit of pure H and pure He, in sigma. Quality sample {len(q)}: below -3: {int((q.nir_sig < -3).sum())}, above +3: {int((np.minimum(R.H_sig, R.He_sig)[q.index] > 3).sum())}")
print(f"   the 41: below -3 sigma: {int((k41.nir_sig < -3).sum())}; between -3 and -2: {int(((k41.nir_sig >= -3) & (k41.nir_sig < -2)).sum())}; above -2: {int((k41.nir_sig >= -2).sum())}; deficit in mag: median {k41.nir_mag.median():.2f}, range {k41.nir_mag.min():.2f} to {k41.nir_mag.max():.2f}")
rows = dict(zip(I.object_id, I.row))
weak = k41[k41.nir_sig >= -3]
print("   not clear (rows, sigma):", sorted((int(rows[o]), round(float(s), 1)) for o, s in zip(weak.object_id, weak.nir_sig)))
# 2. third data set and motion S/N
m = I[I.kept].nsc_dr2.astype(str).str.extract(r"\(([-+\d.]+) ([-+\d.]+) \+- ([\d.]+)")
m = m.astype(float)
nsig = np.hypot(m[0], m[1]) / m[2]
print(f"2. NSC DR2 for the 41: motion itself above 3 sigma in NSC for {int((nsig > 3).sum())}, above 2 sigma for {int((nsig > 2).sum())}, of {int(nsig.notna().sum())} with a value; median NSC error {m[2].median():.1f} mas/yr")
snr = A.pm / A.e_pm
print(f"   our motion S/N: the 41 median {snr[k41.index].median():.1f}, below 7: {int((snr[k41.index] < 7).sum())}; whole sample median {snr.median():.1f}, share below 7: {(snr < 7).mean():.2f}")
# 3. fits no model
nm = q[(q.dchi2 >= qf.D_CHI2) & (q.cia_best < qf.CIA_STRONG) & (q.p_best <= qf.P_MIN)]
print(f"3. quality sources with the chi2 difference and the index of rule H but a best model that is not acceptable: {len(nm)}; of which J+H deficit clear {int((nm.nir_sig < -3).sum())}; in the 143 of stage one: "
      f"{int(nm.object_id.isin(pd.read_csv(H + '/pub/posthoc.csv').object_id).sum())}")
nm.assign(r=22.5 - 2.5 * np.log10(nm.flux_r))[["object_id", "right_ascension", "declination", "r", "pm", "comp_best", "teff_best", "chi2_best", "n", "dchi2", "nir_sig", "nir_mag"] + ["z_" + b for b in qf.BANDS]].round(3).sort_values("chi2_best").to_csv(H + "/pub2/fits_no_model.csv", index=False)
print("   their best chi2: median", round(float(nm.chi2_best.median()), 1), "| largest residual band (against the ordinary model):", nm[["z_" + b for b in qf.BANDS]].abs().idxmax(1).value_counts().to_dict())
# 4. simulation: null distribution and positive control
rng = np.random.default_rng(2)
Dq, Fq = D[K.quality.values].reset_index(drop=True), F[K.quality.values].reset_index(drop=True)
S = Dq.copy()
for b in qf.BANDS:
    mod = S["f_" + b] - Fq["z_" + b] * np.sqrt(S["e_" + b] ** 2 + (C["sys"][b] * 0.921 * S["f_" + b].clip(lower=0)) ** 2)
    S["f_" + b] = mod + rng.normal(size=len(S)) * np.sqrt(S["e_" + b] ** 2 + (C["sys"][b] * 0.921 * mod.clip(lower=0)) ** 2)
Fs = qf.fit(S, T, TR, cia, C["sys"])
dn = (Fs.chi2_weak - Fs.chi2_best).values
print(f"4. null draw: chi2 difference median {np.median(dn):.2f}, 99 % {np.percentile(dn, 99):.1f}, 99.9 % {np.percentile(dn, 99.9):.1f}, max {dn.max():.1f}; with index below {qf.CIA_STRONG}: max {dn[Fs.cia_best.values < qf.CIA_STRONG].max():.1f}")
P = D[D.object_id.isin(I.object_id)].reset_index(drop=True)
Fp = F[D.object_id.isin(I.object_id).values].reset_index(drop=True)
comps = np.array(qf.COMPS)
rec = 0
for s in range(5):
    Sp = P.copy()
    kT = tix(Fp.teff_best.values)
    for j, b in enumerate(qf.BANDS):
        mod = np.array([(10 / Fp["d_" + c][i]) ** 2 * TR[c, qf.MASS][kT[i], j] for i, c in enumerate(Fp.comp_best)])
        Sp["f_" + b] = np.where(np.isfinite(P["f_" + b]), mod + rng.normal(size=len(P)) * np.sqrt(P["e_" + b] ** 2 + (C["sys"][b] * 0.921 * mod) ** 2), np.nan)
    rec += int(qf.classify(Sp, qf.fit(Sp, T, TR, cia, C["sys"])).strong_cia.sum())
print(f"   positive control: sources drawn from the best model of the {len(P)} selected ones are selected again in {rec / (5 * len(P)):.2f} of the draws (primary fluxes)")
# 5. smear
W = pd.read_csv(H + "/sel_all/wd.csv.gz", usecols=["object_id", "ls_mjd_min", "ls_mjd_max"])
A = A.merge(W, on="object_id", how="left")
A["smear"] = A.pm * (A.ls_mjd_max - A.ls_mjd_min) / 365.25 / 1000
qq = A[A.quality]
print(f"5. motion during the Legacy Surveys epochs (arcsec): whole quality sample median {qq.smear.median():.2f}, 90 % {qq.smear.quantile(.9):.2f}; the 41: median {qq[qq.object_id.isin(kept)].smear.median():.2f}, max {qq[qq.object_id.isin(kept)].smear.max():.2f}")
for lo, hi in ((0, .15), (.15, .3), (.3, .5), (.5, 3)):
    g = qq[(qq.smear >= lo) & (qq.smear < hi)]
    print(f"   smear {lo}-{hi}: n {len(g)}, strong absorption {int(g.strong_cia.sum())}, median J+H deficit in sigma {g.nir_sig.median():+.2f}, median z residuals g {g.z_g.median():+.2f} z {g.z_z.median():+.2f}")
A[A.object_id.isin(I.object_id)].assign(row=lambda d: d.object_id.map(rows))[["row", "object_id", "nir_sig", "nir_mag", "opt_teff_H", "opt_teff_He", "smear"]].round(3).sort_values("row").to_csv(H + "/pub2/posthoc_m2.csv", index=False)
# 6. VHS for the Gaia five
G = pd.read_csv(H + "/pub2/gaia_strong_absorption.csv")
for g in G.itertuples():
    out = "no answer"
    for h in ("https://vizier.cfa.harvard.edu", "http://vizier.nao.ac.jp", "https://vizier.idia.ac.za"):
        try:
            r = requests.get(h + "/viz-bin/asu-tsv", params={"-source": "II/367", "-c": f"{g.right_ascension:.6f} {g.declination:.6f}", "-c.rs": 5, "-out": "Jap3,e_Jap3,Hap3,e_Hap3,Ksap3,e_Ksap3", "-out.max": 2}, timeout=(10, 40))
            if r.status_code == 200:
                L = [x for x in r.text.splitlines() if x.strip() and not x.startswith("#")]
                out = " | ".join(re.sub(r"\s+", " ", x) for x in L[3:5]) if len(L) > 3 else "not in VHS DR5 within 5 arcsec"
                break
        except Exception:
            pass
    print(f"6. Gaia {g.GaiaEDR3}: VHS J, eJ, H, eH, Ks, eKs (Vega): {out}")
