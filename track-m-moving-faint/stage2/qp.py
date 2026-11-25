"""Track M, second stage: final tables (rule K columns and public files). Run after qf.py run, qo.py and mp.py m2.
Writes ~/trackm/pub2/: interesting_candidates.csv, fits_all.csv.gz, halo_candidates.csv, gaia_strong_absorption.csv, sheets."""
import io
import json
import os
import time

import numpy as np
import pandas as pd
import requests
from PIL import Image

H = os.path.expanduser("~/trackm")
OUT = H + "/pub2"
SB = "https://simbad.idia.ac.za/simbad/sim-tap/sync"
DL = "https://datalab.noirlab.edu/tap/sync"
BANDS = ["g", "r", "i", "z", "y", "j", "h"]
# eye check by Claude Fable 5.2 (25 Nov 2026), rows of sel_m2/irfaint.png; none removed beyond the pixel step
EYE = {17: "H image elongated, low signal", 30: "star 3 arcsec north", 35: "masked area 2.5 arcsec east in J, artefact 4 arcsec east in Y", 40: "bright galaxy 5 arcsec north; the H background may be affected",
       44: "faint neighbour 1.5 arcsec south"}


def tap(u, q):
    for _ in range(2):
        try:
            r = requests.post(u, data=dict(REQUEST="doQuery", LANG="ADQL", FORMAT="csv", QUERY=q), timeout=(10, 25))
            if r.status_code == 200 and not r.text.lstrip().startswith("<"):
                return pd.read_csv(io.StringIO(r.text))
        except Exception:
            pass
        time.sleep(3)
    return None


os.makedirs(OUT + "/sheets", exist_ok=True)
O = pd.read_csv(H + "/m2/out/fit_all.csv.gz", low_memory=False)
O["r"] = 22.5 - 2.5 * np.log10(O.flux_r.where(O.flux_r > 0))
for b in BANDS:
    O["snr_" + b] = O["f_" + b] / O["e_" + b]
O["dchi2"] = O.chi2_weak - O.chi2_best
O["d_best_model"] = np.select([O.comp_best == c for c in ("H", "He", "HeH8", "HeH5", "HeH2")], [O["d_" + c] for c in ("H", "He", "HeH8", "HeH5", "HeH2")])
O["vtan_best_model"] = 4.74047e-3 * O.pm * O.d_best_model
fitc = (["object_id", "right_ascension", "declination", "r", "pm", "pmx", "pmy", "e_pm", "ebv", "quality", "n"] + [f"{k}_{c}" for c in ("H", "He") for k in ("teff", "tlo", "thi", "chi2", "d", "dcons")]
        + ["comp_best", "teff_best", "chi2_best", "p_best", "cia_best", "tmax_near", "chi2_weak", "comp_weak", "teff_weak", "dchi2", "d_best_model", "vtan_best_model"] + ["z_" + b for b in BANDS] + ["snr_" + b for b in BANDS]
        + ["d_pc", "d_cons_pc", "vtan", "vtan_cons", "halo", "unbound", "strong_cia_primary", "strong_cia_other", "strong_cia", "ultracool"])
O[fitc].round(6).to_csv(OUT + "/fits_all.csv.gz", index=False)
O[O.halo][fitc].round(6).sort_values("vtan_cons", ascending=False).to_csv(OUT + "/halo_candidates.csv", index=False)
S = O[O.strong_cia].sort_values("dchi2", ascending=False).reset_index(drop=True)
X = pd.read_csv(H + "/sel_m2/irfaint_pix.csv")
assert (X.object_id.values == S.object_id.values).all()
S["row"] = np.arange(len(S))
S["pixel_step"] = np.where(X.verdict.str.contains("missing"), X.verdict, np.where(X.verdict.str.contains("J not confirmed"), "passes (forced J S/N below 5 on the pixels)", "passes"))
for k in ("VIS_snr", "NIR_Y_snr", "NIR_J_snr", "NIR_H_snr"):
    S["pix_" + k] = X[k].values
S["eye_note"] = [EYE.get(i, "") for i in range(len(S))]
P = pd.read_csv(H + "/pub/posthoc.csv")
C = pd.read_csv(H + "/pub/ir_deficit_candidates.csv")
S["stage_one"] = np.where(S.object_id.isin(P.object_id[P.local_firm]), "kept, firm in two colours", np.where(S.object_id.isin(P.object_id), "kept", np.where(S.object_id.isin(C.object_id), "catalogue step only", "not selected")))
sim, nsc = [], []
for p in S.itertuples():
    s = tap(SB, f"SELECT main_id, otype FROM basic WHERE 1=CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS', {p.right_ascension:.6f}, {p.declination:.6f}, {10 / 3600:.6f}))")
    sim.append("query failed" if s is None else ("; ".join(f"{a} ({b})" for a, b in zip(s.main_id, s.otype)) or "none"))
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
    nsc.append(v)
S["simbad_10as"], S["nsc_dr2"] = sim, nsc
old = dict(zip(P.object_id, P.nsc_retry))                                  # stage one already holds this column for the 143
S["nsc_dr2"] = [old.get(o, v) if v == "query failed" else v for o, v in zip(S.object_id, S.nsc_dr2)]
S["kept"] = S.pixel_step.str.startswith("passes")
S["class"] = np.where(S.ultracool, "ultracool (every acceptable model below 4000 K)", np.where(S.teff_best < 4000, "strong absorption, best model below 4000 K", "strong absorption, mixed hydrogen-helium model"))
pubc = (["row", "object_id", "right_ascension", "declination", "kept", "class", "pixel_step", "eye_note", "stage_one", "r", "pm", "e_pm", "pmx", "pmy", "comp_best", "teff_best", "tmax_near", "chi2_best", "n", "p_best", "dchi2", "cia_best",
         "teff_H", "chi2_H", "teff_He", "chi2_He", "d_best_model", "vtan_best_model", "vtan_cons"] + ["z_" + b for b in BANDS] + ["snr_" + b for b in BANDS] + ["pix_VIS_snr", "pix_NIR_Y_snr", "pix_NIR_J_snr", "pix_NIR_H_snr"]
        + ["f_" + b for b in BANDS] + ["e_" + b for b in BANDS] + ["simbad_10as", "nsc_dr2"])
S[pubc].round(6).to_csv(OUT + "/interesting_candidates.csv", index=False)
K = S[S.kept]
print(f"strong absorption {len(S)}; pixel step:", S.pixel_step.value_counts().to_dict())
print(f"kept {len(K)}: classes", K["class"].value_counts().to_dict())
print("   stage one status:", K.stage_one.value_counts().to_dict())
print("   SIMBAD:", K.simbad_10as.map(lambda x: x if x in ("none", "query failed") else "has an entry").value_counts().to_dict(), "| NSC:", K.nsc_dr2.str.split(" ").str[0].value_counts().to_dict())
print(f"   r {K.r.min():.1f} to {K.r.max():.1f} (median {K.r.median():.1f}); distance with the best model {K.d_best_model.min():.0f} to {K.d_best_model.max():.0f} pc (median {K.d_best_model.median():.0f}); "
      f"velocity with the best model: median {K.vtan_best_model.median():.0f} km/s, above 200: {int((K.vtan_best_model > 200).sum())}; rule J halo: {int(K.halo.sum())}")
print("   best composition:", K.comp_best.value_counts().to_dict(), "| H S/N on pixels above 3:", int((K.pix_NIR_H_snr > 3).sum()), "| J S/N on pixels above 10:", int((K.pix_NIR_J_snr > 10).sum()))
print(K[~K.simbad_10as.isin(["none", "query failed"])][["row", "simbad_10as"]].to_string())
# sheets
im = Image.open(H + "/sel_m2/irfaint.png").convert("RGB")
for k in range(0, len(S), 12):
    im.crop((0, k * 218, im.size[0], min((k + 12) * 218, im.size[1]))).save(f"{OUT}/sheets/strong_absorption_{k // 12:02d}.jpg", quality=88)
# the Gaia white dwarfs flagged by the same rule (development sample)
G = pd.read_csv(H + "/m2/gcal_fit.csv", low_memory=False)
G = G[G.strong_cia].copy()
G["d_best_model"] = [g["d_" + g.comp_best] for _, g in G.iterrows()]
G["d_parallax"] = 1000 / G.Plx
G["vtan_gaia"] = 4.74047 * np.hypot(G.pmRA, G.pmDE) / G.Plx
G["M_G"] = G.Gmag + 5 * np.log10(G.Plx / 100)
gc = ["GaiaEDR3", "right_ascension", "declination", "Gmag", "Plx", "M_G", "TeffH", "comp_best", "teff_best", "chi2_best", "chi2_weak", "chi2_H", "chi2_He", "d_best_model", "d_parallax", "vtan_gaia", "z_y", "z_j", "z_h"]
G[gc].round(3).to_csv(OUT + "/gaia_strong_absorption.csv", index=False)
pd.set_option("display.width", 250)
print("Gaia white dwarfs with strong absorption:")
print(G[["GaiaEDR3", "Gmag", "Plx", "M_G", "TeffH", "comp_best", "teff_best", "d_best_model", "d_parallax", "vtan_gaia"]].round(2).to_string())
for f in ("cal.json",):
    json.dump(json.load(open(H + "/m2/" + f)), open(OUT + "/" + f, "w"), indent=1)
