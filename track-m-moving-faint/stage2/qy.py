"""Track M, second stage: checks on the five Gaia white dwarfs before writing to a specialist (made after the results were read).
1. Every VizieR table with a row within 4 arcsec of each star; explicit look in the infrared-faint sample (J/ApJ/934/36).
2. VISTA Hemisphere Survey: control on brighter Gaia white dwarfs of the same sample, then the five.
3. Forced WISE fluxes of the Legacy Surveys.
4. Public table with the photometry: writes ~/trackm/pub2/gaia_strong_absorption.csv again (6-decimal positions, AB magnitudes, errors)."""
import io
import os
import re

import numpy as np
import pandas as pd
import requests

H = os.path.expanduser("~/trackm")
HOSTS = ("https://vizier.cfa.harvard.edu", "http://vizier.nao.ac.jp", "https://vizier.idia.ac.za")


def viz(params, timeout=(10, 90)):
    for h in HOSTS:
        try:
            r = requests.get(h + "/viz-bin/asu-tsv", params=params, timeout=timeout)
            if r.status_code == 200 and "#" in r.text:
                return r.text
        except Exception:
            pass
    return None


def rows(text):
    if text is None:
        return None
    return [x for x in text.splitlines() if x.strip() and not x.startswith("#")]


G = pd.read_csv(H + "/pub2/gaia_strong_absorption.csv", dtype={"GaiaEDR3": str})
W = pd.read_csv(H + "/m2/gwd.csv", dtype={"GaiaEDR3": str})
W = W[W.GaiaEDR3.isin(G.GaiaEDR3)].drop_duplicates("GaiaEDR3").set_index("GaiaEDR3").loc[G.GaiaEDR3]
print("matched in gwd:", len(W))
# 1. all tables
for g, w in zip(G.itertuples(), W.itertuples()):
    t = viz({"-source": "", "-c": f"{w.RA_ICRS:.6f} {w.DE_ICRS:.6f}", "-c.rs": 4, "-out.max": 1, "-out": "_r", "-meta.all": 1}, timeout=(10, 240))
    if t is None:
        print("1.", g.GaiaEDR3, "no answer")
        continue
    tabs = re.findall(r"^#Table\s+(\S+?):?\s*$", t, flags=re.M) or re.findall(r"^#Name:\s*(\S+)", t, flags=re.M)
    cats = sorted({"/".join(x.split("/")[:-1]) if x.count("/") > 1 else x for x in tabs})
    print(f"1. {g.GaiaEDR3} ({w.WDJname}): {len(tabs)} tables in {len(cats)} catalogues")
    print("   ", " ".join(cats))
    b = rows(viz({"-source": "J/ApJ/934/36", "-c": f"{w.RA_ICRS:.6f} {w.DE_ICRS:.6f}", "-c.rs": 10, "-out.max": 3}))
    print("    J/ApJ/934/36 (Bergeron et al. 2022, infrared-faint sample):", "no answer" if b is None else ("NOT in it" if len(b) <= 3 else b[3:]))
# 2. VHS
A = pd.read_csv(H + "/m2/gwd.csv", dtype={"GaiaEDR3": str})
ctl = A[(A.Gmag < 17.5) & (A.DE_ICRS < -45)].drop_duplicates("GaiaEDR3").head(6)
full = viz({"-source": "II/367", "-c": f"{ctl.RA_ICRS.iloc[0]:.6f} {ctl.DE_ICRS.iloc[0]:.6f}", "-c.rs": 5, "-out.max": 2})
print("2. VHS control, raw answer for the first control star:")
print("\n".join((full or "no answer").splitlines()[-12:]))


def vhs(ra, dec):
    L = rows(viz({"-source": "II/367/vhs_dr5", "-c": f"{ra:.6f} {dec:.6f}", "-c.rs": 3, "-out.max": 2, "-out": "_r,Yap3,e_Yap3,Jap3,e_Jap3,Hap3,e_Hap3,Ksap3,e_Ksap3"}))
    return "no answer" if L is None else (" | ".join(re.sub(r"\s+", " ", x) for x in L[3:]) if len(L) > 3 else "no row within 3 arcsec")


for c in ctl.itertuples():
    print(f"   control G {c.Gmag:.2f} at {c.RA_ICRS:.4f} {c.DE_ICRS:.4f}: {vhs(c.RA_ICRS, c.DE_ICRS)}")
for g, w in zip(G.itertuples(), W.itertuples()):
    print(f"   Gaia {g.GaiaEDR3}: {vhs(w.RA_ICRS, w.DE_ICRS)}  (also at the Euclid position: {vhs(w.right_ascension, w.declination)})")
# 3 and 4. photometry
L = pd.read_csv(H + "/m2/gcal_ls.csv").drop_duplicates("object_id").set_index("object_id")
E = pd.read_csv(H + "/m2/gcal_eu.csv").drop_duplicates("object_id").set_index("object_id")
ab = lambda f: 22.5 - 2.5 * np.log10(f)
out = []
for g, w in zip(G.itertuples(), W.itertuples()):
    l, e = L.loc[w.object_id], E.loc[w.object_id]
    d = dict(GaiaEDR3=g.GaiaEDR3, WDJname=w.WDJname, ra_gaia_2016=round(w.RA_ICRS, 6), dec_gaia_2016=round(w.DE_ICRS, 6), euclid_object_id=w.object_id, ra_euclid=round(w.right_ascension, 6),
             dec_euclid=round(w.declination, 6), Gmag=round(w.Gmag, 3), BPmag=round(w.BPmag, 3), RPmag=round(w.RPmag, 3), Plx=round(w.Plx, 3), pmRA=round(w.pmRA, 2), pmDE=round(w.pmDE, 2), Pwd=round(w.Pwd, 3),
             TeffH_gf21=w.TeffH, TeffHe_gf21=w.TeffHe)
    for b in "griz":
        f, iv, tr = l["flux_" + b], l["flux_ivar_" + b], l["mw_transmission_" + b]
        d[b + "_ls"], d["e_" + b + "_ls"] = round(ab(f), 3), round(1.0857 / (f * iv ** 0.5), 3)
        d["mw_transmission_" + b] = round(tr, 3)
    for b in "yjh":
        for k, nm in (("2fwhm_aper", "ap"), ("templfit", "tf")):
            f, s = e[f"flux_{b}_{k}"], e[f"fluxerr_{b}_{k}"]                  # microjansky
            d[f"{b.upper()}_euclid_{nm}"], d[f"e_{b.upper()}_euclid_{nm}"] = round(23.9 - 2.5 * np.log10(f), 3), round(1.0857 * s / f, 3)
    d["VIS_euclid_psf"] = round(23.9 - 2.5 * np.log10(e.flux_vis_psf), 3)
    for b in ("w1", "w2"):
        f, iv = l["flux_" + b], l["flux_ivar_" + b]
        d["flux_" + b + "_nmgy"], d["e_flux_" + b + "_nmgy"] = round(f, 3), round(iv ** -0.5, 3)
    d.update(comp_best=g.comp_best, teff_best=g.teff_best, chi2_best=g.chi2_best, chi2_ordinary=g.chi2_weak, chi2_pureH=g.chi2_H, chi2_pureHe=g.chi2_He, d_best_model=g.d_best_model, d_parallax=g.d_parallax,
             vtan_gaia=g.vtan_gaia, z_y=g.z_y, z_j=g.z_j, z_h=g.z_h)
    out.append(d)
O = pd.DataFrame(out)
print("3. forced WISE (nanomaggies, flux and error):")
print(O[["GaiaEDR3", "flux_w1_nmgy", "e_flux_w1_nmgy", "flux_w2_nmgy", "e_flux_w2_nmgy"]].to_string(index=False))
print("4.")
print(O[["GaiaEDR3", "Gmag", "Plx", "Pwd", "g_ls", "r_ls", "i_ls", "z_ls", "Y_euclid_ap", "J_euclid_ap", "H_euclid_ap", "e_H_euclid_ap", "Y_euclid_tf", "J_euclid_tf", "H_euclid_tf", "VIS_euclid_psf"]].to_string(index=False))
os.makedirs(H + "/pub2b", exist_ok=True)
O.to_csv(H + "/pub2b/gaia_strong_absorption.csv", index=False)
