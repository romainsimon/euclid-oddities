"""Track M selection: rules A to E of PREREG_M.md applied to the per-tile measurements of tm.py. No model, no network.
Usage: ms.py dev | ms.py all
"all" refuses to run unless ~/trackm/FROZEN exists (written after the rules are public). "dev" reads only the development box."""
import glob
import json
import os
import sys

import numpy as np
import pandas as pd

H = os.path.expanduser("~/trackm")
DEV = dict(ra=(50.0, 60.0), dec=(-50.0, -40.0))
PM_MIN, SNR_MIN, SEP_MAX, SEP2_MIN = 30.0, 5.0, 2.5, 2.0      # rule A
VIS_LO, VIS_HI, VR_LO, VR_HI = 20.0, 24.0, -1.2, 0.6          # rule A
RZ_MAX, LINE, SLOPE, RZ_FLOOR = 0.9, 17.0, 3.5, -0.5          # rule B
LINES = (15.5, 17.0, 17.5)                                    # rule B, counts reported for each
J_SNR, FLOOR_MAG, H_FLOOR = 8.0, 0.08, 2.0                    # rule C
GAIA_SD_MAX, TIE_MIN, GAIA_N_MIN = 2.0, 100, 20               # rule E
BINS = [(20.0, 20.5), (20.5, 21.5), (21.5, 22.5), (22.5, 23.5), (23.5, 24.0)]


def prep(D):
    D = D.copy()
    D["ls_ref_cat"] = D.ls_ref_cat.fillna("").astype(str)
    for b in "grz":
        f = D["ls_flux_" + b]
        D[b] = 22.5 - 2.5 * np.log10(f.where(f > 0))
    D["e_ls"] = np.hypot(1 / np.sqrt(D.ls_ra_ivar.clip(lower=1e-30)), 1 / np.sqrt(D.ls_dec_ivar.clip(lower=1e-30))) * 3600 * 1000 / np.sqrt(2)
    D["e_pm"] = np.hypot(np.hypot(D.e_ls, D.tie_err * 1000), 8.0) / D.base_yr
    D["snr"] = D.pm / D.e_pm
    D["Hr"] = D.r + 5 * np.log10(D.pm / 1000) + 5
    D["rz"], D["gr"], D["vis_r"] = D.r - D.z, D.g - D.r, D.vis - D.r
    return D


def common(D):
    return D[D.matched & (D.ls_ref_cat == "") & D.gaia_id.isna() & (D.vis > VIS_LO) & (D.vis < VIS_HI) & (D.ls_maskbits == 0) & (D.det_quality_flag == 0)
             & (D.vis_r > VR_LO) & (D.vis_r < VR_HI) & np.isfinite(D.r) & np.isfinite(D.z)]


def movers(D):
    return D[(D.snr > SNR_MIN) & (D.pm > PM_MIN) & (D.sep2 > SEP2_MIN) & (D.sep < SEP_MAX)]


def box(D, line=LINE):
    return D[(D.rz < RZ_MAX) & (D.Hr > line + SLOPE * D.rz.clip(lower=RZ_FLOOR))]


def hist(v):
    return np.array([int(((v >= a) & (v < b)).sum()) for a, b in BINS])


def bb(T):
    f = lambda lam: (14388 / (lam * T)) ** 3 / np.expm1(14388 / (lam * T))
    m = lambda a, b: -2.5 * np.log10(f(a) / f(b))
    return m(0.475, 0.635), m(1.08, 1.37), m(1.37, 1.77)


def main():
    mode = sys.argv[1]
    if mode == "all" and not os.path.exists(H + "/FROZEN"):
        sys.exit("refused: ~/trackm/FROZEN is missing (the rules must be public first)")
    J = [json.load(open(f)) for f in sorted(glob.glob(H + "/tiles/*.json"))]
    J = [j for j in J if j.get("status") == "ok"]
    if mode == "dev":
        J = [j for j in J if DEV["ra"][0] <= j["ra"] < DEV["ra"][1] and DEV["dec"][0] <= j["dec"] < DEV["dec"][1]]
    out = f"{H}/sel_{mode}"
    os.makedirs(out, exist_ok=True)
    # rule E
    keep, dropped, unchecked = [], [], []
    for j in J:
        g = j.get("gaia_check") or {}
        if j.get("n_tie", 0) < TIE_MIN:
            dropped.append((j["tile"], j["ra"], j["dec"], f"tie on {j.get('n_tie', 0)} galaxies"))
        elif g.get("n", 0) >= GAIA_N_MIN and max(g["sd_x"], g["sd_y"]) > GAIA_SD_MAX:
            dropped.append((j["tile"], j["ra"], j["dec"], f"Gaia scatter {max(g['sd_x'], g['sd_y']):.2f} mas/yr"))
        else:
            keep.append(j)
            if g.get("n", 0) < GAIA_N_MIN:
                unchecked.append(j["tile"])
    pd.DataFrame(dropped, columns=["tile", "ra", "dec", "reason"]).to_csv(out + "/tiles_dropped.csv", index=False)
    sd = np.array([[j["gaia_check"]["sd_x"], j["gaia_check"]["sd_y"]] for j in keep if (j.get("gaia_check") or {}).get("n", 0) >= GAIA_N_MIN])
    print(f"tiles measured: {len(J)}; dropped by rule E: {len(dropped)}; kept: {len(keep)} (about {0.25 * len(keep):.0f} deg2 before overlaps), {len(unchecked)} of them with fewer than {GAIA_N_MIN} Gaia stars for the check")
    if len(sd):
        print(f"Gaia check over kept tiles: median per-star scatter {np.median(sd[:, 0]):.2f} / {np.median(sd[:, 1]):.2f} mas/yr, worst {sd.max():.2f}")
    seen_p, seen_g = set(), set()
    n_pt, n_gal, MV, GM = np.zeros(len(BINS), int), np.zeros(len(BINS), int), [], []
    for i, j in enumerate(keep):
        t = j["tile"]
        P = pd.read_csv(f"{H}/tiles/{t}.csv.gz")
        P = prep(P[~P.object_id.isin(seen_p)].drop_duplicates("object_id"))      # an object seen in two tiles is kept from the lower tile index
        seen_p.update(P.object_id)
        pt = common(P[(P.point_like_prob > 0.9) & (P.ls_type == "PSF")])
        n_pt += hist(pt.vis)
        MV.append(movers(pt))
        G = pd.read_csv(f"{H}/tiles/{t}_gal.csv.gz")
        if len(G):
            G = prep(G[~G.object_id.isin(seen_g)].drop_duplicates("object_id"))
            seen_g.update(G.object_id)
            GM.append(movers(common(G)))
        for k, (a, b) in enumerate(BINS):       # galaxy counts per bin: bins of the tile summary (20.5 to 24), all matched extended sources
            n_gal[k] += j["control"].get(f"{a}-{b}", {}).get("n", 0)
        if i % 500 == 0:
            print("  ", i, len(keep), flush=True)
    mv = pd.concat(MV, ignore_index=True)
    gm = pd.concat(GM, ignore_index=True) if GM else mv.iloc[:0]
    wd, gb = box(mv), box(gm)
    print(f"A. clean non-Gaia point sources VIS 20-24: {int(n_pt.sum())}; movers: {len(mv)}")
    print("B. white dwarf candidates:", {ln: len(box(mv, ln)) for ln in LINES}, f"(rule line {LINE}: {len(wd) / (0.25 * len(keep)):.2f} per deg2)")
    print("D. control with extended sources (same cuts):")
    em = eb = 0.0
    for k, (a, b) in enumerate(BINS):
        fm, fb = int(((gm.vis >= a) & (gm.vis < b)).sum()), int(((gb.vis >= a) & (gb.vis < b)).sum())
        om, ob = int(((mv.vis >= a) & (mv.vis < b)).sum()), int(((wd.vis >= a) & (wd.vis < b)).sum())
        if n_gal[k]:
            em += fm / n_gal[k] * n_pt[k]
            eb += fb / n_gal[k] * n_pt[k]
            print(f"   VIS {a}-{b}: extended {n_gal[k]}, false movers {fm}, in the box {fb} | point sources {n_pt[k]}: movers {om} (false expected <= {fm / n_gal[k] * n_pt[k]:.1f}), "
                  f"box {ob} (false expected <= {fb / n_gal[k] * n_pt[k]:.1f})")
        else:
            print(f"   VIS {a}-{b}: no extended-source count stored for this bin | point sources {n_pt[k]}: movers {om}, box {ob}")
    print(f"   expected false movers: {em:.1f} of {len(mv)}; in the box: {eb:.1f} of {len(wd)}")
    print("   box by magnitude and motion:", pd.crosstab(pd.cut(wd.vis, [20, 21.5, 22.5, 23.5, 24]), pd.cut(wd.pm, [30, 40, 60, 100, 400])).to_string().replace("\n", " | "))
    mv.to_csv(out + "/movers.csv.gz", index=False)
    wd.to_csv(out + "/wd.csv.gz", index=False)
    # rule C, catalogue step
    T = np.arange(3000, 15000, 100)
    B = np.array([bb(t) for t in T])
    W = wd.copy()
    for b_ in "yjh":
        W[b_ + "_snr"] = W[f"flux_{b_}_2fwhm_aper"] / W[f"fluxerr_{b_}_2fwhm_aper"]
    W = W[(W.j_snr > J_SNR) & np.isfinite(W.gr)].copy()
    fj, fy = W.flux_j_2fwhm_aper, W.flux_y_2fwhm_aper
    fh = np.maximum(W.flux_h_2fwhm_aper, H_FLOOR * W.fluxerr_h_2fwhm_aper)      # H below 2 sigma: the 2 sigma value is used, J - H is then an upper limit
    W["h_limit"] = W.flux_h_2fwhm_aper < H_FLOOR * W.fluxerr_h_2fwhm_aper
    W["jh"] = -2.5 * np.log10(fj / fh)
    W["yj"] = -2.5 * np.log10(fy.where(fy > 0) / fj)
    W["T_bb"] = np.interp(W.gr, B[::-1, 0], T[::-1])
    W["bb_jh"] = np.interp(W.T_bb, T, B[:, 2])
    W["d_jh"] = W.jh - W.bb_jh
    W["d_yj"] = W.yj - np.interp(W.T_bb, T, B[:, 1])
    W["e_jh"] = 1.086 * np.hypot(1 / W.j_snr, 1 / W.h_snr.clip(lower=H_FLOOR))
    W["e_yj"] = 1.086 * np.hypot(1 / W.j_snr, 1 / W.y_snr.clip(lower=0.5))
    med_jh, med_yj = W.d_jh[~W.h_limit].median(), W.d_yj.median()               # median offset of the whole sample of this run
    sc = 1.4826 * (W.d_jh[~W.h_limit] - med_jh).abs().median()
    W["sig_jh"] = (W.d_jh - med_jh) / np.hypot(W.e_jh, FLOOR_MAG)
    W["sig_yj"] = (W.d_yj - med_yj) / np.hypot(W.e_yj, FLOOR_MAG)
    lo = (W.sig_jh < -3) | ((W.sig_jh < -2) & (W.sig_yj < -2))
    hi = ((W.sig_jh > 3) & ~W.h_limit) | ((W.sig_jh > 2) & (W.sig_yj > 2) & ~W.h_limit)
    print(f"C. box sources with J S/N > {J_SNR:.0f}: {len(W)}; J-H minus blackbody: median {med_jh:+.3f}, robust scatter {sc:.3f}; H below 2 sigma: {int(W.h_limit.sum())}")
    print(f"   near-infrared deficit (catalogue step): {int(lo.sum())}; noise tail, same rule with signs reversed: {int(hi.sum())}")
    irf = W[lo].sort_values("sig_jh")
    irf.to_csv(out + "/irfaint.csv", index=False)
    W[hi].to_csv(out + "/irexcess.csv", index=False)
    pd.set_option("display.width", 260)
    pd.set_option("display.max_rows", 60)
    c = ["object_id", "right_ascension", "declination", "tile", "r", "gr", "rz", "pm", "Hr", "yj", "jh", "sig_yj", "sig_jh", "j_snr", "h_snr", "h_limit"]
    print(irf[c].round(3).head(60).to_string())


main()
