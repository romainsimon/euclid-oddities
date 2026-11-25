"""Track M, second stage: synthetic photometry of white dwarf model spectra in the bands of the data.
Spectra: Warwick grids (Tremblay et al. 2011 pure hydrogen with the Kowalski & Saumon 2006 Lyman alpha wing and H2 collision-induced absorption;
Cukanovaite et al. 2021 helium-rich, He/H = 1e2, 1e5, 1e8 and pure helium). Masses and radii: Montreal tables (Bedard et al. 2020).
Filter curves: SVO Filter Profile Service. Output: ~/trackm/models/synth.csv, absolute AB magnitudes at 10 pc on the model grid nodes.
Check printed: our Pan-STARRS magnitudes against the tables published with the grids."""
import io
import os
import re

import numpy as np
import pandas as pd
import requests

M = os.path.expanduser("~/trackm/models")
SVO = "http://svo2.cab.inta-csic.es/theory/fps/getdata.php"
FILT = dict(g="CTIO/DECam.g", r="CTIO/DECam.r", i="CTIO/DECam.i", z="CTIO/DECam.z", vis="Euclid/VIS.vis", y="Euclid/NISP.Y", j="Euclid/NISP.J", h="Euclid/NISP.H",
            ps_g="PAN-STARRS/PS1.g", ps_r="PAN-STARRS/PS1.r", ps_i="PAN-STARRS/PS1.i", ps_z="PAN-STARRS/PS1.z", ps_y="PAN-STARRS/PS1.y")
COMP = dict(H=("grid_IR/{g}_LyA_IR", "DA"), He=("models/{g}_300_ML125", "DB"), HeH8=("models/{g}_080_ML125", "DB"), HeH5=("models/{g}_050_ML125", "DB"), HeH2=("models/{g}_020_ML125", "DB"))
GS = ("700", "750", "800", "850", "900")
G_N, MSUN, PC = 6.6743e-8, 1.98841e33, 3.0857e18


def filt(fid):
    f = f"{M}/filt_{fid.replace('/', '_')}.txt"
    if not os.path.exists(f):
        r = requests.get(SVO, params=dict(format="ascii", id=fid), timeout=60)
        r.raise_for_status()
        open(f, "w").write(r.text)
    a = np.loadtxt(f)
    return a[:, 0], a[:, 1]


def grid(path):
    t = open(path).read()
    head = list(re.finditer(r"Effective temperature =\s*([\d.]+)\s+gravity =\s*([\dE.+]+)\s+y =\s*([\dE.+]+)", t))
    n = int(t.split(None, 1)[0])
    w = np.array(t[:head[0].start()].split()[1:], float)
    assert len(w) == n
    out = []
    for k, m in enumerate(head):
        body = t[m.end():(head[k + 1].start() if k + 1 < len(head) else len(t))]
        f = np.array([float(x) for x in re.findall(r"[-+]?\d\.\d+E[-+]\d+", body)])
        assert len(f) == n, (path, m.group(1), len(f))
        out.append((float(m.group(1)), np.log10(float(m.group(2))), f))
    return w, out


def montreal(name):
    """Teff, log g, mass of the Montreal table (several log g blocks)."""
    rows = []
    for ln in open(f"{M}/{name}"):
        p = ln.split()
        if len(p) > 20 and re.fullmatch(r"[\d.]+", p[0]):
            rows.append((float(p[0]), float(p[1]), float(p[2])))
    return pd.DataFrame(rows, columns=["teff", "logg", "mass"])


def mass_at(tab, teff, logg):
    """Mass at (teff, logg): linear in log g between the table blocks, linear in Teff inside a block."""
    gs = np.sort(tab.logg.round(1).unique())
    m = []
    for g in gs:
        b = tab[tab.logg.round(1) == g].sort_values("teff")
        m.append(np.interp(teff, b.teff, b.mass))
    return float(np.interp(logg, gs, m))


F = {b: filt(i) for b, i in FILT.items()}
MT = {k: montreal("Table_" + k) for k in ("DA", "DB")}
rows = []
for comp, (pat, mt) in COMP.items():
    for g in GS:
        w, models = grid(f"{M}/{pat.format(g=g)}")
        nu = 2.99792458e18 / w
        for teff, logg, hnu in models:
            if teff > 20000:
                continue
            mass = mass_at(MT[mt], max(teff, MT[mt].teff.min()), logg)
            rad = np.sqrt(G_N * mass * MSUN / 10 ** logg)
            fnu = 4 * np.pi * hnu * (rad / (10 * PC)) ** 2                    # erg cm-2 s-1 Hz-1 at 10 pc
            row = dict(comp=comp, teff=teff, logg=round(logg, 2), mass=round(mass, 4), radius_cm=rad)
            for b, (fw, ft) in F.items():
                T = np.interp(w, fw, ft, left=0, right=0)
                k = T > 0
                num = np.trapezoid((fnu * T / nu)[k][::-1], nu[k][::-1])       # photon-counting mean flux density
                den = np.trapezoid((T / nu)[k][::-1], nu[k][::-1])
                row[b] = -2.5 * np.log10(max(num / den, 1e-300) / 3.631e-20)
            rows.append(row)
S = pd.DataFrame(rows)
S.to_csv(M + "/synth.csv", index=False)
print(S.groupby("comp").agg(n=("teff", "size"), tmin=("teff", "min"), tmax=("teff", "max")).to_string())
# check against the Pan-STARRS table published with the pure-hydrogen grid
P = []
for ln in open(M + "/table_panstarrs_h.txt"):
    p = ln.split()
    if len(p) == 9 and re.fullmatch(r"[\d.]+", p[0]):
        P.append([float(x) for x in p])
P = pd.DataFrame(P, columns=["teff", "logg", "mass_t", "mbol", "t_g", "t_r", "t_i", "t_z", "t_y"])
C = S[S.comp == "H"].merge(P, on=["teff", "logg"])
print(f"check against table_panstarrs_h.txt: {len(C)} common models")
for lo, hi in ((1500, 3000), (3000, 5000), (5000, 20000)):
    c = C[(C.teff >= lo) & (C.teff < hi)]
    print(f"   Teff {lo}-{hi}: mass ours/table {np.median(c.mass / c.mass_t):.3f}; ours minus table, median (max abs): "
          + ", ".join(f"{b} {np.median(c['ps_' + b] - c['t_' + b]):+.3f} ({np.abs(c['ps_' + b] - c['t_' + b]).max():.3f})" for b in "grizy"))
c = S[(S.logg == 8.0) & S.teff.isin([3000, 3500, 4000, 4500, 5000, 6000, 8000, 12000])]
c = c.assign(gr=c.g - c.r, rz=c.r - c.z, vis_r=c.vis - c.r, zy=c.z - c.y, yj=c.y - c.j, jh=c.j - c.h)
print(c[["comp", "teff", "mass", "r", "gr", "rz", "vis_r", "zy", "yj", "jh"]].round(3).to_string())
