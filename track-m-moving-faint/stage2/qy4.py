"""Track M, second stage: VISTA Hemisphere Survey DR5 photometry (NOIRLab Data Lab) of the five Gaia white dwarfs, with a coverage test around each."""
import math
import os

import pandas as pd
import requests

G = pd.read_csv(os.path.expanduser("~/trackm/pub2b/gaia_strong_absorption.csv"), dtype={"GaiaEDR3": str})
U = "https://datalab.noirlab.edu/tap/sync"


def q(s):
    try:
        r = requests.post(U, data={"REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "csv", "QUERY": s}, timeout=(10, 120))
        return r.text[:700].strip().replace("\n", " | ") if r.status_code == 200 else f"HTTP {r.status_code} {r.text[:200]}"
    except Exception as e:
        return "error " + str(e)[:120]


def box(g, r):
    dr, dd = r / 3600 / math.cos(math.radians(g.dec_euclid)), r / 3600
    return f"ra2000 BETWEEN {g.ra_euclid - dr} AND {g.ra_euclid + dr} AND dec2000 BETWEEN {g.dec_euclid - dd} AND {g.dec_euclid + dd}"


for g in (G.itertuples() if os.environ.get("QUERY") else []):
    print(g.GaiaEDR3, "within 4 arcsec:", q(f"SELECT ra2000,dec2000,japermag3,japermag3err,hapermag3,hapermag3err,ksapermag3,ksapermag3err FROM vhs_dr5.vhs_cat_v3 WHERE {box(g, 4)}"))
    print("   within 90 arcsec, count and faintest J with error below 0.2:", q(f"SELECT count(*), max(japermag3) FROM vhs_dr5.vhs_cat_v3 WHERE {box(g, 90)} AND japermag3err < 0.2 AND japermag3err > 0"))

# Public table: the same rows with the VISTA J magnitude. The values are those printed by the query above on 25 Nov 2026 (Vega, 2 arcsec aperture,
# the detection with the smaller error when there are two); the service timed out on a second pass, so they are written here by hand.
VHS = {"6487573599829346176": (19.101, 0.068, 2), "4729108809392699392": (18.564, 0.035, 1), "4727802456435996544": (19.889, 0.144, 2), "4768450851559548672": (None, None, 0),
       "4922114228674321792": (18.496, 0.030, 1)}
G["J_vhs_vega"], G["e_J_vhs"], G["n_vhs"] = zip(*[VHS[i] for i in G.GaiaEDR3])
G = G.rename(columns={"ra_euclid": "right_ascension", "dec_euclid": "declination"})
G.to_csv(os.path.expanduser("~/trackm/pub2/gaia_strong_absorption.csv"), index=False)
pd.set_option("display.width", 400)
print(G[["GaiaEDR3", "WDJname", "right_ascension", "declination", "Gmag", "Plx", "Pwd", "g_ls", "r_ls", "i_ls", "z_ls", "Y_euclid_ap", "J_euclid_ap", "H_euclid_ap", "J_vhs_vega", "e_J_vhs"]].to_string(index=False))
print(G[["GaiaEDR3", "e_g_ls", "e_r_ls", "e_i_ls", "e_z_ls", "e_Y_euclid_ap", "e_J_euclid_ap", "e_H_euclid_ap", "pmRA", "pmDE", "TeffH_gf21", "teff_best", "comp_best"]].to_string(index=False))
