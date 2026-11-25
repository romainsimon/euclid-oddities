"""Builds site/data/wd_faint.json and site/data/img/wd/ from the public tables of Track M, second stage
(track-m-moving-faint/stage2/). Run from the repository root: python site/mk_wd.py"""
import csv
import json
import re
import shutil
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
S2 = ROOT / "track-m-moving-faint" / "stage2"
OUT = ROOT / "site" / "data"
COMP = {"H": "pure hydrogen", "He": "pure helium", "HeH2": "helium with hydrogen (He/H = 100)", "HeH5": "helium with hydrogen (He/H = 100,000)", "HeH8": "helium with a trace of hydrogen (He/H = 1e8)"}


def sexa(ra, dec):
    t = round(ra / 15 * 36000)                     # tenths of a second of time, rounded (the convention of the first list)
    a = round(abs(dec) * 3600)
    return f"{t // 36000:02d}{t // 600 % 60:02d}{t % 600 / 10:04.1f}{'-' if dec < 0 else '+'}{a // 3600:02d}{a // 60 % 60:02d}{a % 60:02d}"


rows = list(csv.DictReader(open(S2 / "interesting_candidates.csv", encoding="utf-8")))
post = {r["object_id"]: r for r in csv.DictReader(open(S2 / "posthoc_m2.csv", encoding="utf-8"))}
old = {}
if (OUT / "wd_faint.json").exists():
    old = {c["object_id"]: c["slug"] for c in json.loads((OUT / "wd_faint.json").read_text(encoding="utf-8"))["candidates"]}
sheets = {}
img = OUT / "img" / "wd"
if img.exists():
    shutil.rmtree(img)
img.mkdir(parents=True)
C = []
for r in rows:
    if r["kept"] != "True":
        continue
    ra, dec, oid, row = float(r["right_ascension"]), float(r["declination"]), r["object_id"], int(r["row"])
    slug = old.get(oid) or "mj" + sexa(ra, dec)
    p = post[oid]
    firm = float(p["nir_sig"]) < -3
    m = re.search(r"\(([-+\d.]+) ([-+\d.]+) \+- ([\d.]+)", r["nsc_dr2"])
    note = "; ".join(x for x in (r["eye_note"], "forced J signal below 5 sigma on the pixels" if "below 5" in r["pixel_step"] else "") if x)
    C.append(dict(slug=slug, name="Euclid J" + slug[2:], object_id=oid, ra=round(ra, 6), dec=round(dec, 6), r=round(float(r["r"]), 2), pm=round(float(r["pm"]), 1), pmx=round(float(r["pmx"]), 1),
                  pmy=round(float(r["pmy"]), 1), e_pm=round(float(r["e_pm"]), 1), firm=firm, comp=COMP[r["comp_best"]], teff=int(float(r["teff_best"])), tmax=int(float(r["tmax_near"])),
                  dchi2=round(float(r["dchi2"]), 1), chi2=round(float(r["chi2_best"]), 1), nir_sig=round(float(p["nir_sig"]), 1), nir_mag=round(float(p["nir_mag"]), 2), opt_teff=int(float(p["opt_teff_H"])),
                  d_pc=int(round(float(r["d_best_model"]))), vtan=int(round(float(r["vtan_best_model"]))), snr_j=round(float(r["pix_NIR_J_snr"]), 1), snr_h=round(float(r["pix_NIR_H_snr"]), 1),
                  nsc=r["nsc_dr2"].split(" ")[0] if m else "none", nsc_pmra=float(m.group(1)) if m else None, nsc_pmdec=float(m.group(2)) if m else None, nsc_e=float(m.group(3)) if m else None,
                  nsc_sig=round((float(m.group(1)) ** 2 + float(m.group(2)) ** 2) ** 0.5 / float(m.group(3)), 1) if m else None, simbad=r["simbad_10as"], stage1=r["stage_one"], note=note, row=row))
    k = row // 12
    if k not in sheets:
        sheets[k] = Image.open(S2 / "sheets" / f"strong_absorption_{k:02d}.jpg").convert("RGB")
    y = (row % 12) * 218
    strip = sheets[k].crop((0, y + 18, 816, y + 218))
    strip.resize((1072, 265), Image.LANCZOS).save(img / f"{slug}-marked.jpg", quality=88)
    strip.crop((0, 0, 200, 200)).resize((360, 360), Image.LANCZOS).save(img / f"{slug}-thumb.jpg", quality=88)
gaia = [dict(id=g["GaiaEDR3"], ra=float(g["right_ascension"]), dec=float(g["declination"]), g=float(g["Gmag"]), d_plx=round(float(g["d_parallax"])), d_model=round(float(g["d_best_model"])),
             comp=COMP[g["comp_best"]], teff=int(float(g["teff_best"])), vtan=round(float(g["vtan_gaia"]))) for g in csv.DictReader(open(S2 / "gaia_strong_absorption.csv", encoding="utf-8"))]
assert len({c["slug"] for c in C}) == len(C)
meta = dict(date="2026-11-25", model="Claude Fable 5.2", harness="Claude Code, interactive session", tiles=6601, area=1650, movers=44602, wd=9407, quality=8186, strong=47, kept=len(C),
            firm=sum(c["firm"] for c in C), known=105, stage1=143, stage1_in=sum(c["stage1"].startswith("kept") for c in C), sim=0, false_box=23,
            steps=[["Point sources not in Gaia, VIS 20 to 24", 4789781], ["Moved by more than 30 mas/yr at 5 sigma", 44602], ["White dwarf candidates (reduced proper motion)", 9407],
                   ["Good photometry in seven bands", 8186], ["Need strong absorption, two flux measurements", 47], ["Kept after the pixel and eye checks", len(C)]])
(OUT / "wd_faint.json").write_text(json.dumps(dict(meta=meta, candidates=C, gaia=gaia), indent=1), encoding="utf-8")
print(len(C), "candidates,", meta["firm"], "firm,", sum(c["object_id"] in old for c in C), "slugs reused,", len(list(img.iterdir())), "images")
