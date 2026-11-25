"""Track M, second stage: model-atmosphere fit of the photometry (rules G to K of PREREG_M2.md). No language model.
qf.py cal          calibration and validation on Gaia white dwarfs (development; they are never candidates). Writes m2/cal.json.
qf.py run          the 9,407 white dwarf candidates. Refuses unless ~/trackm/FROZEN2 exists.
qf.py sim          noise-only expectation: synthetic sources drawn from the best weak-absorption model of each candidate, same errors, same cuts.
Bands: Legacy Surveys DR10 g, r, i, z (Tractor) and Euclid Y, J, H. VIS is not fitted (kept as a check).
Models: synth.csv of qm.py (pure H, pure He, He/H = 1e2, 1e5, 1e8), at 0.6 solar masses; distances also at 0.9 solar masses."""
import json
import os
import sys

import warnings

import numpy as np
import pandas as pd
from scipy.stats import chi2 as chi2dist

warnings.filterwarnings("ignore")
H = os.path.expanduser("~/trackm")
BANDS = ["g", "r", "i", "z", "y", "j", "h"]
OPT, NIR = ["g", "r", "i", "z"], ["y", "j", "h"]
COMPS = ["H", "He", "HeH8", "HeH5", "HeH2"]
T_MIN, T_MAX, T_STEP = 2500.0, 20000.0, 25.0
MASS, MASS_CONS = 0.6, 0.9
K_EXT = dict(y=0.88, j=0.60, h=0.41, vis=1.9)        # A / E(B-V) of SFD for the Euclid bands (power law -1.6 from the 2MASS values of Schlafly & Finkbeiner 2011); g, r, i, z use the Legacy Surveys transmissions
SYS_OPT = 0.03                                       # mag, per optical band, in quadrature
CIA_WEAK, CIA_STRONG = -0.40, -0.50                  # model J - H minus pure-helium J - H at the same temperature. Above -0.40: "ordinary" (includes pure hydrogen down to about 4000 K)
D_CHI2, P_MIN, D_ULTRA, T_ULTRA = 16.0, 1e-3, 9.0, 4000.0
SNR_J, FRAC_MAX = 5.0, 0.1
V_HALO, V_UNBOUND = 200.0, 500.0
NIR_KIND = "templfit"                                # overwritten by cal.json


def tracks():
    """Model fluxes (microJy at 10 pc) on a fine temperature grid, per composition and mass; and the absorption index of each model."""
    S = pd.read_csv(H + "/models/synth.csv")
    T = np.arange(T_MIN, T_MAX + 1, T_STEP)
    out = {}
    for c in COMPS:
        for mass in (MASS, MASS_CONS):
            rows = []
            for t, g in S[S.comp == c].groupby("teff"):
                g = g.sort_values("mass")
                rows.append([t] + [np.interp(mass, g.mass, g[b]) for b in BANDS + ["vis"]])
            A = np.array(rows)
            ok = (T >= A[:, 0].min()) & (T <= A[:, 0].max())
            mags = np.full((len(T), len(BANDS) + 1), np.nan)
            for k in range(len(BANDS) + 1):
                mags[ok, k] = np.interp(T[ok], A[:, 0], A[:, k + 1])
            out[c, mass] = 3631e6 * 10 ** (-0.4 * mags)
    jh = lambda F: -2.5 * np.log10(F[:, 5] / F[:, 6])
    he = jh(out["He", MASS])
    he = np.where(np.isfinite(he), he, he[np.isfinite(he)][0])       # below the coolest pure-helium model: its coolest value
    cia = {c: jh(out[c, MASS]) - he for c in COMPS}
    return T, out, cia


def load(tag, cal):
    """Fluxes in microJy, corrected for extinction and for the near-infrared zero points of cal.json."""
    base = pd.read_csv(H + ("/sel_all/wd.csv.gz" if tag == "wd" else "/m2/gcal.csv"), low_memory=False)
    L = pd.read_csv(f"{H}/m2/{tag}_ls.csv")
    E = pd.read_csv(f"{H}/m2/{tag}_eu.csv").drop_duplicates("object_id")
    if "e_pm" not in base.columns:
        base["e_pm"] = 0.0
    keep = ["object_id", "right_ascension", "declination", "tile", "vis", "pm", "pmx", "pmy", "e_pm", "base_yr"] + [c for c in ("TeffH", "e_TeffH", "loggH", "MassH", "TeffHe", "Plx", "e_Plx", "pmRA", "pmDE", "Gmag", "Pwd", "GaiaEDR3", "Hr", "gr", "rz") if c in base.columns]
    D = base[keep].merge(L[L.status == "ok"].drop(columns=["status", "ra", "dec"]), on="object_id").merge(E, on="object_id", suffixes=("", "_eu"))
    for b in OPT:
        tr = D[f"mw_transmission_{b}"].clip(lower=0.3)
        ok = (D[f"nobs_{b}"] > 0) & (D[f"flux_ivar_{b}"] > 0)
        D["f_" + b] = np.where(ok, 3.631 * D[f"flux_{b}"] / tr, np.nan)
        D["e_" + b] = np.where(ok, 3.631 / np.sqrt(D[f"flux_ivar_{b}"].where(ok, 1)) / tr, np.nan)
    kind = cal.get("nir_kind", NIR_KIND)
    for b in NIR:
        col = f"{b}_templfit" if kind == "templfit" else f"{b}_2fwhm_aper"
        k = 10 ** (0.4 * (K_EXT[b] * D.ebv + cal.get("zp", {}).get(b, 0.0)))        # zp = observed minus model magnitude of the warm calibrators; removed from the data
        ok = (D[f"fluxerr_{col}"] > 0) & np.isfinite(D[f"flux_{col}"])
        D["f_" + b] = np.where(ok, D[f"flux_{col}"] * k, np.nan)
        D["e_" + b] = np.where(ok, D[f"fluxerr_{col}"] * k, np.nan)
    D["f_vis"] = D.flux_vis_psf * 10 ** (0.4 * K_EXT["vis"] * D.ebv)
    return D


def fit(D, T, TR, cia, sys_mag, bands=BANDS):
    """Chi2 on the temperature grid for every composition; amplitude solved analytically. Returns a dict of arrays."""
    idx = [BANDS.index(b) for b in bands]
    f = D[["f_" + b for b in bands]].values.astype(float)
    e = D[["e_" + b for b in bands]].values.astype(float)
    s = np.array([sys_mag[b] for b in bands]) * 0.921
    ok = np.isfinite(f) & np.isfinite(e)
    var = np.where(ok, e ** 2 + (s * np.clip(np.nan_to_num(f), 0, None)) ** 2, 1.0)
    w = ok / var
    f0 = np.nan_to_num(f)
    R = dict(n=ok.sum(1))
    sff = (w * f0 ** 2).sum(1)
    C2, AMP = {}, {}
    for c in COMPS:
        m = TR[c, MASS][:, idx]                               # T x B
        good = np.isfinite(m).all(1)
        m = np.nan_to_num(m)
        sfm = (w * f0) @ m.T                                  # N x T
        smm = w @ (m ** 2).T
        a = np.clip(sfm / np.where(smm > 0, smm, 1), 1e-30, None)
        c2 = sff[:, None] - 2 * a * sfm + a ** 2 * smm
        c2[:, ~good] = np.inf
        C2[c], AMP[c] = c2, a
        k = np.argmin(c2, 1)
        r = np.arange(len(D))
        R[f"chi2_{c}"], R[f"teff_{c}"], R[f"d_{c}"] = c2[r, k], T[k], 10 / np.sqrt(a[r, k])
        inside = c2 <= c2[r, k][:, None] + 1
        R[f"tlo_{c}"] = np.where(inside, T[None, :], np.inf).min(1)
        R[f"thi_{c}"] = np.where(inside, T[None, :], -np.inf).max(1)
        mc = np.nan_to_num(TR[c, MASS_CONS][:, idx])          # distance at the conservative mass, same temperature
        R[f"dcons_{c}"] = R[f"d_{c}"] * np.sqrt((mc[k] ** 2 * w).sum(1) / np.clip((m[k] ** 2 * w).sum(1), 1e-300, None))
    allc = np.stack([C2[c] for c in COMPS], 1)                # N x C x T
    ciaa = np.stack([cia[c] for c in COMPS], 0)               # C x T
    best = allc.reshape(len(D), -1).argmin(1)
    R["chi2_best"] = allc.reshape(len(D), -1).min(1)
    R["comp_best"] = np.array(COMPS)[best // len(T)]
    R["teff_best"] = T[best % len(T)]
    R["cia_best"] = ciaa.reshape(-1)[best]
    weak = np.where((ciaa > CIA_WEAK)[None], allc, np.inf).reshape(len(D), -1)
    kw = weak.argmin(1)
    R["chi2_weak"], R["comp_weak"], R["teff_weak"] = weak.min(1), np.array(COMPS)[kw // len(T)], T[kw % len(T)]
    near = allc <= (R["chi2_best"] + D_ULTRA)[:, None, None]
    R["tmax_near"] = np.where(near, T[None, None, :], -np.inf).max((1, 2))
    R["ciamax_near"] = np.where(near, ciaa[None], -np.inf).max((1, 2))
    aw = np.stack([AMP[c] for c in COMPS], 1).reshape(len(D), -1)[np.arange(len(D)), kw]
    mw = np.stack([np.nan_to_num(TR[c, MASS]) for c in COMPS], 0).reshape(-1, len(BANDS) + 1)[kw]
    for j, b in enumerate(bands):                             # residuals against the best weak-absorption model, in sigma
        R["z_" + b] = np.where(ok[:, j], (f0[:, j] - aw * mw[:, BANDS.index(b)]) / np.sqrt(var[:, j]), np.nan)
    R["vis_pred"] = aw * mw[:, len(BANDS)]
    R["p_best"] = chi2dist.sf(R["chi2_best"], np.clip(R["n"] - 2, 1, None))
    return pd.DataFrame(R, index=D.index)


def quality(D):
    """Rule G: the sources that may be classified."""
    q = (D[["nobs_g", "nobs_r", "nobs_z"]] > 0).all(1) & (D[["fracflux_g", "fracflux_r", "fracflux_z"]].abs() < FRAC_MAX).all(1) & (D.maskbits == 0)
    q &= (D.f_j / D.e_j > SNR_J) & np.isfinite(D.f_y) & np.isfinite(D.f_h) & (D.flag_y == 0) & (D.flag_j == 0) & (D.flag_h == 0)
    return q


def classify(D, F):
    """Rules H to J."""
    q = quality(D)
    t1 = q & (F.chi2_weak - F.chi2_best >= D_CHI2) & (F.cia_best < CIA_STRONG) & (F.p_best > P_MIN)
    ultra = t1 & (F.tmax_near < T_ULTRA)
    d_best = np.where(F.chi2_H <= F.chi2_He, F.d_H, F.d_He)
    d_cons = np.minimum(F.dcons_H, F.dcons_He)
    v_best = 4.74047e-3 * D.pm * d_best
    v_cons = 4.74047e-3 * (D.pm - D.e_pm).clip(lower=0) * d_cons
    return pd.DataFrame(dict(quality=q, strong_cia=t1, ultracool=ultra, d_pc=d_best, d_cons_pc=d_cons, vtan=v_best, vtan_cons=v_cons, halo=v_cons > V_HALO, unbound=v_cons > V_UNBOUND), index=D.index)


def both(tag, C, T, TR, cia):
    """Fit and classify with the primary near-infrared fluxes; strong absorption and ultracool must also hold with the other flux type."""
    D = load(tag, C)
    F = fit(D, T, TR, cia, C["sys"])
    K = classify(D, F)
    other = [k for k in C["kinds"] if k != C["nir_kind"]][0]
    D2 = load(tag, dict(nir_kind=other, zp=C["kinds"][other]["zp"]))
    K2 = classify(D2, fit(D2, T, TR, cia, C["kinds"][other]["sys"]))
    assert (D2.object_id.values == D.object_id.values).all()
    K["strong_cia_primary"], K["strong_cia_other"] = K.strong_cia, K2.strong_cia.values
    K["strong_cia"] = K.strong_cia & K2.strong_cia.values
    K["ultracool"] = K.ultracool & K2.ultracool.values
    return D, F, K


def cal():
    T, TR, cia = tracks()
    rep = {}
    for kind in ("templfit", "2fwhm_aper"):
        D = load("gcal", dict(nir_kind=kind))
        D = D[(D[["fracflux_g", "fracflux_r", "fracflux_z"]].abs() < FRAC_MAX).all(1) & (D.maskbits == 0)].reset_index(drop=True)
        sys0 = dict(g=SYS_OPT, r=SYS_OPT, i=SYS_OPT, z=SYS_OPT, y=0.05, j=0.05, h=0.05)
        Fo = fit(D, T, TR, cia, sys0, bands=OPT)             # optical only, pure hydrogen prediction of the near-infrared
        k = ((T[None, :] - Fo.teff_H.values[:, None]) == 0).argmax(1)
        a = (10 / Fo.d_H.values) ** 2
        res = {}
        for b in NIR + ["vis"] + OPT:
            j = BANDS.index(b) if b != "vis" else len(BANDS)
            res[b] = -2.5 * np.log10((D["f_" + b] / (a * TR["H", MASS][k, j])).where(D["f_" + b] > 0))
        Rz = pd.DataFrame(res)
        warm = (D.TeffH > 7500) & (D.TeffH < 14000) & (Fo.teff_H > 7000) & (Fo.teff_H < 15000) & np.isfinite(D.f_j) & (D.f_j / D.e_j > 10)
        mad = lambda v: float(1.4826 * (v - v.median()).abs().median())
        print(f"== near-infrared fluxes: {kind}; Gaia white dwarfs {len(D)}, warm calibrators {int(warm.sum())}")
        rep[kind] = {}
        for b in NIR + ["vis"] + OPT:
            v = Rz[b][warm].dropna()
            snr = (D["f_" + b] / D["e_" + b])[warm] if b != "vis" else None
            ephot = float(np.median(1.086 / snr.dropna())) if snr is not None else 0.0
            rep[kind][b] = dict(zp=round(float(v.median()), 4), scatter=round(mad(v), 4), phot=round(ephot, 4), n=int(len(v)))
            print(f"   {b}: observed minus model {v.median():+.3f}, robust scatter {mad(v):.3f} (median photometric error {ephot:.3f}), n {len(v)}")
        for lo, hi in ((7500, 9000), (9000, 11000), (11000, 14000)):
            m = warm & (D.TeffH >= lo) & (D.TeffH < hi)
            print(f"      Teff {lo}-{hi}: " + ", ".join(f"{b} {Rz[b][m].median():+.3f}" for b in NIR))
        for lo, hi in ((18.5, 19.5), (19.5, 20.2), (20.2, 21.5)):
            m = warm & (D.vis >= lo) & (D.vis < hi)
            print(f"      VIS {lo}-{hi}: " + ", ".join(f"{b} {Rz[b][m].median():+.3f}" for b in NIR))
    tot = {k: float(np.sqrt(sum(max(rep[k][b]["scatter"] ** 2 - rep[k][b]["phot"] ** 2, 0) for b in NIR))) for k in rep}
    kind = min(tot, key=tot.get)
    kinds = {}
    for k_ in rep:
        sm = {b: SYS_OPT for b in OPT}
        for b in NIR:
            sm[b] = round(float(max(np.sqrt(max(rep[k_][b]["scatter"] ** 2 - rep[k_][b]["phot"] ** 2, 0)), 0.05)), 3)
        kinds[k_] = dict(zp={b: rep[k_][b]["zp"] for b in NIR}, sys=sm)
    sysm = kinds[kind]["sys"]
    C = dict(nir_kind=kind, zp=kinds[kind]["zp"], sys=sysm, kinds=kinds, report=rep)
    json.dump(C, open(H + "/m2/cal.json", "w"), indent=1)
    print("chosen:", kind, "zero points", C["zp"], "systematics", sysm)
    # validation: full fit of all Gaia white dwarfs of the sample with the calibration applied
    D, F, K = both("gcal", C, T, TR, cia)
    D = pd.concat([D, F, K], axis=1)
    D.to_csv(H + "/m2/gcal_fit.csv", index=False)
    V = D[D.quality & (D.Plx > 3) & (D.Gmag < 20)].copy()      # parallax error not fetched: bright and near enough for a parallax better than about 20 %
    V["t_fit"] = np.where(V.chi2_H <= V.chi2_He, V.teff_H, V.teff_He)
    V["dr"] = V.d_pc / (1000 / V.Plx)
    print(f"== validation on {len(V)} Gaia white dwarfs with quality cuts and parallax better than 20 %")
    for lo, hi in ((3000, 5000), (5000, 6000), (6000, 7000), (7000, 10000), (10000, 20000)):
        m = (V.TeffH >= lo) & (V.TeffH < hi)
        if m.sum() < 3:
            continue
        v = V[m]
        lr = np.log(v.dr)
        mdn = np.where(v.chi2_H <= v.chi2_He, v.chi2_H, v.chi2_He) / (v.n - 2)
        print(f"   catalogue Teff {lo}-{hi}: n {m.sum()}; our Teff / catalogue: median {np.median(v.t_fit / v.TeffH):.3f}, scatter {1.4826 * np.median(np.abs(v.t_fit / v.TeffH - np.median(v.t_fit / v.TeffH))):.3f}; "
              f"photometric / parallax distance: median {np.exp(np.median(lr)):.2f}, 16-84 % {np.exp(np.percentile(lr, 16)):.2f}-{np.exp(np.percentile(lr, 84)):.2f}; "
              f"conservative distance below the parallax distance for {np.mean(v.d_cons_pc < 1000 / v.Plx):.2f}; reduced chi2 median {np.median(mdn):.2f}; strong absorption {int(v.strong_cia.sum())}")
    vt = 4.74047 * np.hypot(V.pmRA, V.pmDE) / V.Plx
    print(f"   true tangential velocity above {V_HALO:.0f} km/s: {int((vt > V_HALO).sum())}; flagged halo by the rule: {int(V.halo.sum())}; flagged but true velocity below: {int((V.halo & (vt < V_HALO)).sum())}; true but not flagged: {int((~V.halo & (vt > V_HALO)).sum())}")
    A = D[D.quality]
    print(f"== all {len(A)} quality Gaia white dwarfs: strong absorption {int(A.strong_cia.sum())}, of which ultracool {int(A.ultracool.sum())}; p_best below {P_MIN}: {int((A.p_best < P_MIN).sum())}")
    pd.set_option("display.width", 250)
    c = ["GaiaEDR3", "right_ascension", "declination", "Gmag", "TeffH", "Plx", "comp_best", "teff_best", "chi2_best", "chi2_weak", "chi2_H", "chi2_He", "n", "cia_best", "tmax_near", "z_y", "z_j", "z_h"]
    print(A[A.strong_cia][c].round(3).to_string())
    print("H band residual against the weak-absorption fit, quality sample: below -3 sigma", int((A.z_h < -3).sum()), ", above +3 sigma", int((A.z_h > 3).sum()))


def run(sim=False):
    if not os.path.exists(H + "/FROZEN2"):
        sys.exit("refused: ~/trackm/FROZEN2 is missing (the rules of the second stage must be public first)")
    C = json.load(open(H + "/m2/cal.json"))
    T, TR, cia = tracks()
    D, F, K = both("wd", C, T, TR, cia)
    if sim:
        rng = np.random.default_rng(1)
        q = K.quality.values
        Dq, Fq = D[q].reset_index(drop=True), F[q].reset_index(drop=True)
        kT = ((T[None, :] - Fq.teff_weak.values[:, None]) == 0).argmax(1)
        tot = dict(strong_cia=0, ultracool=0)
        NS = 5
        for s in range(NS):
            S = Dq.copy()
            for j, b in enumerate(BANDS):
                amp =(S["f_" + b] - Fq["z_" + b] * np.sqrt(S["e_" + b] ** 2 + (C["sys"][b] * 0.921 * S["f_" + b].clip(lower=0)) ** 2))      # model flux of the weak fit in this band
                amp = amp.where(np.isfinite(amp), np.nan)
                sig = np.sqrt(S["e_" + b] ** 2 + (C["sys"][b] * 0.921 * amp.clip(lower=0)) ** 2)
                S["f_" + b] = amp + rng.normal(size=len(S)) * sig
            Ks = classify(S, fit(S, T, TR, cia, C["sys"]))
            for k in tot:
                tot[k] += int(Ks[k].sum())
            print(f"   simulation {s}: strong absorption {int(Ks.strong_cia.sum())}, ultracool {int(Ks.ultracool.sum())}", flush=True)
        print("(the simulation uses the primary fluxes only, so it is an upper bound for the rule that asks for both flux types)")
        print(f"noise-only expectation over {int(q.sum())} quality sources: strong absorption {tot['strong_cia'] / NS:.1f}, ultracool {tot['ultracool'] / NS:.1f}")
        return
    O = pd.concat([D, F, K], axis=1)
    os.makedirs(H + "/m2/out", exist_ok=True)
    O.to_csv(H + "/m2/out/fit_all.csv.gz", index=False)
    q = O[O.quality]
    print(f"candidates with photometry {len(O)} of 9407; quality (rule G) {len(q)}")
    print(f"strong absorption (rule H): {int(q.strong_cia.sum())} (primary fluxes alone {int(q.strong_cia_primary.sum())}, other fluxes alone {int(q.strong_cia_other.sum())}); of which ultracool (rule I): {int(q.ultracool.sum())}")
    print(f"H band residual against the weak-absorption fit: below -3 sigma {int((q.z_h < -3).sum())}, above +3 sigma {int((q.z_h > 3).sum())}")
    hal = O[O.halo]
    print(f"halo by the conservative velocity (rule J), all {len(O)}: {len(hal)}; above {V_UNBOUND:.0f} km/s: {int(O.unbound.sum())}; best-fit velocity above {V_HALO:.0f}: {int((O.vtan > V_HALO).sum())}")
    print(f"strong absorption and halo: {int((q.strong_cia & q.halo).sum())}")
    warm = q[(q.teff_best > 7000) & (q.teff_best < 15000)]
    print("warm candidates (7000-15000 K), median residual in sigma:", {b: round(float(warm['z_' + b].median()), 2) for b in BANDS}, "n", len(warm))
    q[q.strong_cia].sort_values("chi2_weak", ascending=False).to_csv(H + "/m2/out/strong_cia.csv", index=False)
    hal.to_csv(H + "/m2/out/halo.csv", index=False)


if __name__ == "__main__":
    {"cal": cal, "run": run, "sim": lambda: run(sim=True)}[sys.argv[1]]()
