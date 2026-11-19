"""Radio-bright, Euclid-dark sources: eye-check removals, literature columns and the public table (no model call).

  final    dark_all.csv -> final.csv: removed sources marked, SIMBAD / NED / pulsar / VLASS columns added.

All added columns are descriptive (PREREG_R.md rule 8). REMOVED is the list of sources taken out after the eye check
of the image sheets by Claude Fable 5.2 on 19 Nov 2026, each with its reason (PREREG_R.md, "What a person or a model may still do").
"""
from __future__ import annotations

import io

import numpy as np
import pandas as pd
import requests

import rd

HOME = rd.HOME
SIMBAD = "https://simbad.cfa.harvard.edu/simbad/sim-tap/sync"
NED = "https://ned.ipac.caltech.edu/tap/sync"
VIZIER = ("https://tapvizier.cds.unistra.fr/TAPVizieR/tap/sync", "http://tapvizier.cds.unistra.fr/TAPVizieR/tap/sync",
          "https://vizier.cfa.harvard.edu/TAPVizieR/tap/sync")
R_LIT = 15.0      # arcsec, SIMBAD and NED cone around the RACS-mid position (covers NVSS / SUMSS position errors)
R_PSR = 30.0      # arcsec, pulsar cone
R_VLASS = 5.0     # arcsec
REMOVED = {
    "RACS-MID1 J010708.0-580626": "VIS: patch of low-coverage noise with a masked hole covers the position",
    "RACS-MID1 J043500.4-243104": "H: edge of the mosaic about 3 arcsec from the position, noisy data",
}
SURVEYS = ("NVSS", "SUMSS", "GLEAM", "WISEA", "WISE", "2MASS", "GALEX", "TGSS", "MRC", "PMN", "MWACS", "VLSS", "RACS", "AT20G", "ATPMN")


def tap(urls, q, timeout=90):
    for u in ([urls] if isinstance(urls, str) else urls):
        try:
            r = requests.post(u, data=dict(REQUEST="doQuery", LANG="ADQL", FORMAT="csv", QUERY=q), timeout=timeout)
            if r.status_code == 200 and not r.text.lstrip().startswith("<"):
                return pd.read_csv(io.StringIO(r.text))
        except Exception:
            pass
    return None


def final():
    C = pd.read_csv(HOME / "dark_all.csv", dtype={"sid": str})
    rows = []
    viz_ok = tap(VIZIER, 'SELECT TOP 1 PSRJ FROM "B/psr/psr"', timeout=30) is not None
    print("VizieR reachable:", viz_ok, flush=True)
    viz_fail = 0
    for p in C.itertuples():
        ra, dec = p.ra_mid, p.dec_mid
        rec = dict(sid=p.sid)
        s = tap(SIMBAD, "SELECT main_id, otype, nbref, rvz_redshift FROM basic WHERE "
                        f"1=CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS', {ra:.6f}, {dec:.6f}, {R_LIT / 3600:.6f}))")
        if s is None:
            rec["simbad"] = "query failed"
        else:
            rec["simbad"] = "; ".join(f"{a} ({b}, {int(n)} refs)" for a, b, n in zip(s.main_id, s.otype, s.nbref.fillna(0)))
            rec["simbad_refs"] = int(s.nbref.fillna(0).max()) if len(s) else 0
            rec["simbad_z"] = float(s.rvz_redshift.max()) if len(s) and s.rvz_redshift.notna().any() else np.nan
        n = tap(NED, "SELECT prefname, prefphytype, z FROM objdir WHERE "
                     f"1=CONTAINS(POINT('J2000', ra, dec), CIRCLE('J2000', {ra:.6f}, {dec:.6f}, {R_LIT / 3600:.6f}))")
        if n is None:
            rec["ned"] = "query failed"
        else:
            rec["ned"] = "; ".join(f"{a} ({b})" if isinstance(b, str) else str(a) for a, b in zip(n.prefname, n.prefphytype))
            rec["ned_z"] = float(n.z.max()) if len(n) and n.z.notna().any() else np.nan
            rec["ned_other"] = "; ".join(str(a) for a in n.prefname if not str(a).startswith(SURVEYS))
        if viz_ok and viz_fail < 3:
            ps = tap(VIZIER, 'SELECT PSRJ FROM "B/psr/psr" WHERE '
                             f"1=CONTAINS(POINT('ICRS', RAJ2000, DEJ2000), CIRCLE('ICRS', {ra:.6f}, {dec:.6f}, {R_PSR / 3600:.6f}))", timeout=20)
            viz_fail = viz_fail + 1 if ps is None else 0
            rec["pulsar"] = "query failed" if ps is None else "; ".join(ps.PSRJ.astype(str))
            if dec > -40:
                v = tap(VIZIER, 'SELECT RAJ2000, DEJ2000, Ftot, Fpeak, DCMaj FROM "J/ApJS/255/30/comp" WHERE '
                                f"1=CONTAINS(POINT('ICRS', RAJ2000, DEJ2000), CIRCLE('ICRS', {ra:.6f}, {dec:.6f}, {R_VLASS / 3600:.6f}))", timeout=20)
                if v is None:
                    rec["vlass_n"] = -1
                else:
                    rec["vlass_n"] = len(v)
                    if len(v):
                        d = np.hypot((v.RAJ2000 - ra) * np.cos(np.radians(dec)), v.DEJ2000 - dec) * 3600
                        k = int(d.argmin())
                        rec.update(vlass_sep=float(d[k]), vlass_total=float(v.Ftot[k]), vlass_dcmaj=float(v.DCMaj[k]))
        rows.append(rec)
        if len(rows) % 10 == 0:
            print(len(rows), "of", len(C), flush=True)
    F = C.merge(pd.DataFrame(rows), on="sid")
    F["removed"] = F.name.map(REMOVED).fillna("")
    F.to_csv(HOME / "final_full.csv", index=False)
    keep = ["name", "ra", "dec", "cls", "dev", "removed", "peak", "total_mid", "total_low", "total_high", "alpha_low_mid", "alpha_mid_high",
            "high_sep", "tp_mid", "tp_high", "VIS_snr15", "NIR_H_snr15", "VIS_lim", "NIR_H_lim", "VIS_peak_snr", "NIR_H_peak_snr",
            "wise_n5", "wise_sep", "w1", "w2", "simbad", "simbad_refs", "simbad_z", "ned", "ned_z", "ned_other", "pulsar",
            "vlass_n", "vlass_sep", "vlass_total", "vlass_dcmaj", "tile", "sid"]
    P = F[[c for c in keep if c in F]].rename(columns=dict(ra="ra_corrected", dec="dec_corrected", peak="peak_mid_mJy_beam",
                                                           total_mid="total_mid_mJy", total_low="total_low_mJy", total_high="total_high_mJy"))
    P.round(5).to_csv(HOME / "track_r_candidates.csv", index=False)
    K = F[F.removed == ""]
    print(f"selected {len(F)}, removed after the eye check {int((F.removed != '').sum())}, kept {len(K)}: {K.cls.value_counts().to_dict()}")
    print("kept, development box:", int(K.dev.sum()), "| outside:", int((~K.dev).sum()))
    print("SIMBAD: with a redshift", int(K.simbad_z.notna().sum()), "| with more than 5 references", int((K.simbad_refs > 5).sum()),
          "| query failed", int((K.simbad == "query failed").sum()))
    print("NED: with a redshift", int(K.ned_z.notna().sum()), "| with a non-survey name", int((K.ned_other.fillna('') != '').sum()),
          "| query failed", int((K.ned == "query failed").sum()))
    if "pulsar" in K:
        print("pulsar within", R_PSR, "arcsec:", int((K.pulsar.fillna("") != "").sum()))
    if "vlass_n" in K:
        v = K[K.vlass_n.notna()]
        print("VLASS (Dec > -40):", len(v), "queried,", int((v.vlass_n > 0).sum()), "detected,", int((v.vlass_n == 0).sum()), "not detected")
    pd.set_option("display.width", 250)
    pd.set_option("display.max_colwidth", 120)
    pd.set_option("display.max_rows", 300)
    odd = K[(K.simbad_z.notna()) | (K.ned_z.notna()) | (K.simbad_refs > 5) | (K.ned_other.fillna("") != "")]
    print(odd[["name", "peak", "cls", "simbad", "ned_other", "ned_z"]].to_string())


if __name__ == "__main__":
    final()
