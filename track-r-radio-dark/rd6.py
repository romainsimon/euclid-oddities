"""Radio-bright, Euclid-dark sources: existing observations in public archives (no model call).

  rd6.py      every source of dark_all.csv -> archives.jsonl (one line per source, resumable)

ALMA (ObsCore TAP at almascience.eso.org): any observation whose pointing lies within 30 arcsec.
ESO (ObsCore TAP at archive.eso.org): any reduced product within 10 arcsec; spectra and cubes are listed separately from images.
Descriptive only (PREREG_R.md rule 8). A hit means data exist at that position, not that the source was the target.
"""
from __future__ import annotations

import json

import pandas as pd

import rd
import rd4

HOME = rd.HOME
ALMA = "https://almascience.eso.org/tap/sync"
ESO = "https://archive.eso.org/tap_obs/sync"


def main():
    C = pd.read_csv(HOME / "dark_all.csv", dtype={"sid": str})
    f = HOME / "archives.jsonl"
    done = {json.loads(x)["sid"] for x in open(f, encoding="utf-8")} if f.exists() else set()
    for i, p in enumerate(C.itertuples(), 1):
        if p.sid in done:
            continue
        ra, dec = p.ra, p.dec
        a = rd4.tap(ALMA, "SELECT target_name, proposal_id, band_list, t_exptime, obs_release_date FROM ivoa.obscore WHERE "
                          f"1=CONTAINS(POINT('ICRS', s_ra, s_dec), CIRCLE('ICRS', {ra:.6f}, {dec:.6f}, {30 / 3600:.6f}))", timeout=90)
        e = rd4.tap(ESO, "SELECT dataproduct_type, instrument_name, obs_collection, target_name, t_exptime, em_min, em_max FROM ivoa.ObsCore WHERE "
                         f"1=CONTAINS(POINT('ICRS', s_ra, s_dec), CIRCLE('ICRS', {ra:.6f}, {dec:.6f}, {10 / 3600:.6f}))", timeout=90)
        if a is None or e is None:
            print(f"{i}/{len(C)} {p.name[10:]} failed: {'alma ' if a is None else ''}{'eso' if e is None else ''} (a rerun retries)", flush=True)
            continue
        rec = dict(sid=p.sid, name=p.name, alma=a[:20],
                   eso_spectra=[r for r in e if r["dataproduct_type"] in ("spectrum", "cube")][:20],
                   eso_images=sorted({f"{r['instrument_name']} / {r['obs_collection']}" for r in e if r["dataproduct_type"] not in ("spectrum", "cube")}))
        with open(f, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec) + chr(10))
        if rec["alma"] or rec["eso_spectra"]:
            print(f"HIT {p.name[10:]} alma {len(rec['alma'])} eso spectra/cubes {len(rec['eso_spectra'])}", flush=True)
        if i % 20 == 0:
            print(f"{i}/{len(C)}", flush=True)
    R = [json.loads(x) for x in open(f, encoding="utf-8")]
    print(f"DONE {len(R)} of {len(C)}: ALMA {sum(bool(r['alma']) for r in R)}, ESO spectra or cubes {sum(bool(r['eso_spectra']) for r in R)}, "
          f"ESO images {sum(bool(r['eso_images']) for r in R)}", flush=True)


if __name__ == "__main__":
    main()
