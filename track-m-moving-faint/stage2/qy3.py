"""Track M, second stage: is there any VISTA or 2MASS source near the five Gaia white dwarfs? (coverage test, 60 arcsec, then the star itself)"""
import re
import pandas as pd
from qy2 import qy, H
G = pd.read_csv(H + "/pub2b/gaia_strong_absorption.csv", dtype={"GaiaEDR3": str})
for g in G.itertuples():
    for src, cols in (("II/367/vhs_dr5", "_r,Jap3,e_Jap3,Hap3,e_Hap3,Ksap3,e_Ksap3"), ("II/343/viking2", "_r,Jap3,e_Jap3,Hap3,e_Hap3,Ksap3,e_Ksap3"), ("II/246/out", "_r,Jmag,Hmag")):
        t = qy.viz({"-source": src, "-c": f"{g.ra_euclid:.6f} {g.dec_euclid:.6f}", "-c.rs": 90, "-out.max": 200, "-out": cols, "-sort": "_r"})
        L = qy.rows(t)
        if L is None:
            print(g.GaiaEDR3, src, "no answer"); continue
        d = [x.split("\t") for x in L[3:]]
        near = [x for x in d if float(x[0]) < 3]
        print(g.GaiaEDR3, src, "sources within 90 arcsec:", len(d), "| within 3 arcsec:", near, "| faintest J within 90:", max([float(x[1]) for x in d if x[1].strip()] or [0]))
