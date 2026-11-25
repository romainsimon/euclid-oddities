"""Track M, second stage: checks on the sources that "fit no model" and have clean pixels (made after the results were read).
1. Is the optical misfit in the data? Legacy Surveys Tractor fluxes against the Euclid catalogue's own forced DECam fluxes, Tractor fit quality, blending, smear.
2. Euclid VIS against r, i, z: residual from the relation of the whole quality sample.
3. SIMBAD within 10 arcsec.
Writes ~/trackm/pub2/fits_no_model.csv again with the pixel verdict and these columns."""
import io
import os
import time

import numpy as np
import pandas as pd
import requests

H = os.path.expanduser("~/trackm")
N = pd.read_csv(H + "/pub2/fits_no_model.csv")
N = N[[c for c in N.columns if c not in ("pixels", "eye_note", "smear", "dg_euclid", "dr_euclid", "di_euclid", "vis_resid", "fracflux_max", "rchisq_max", "simbad_10as", "group")]]
P = pd.read_csv(H + "/sel_m3/irfaint_pix.csv")
A = pd.read_csv(H + "/m2/out/fit_all.csv.gz").drop_duplicates("object_id")
W = pd.read_csv(H + "/sel_all/wd.csv.gz", usecols=["object_id", "ls_mjd_min", "ls_mjd_max"]).drop_duplicates("object_id")
A = A.merge(W, on="object_id", how="left")
A["smear"] = A.pm * (A.ls_mjd_max - A.ls_mjd_min) / 365.25 / 1000
for b in "gri":
    fe = A[f"flux_{b}_ext_decam_templfit"]                      # microjansky
    A[f"d{b}_euclid"] = (22.5 - 2.5 * np.log10(A["flux_" + b].where(A["flux_" + b] > 0))) - (23.9 - 2.5 * np.log10(fe.where(fe > 0)))
A["fracflux_max"] = A[["fracflux_g", "fracflux_r", "fracflux_i", "fracflux_z"]].max(axis=1)
A["rchisq_max"] = A[["rchisq_g", "rchisq_r", "rchisq_i", "rchisq_z"]].max(axis=1)
m = lambda b: 22.5 - 2.5 * np.log10(A["flux_" + b].where(A["flux_" + b] > 0))
A["vis_ab"] = 23.9 - 2.5 * np.log10(A.flux_vis_psf.where(A.flux_vis_psf > 0))
ri = 22.5 - 2.5 * np.log10(((A.flux_r + A.flux_i + A.flux_z) / 3).where(A.flux_r > 0))
x, y = (m("r") - m("z")), A.vis_ab - ri
q = A.quality & x.notna() & y.notna() & (x.abs() < 2)
co = np.polyfit(x[q], y[q], 3)
A["vis_resid"] = y - np.polyval(co, x)
sd = 1.4826 * (A.vis_resid[q] - A.vis_resid[q].median()).abs().median()
print(f"quality sample {int(q.sum())}: VIS residual scatter {sd:.3f} mag; Tractor minus Euclid forced DECam, median and robust scatter: " + "; ".join(
    f"{b} {A.loc[q, f'd{b}_euclid'].median():+.3f} +- {1.4826 * (A.loc[q, f'd{b}_euclid'] - A.loc[q, f'd{b}_euclid'].median()).abs().median():.3f}" for b in "gri"))
print(f"   smear median {A.smear[q].median():.2f}, fracflux_max 90 % {A.fracflux_max[q].quantile(.9):.2f}, rchisq_max 90 % {A.rchisq_max[q].quantile(.9):.2f}")
hole = (P.NIR_Y_bad > 0) | (P.NIR_J_bad > 0) | (P.NIR_H_bad > 0)
P["pixels"] = np.where(hole, "missing pixels within 1.5 arcsec", "clean")
EYE = {5: "galaxy 4 arcsec east", 17: "two faint neighbours within 4 arcsec", 22: "galaxy 3 arcsec north", 36: "two galaxies 3 to 5 arcsec north-east", 37: "galaxies 3 arcsec north and 5 arcsec south",
       38: "faint neighbours within 5 arcsec", 39: "linear streak 2 to 3 arcsec away in every band"}
P["eye_note"] = [EYE.get(i, "") for i in range(len(P))]
P["sheet_row"] = range(len(P))
T = N.merge(P[["object_id", "sheet_row", "pixels", "eye_note", "NIR_J_snr", "NIR_H_snr"]], on="object_id").merge(
    A[["object_id", "smear", "dg_euclid", "dr_euclid", "di_euclid", "vis_resid", "fracflux_max", "rchisq_max", "e_pm"]], on="object_id", how="left").sort_values("sheet_row")
SB = "https://simbad.idia.ac.za/simbad/sim-tap/sync"
sim = []
for p in T.itertuples():
    out = "query failed"
    if p.pixels == "clean":
        qy = f"SELECT main_id, otype FROM basic WHERE 1=CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS', {p.right_ascension:.6f}, {p.declination:.6f}, {10 / 3600:.6f}))"
        for _ in range(3):
            try:
                r = requests.post(SB, data=dict(REQUEST="doQuery", LANG="ADQL", FORMAT="csv", QUERY=qy), timeout=(15, 60))
                if r.status_code == 200 and not r.text.lstrip().startswith("<"):
                    t = pd.read_csv(io.StringIO(r.text))
                    out = "; ".join(f"{a} ({b})" for a, b in zip(t.main_id, t.otype)) or "none"
                    break
            except Exception:
                pass
            time.sleep(2)
    else:
        out = "not queried"
    sim.append(out)
T["simbad_10as"] = sim
clean = T.pixels == "clean"
deficit = T.nir_sig < -3
iso = T.eye_note == ""
T["group"] = np.select([~clean, clean & deficit & iso, clean & deficit], ["missing pixels", "clean, clear near-infrared deficit, isolated", "clean, clear near-infrared deficit, neighbour or streak"], "clean, no clear near-infrared deficit")
print(T.group.value_counts().to_string())
pd.set_option("display.width", 330)
pd.set_option("display.max_rows", 100)
c = ["sheet_row", "object_id", "r", "pm", "e_pm", "comp_best", "teff_best", "chi2_best", "dchi2", "nir_sig", "nir_mag", "smear", "dg_euclid", "dr_euclid", "di_euclid", "vis_resid", "fracflux_max", "rchisq_max", "z_g", "z_r", "z_i", "z_z", "simbad_10as", "eye_note"]
print(T[clean][c].round(2).to_string(index=False))
g = T[clean & deficit]
print(f"clean with clear deficit {len(g)}: median Tractor minus Euclid g {g.dg_euclid.median():+.3f}, r {g.dr_euclid.median():+.3f}, i {g.di_euclid.median():+.3f}; VIS residual median {g.vis_resid.median():+.3f}, "
      f"beyond 3 scatter {int((g.vis_resid.abs() > 3 * sd).sum())}; smear median {g.smear.median():.2f}, max {g.smear.max():.2f}; SIMBAD none for {int((g.simbad_10as == 'none').sum())}")
s1 = pd.read_csv(H + "/pub/posthoc.csv")
print("in the 143 of stage one:", int(g.object_id.isin(s1.object_id).sum()), "of", len(g))
T.drop(columns=["e_pm"]).round(3).to_csv(H + "/pub2/fits_no_model.csv", index=False)
