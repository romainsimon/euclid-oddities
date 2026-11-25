"""Track M, second stage: pixel step for the sources that meet rule H except that their best model is not acceptable ("fits no model").
qn.py prep : writes ~/trackm/sel_m3/irfaint.csv (input of mp.py m3), in the order of fits_no_model.csv (best chi2 first)
qn.py pages: cuts sel_m3/irfaint.png into pages of 11 rows and prints the measurements"""
import os
import sys

import numpy as np
import pandas as pd
from PIL import Image

H = os.path.expanduser("~/trackm")
N = pd.read_csv(H + "/pub2/fits_no_model.csv")
if sys.argv[1] == "prep":
    os.makedirs(H + "/sel_m3", exist_ok=True)
    W = pd.read_csv(H + "/sel_all/wd.csv.gz").drop_duplicates("object_id")
    I = pd.read_csv(H + "/sel_all/irfaint.csv")
    X = W[W.object_id.isin(N.object_id)].merge(N[["object_id", "teff_best", "comp_best", "dchi2", "chi2_best"]], on="object_id").sort_values("chi2_best").reset_index(drop=True)
    for col in I.columns:
        if col not in X.columns:
            X[col] = np.nan
    X["bb_jh"], X["sig_jh"] = 0.0, np.arange(len(X), dtype=float)
    X[list(I.columns) + ["teff_best", "comp_best", "dchi2", "chi2_best"]].to_csv(H + "/sel_m3/irfaint.csv", index=False)
    print(len(X), "rows")
else:
    im = Image.open(H + "/sel_m3/irfaint.png")
    os.makedirs(H + "/sel_m3/pages", exist_ok=True)
    for k in range(0, len(N), 11):
        im.crop((0, k * 218, im.size[0], min((k + 11) * 218, im.size[1]))).save(f"{H}/sel_m3/pages/n{k // 11:02d}.png")
    P = pd.read_csv(H + "/sel_m3/irfaint_pix.csv")
    X = pd.read_csv(H + "/sel_m3/irfaint.csv")
    assert (P.object_id.values == X.object_id.values).all()
    T = P.merge(N, on="object_id", suffixes=("", "_n"))
    pd.set_option("display.width", 330)
    pd.set_option("display.max_rows", 100)
    print(T[["object_id", "r", "pm", "comp_best", "teff_best", "chi2_best", "dchi2", "nir_sig", "nir_mag", "VIS_snr", "NIR_Y_snr", "NIR_J_snr", "NIR_H_snr", "NIR_Y_bad", "NIR_J_bad", "NIR_H_bad", "z_g", "z_r", "z_i", "z_z", "z_y", "z_j", "z_h"]].round(2).to_string())
