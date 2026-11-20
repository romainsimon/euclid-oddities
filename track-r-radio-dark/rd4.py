"""Radio-bright, Euclid-dark sources: literature lookup through the CDS mirrors (no model call).

The Strasbourg CDS servers were down from 18 Nov 2026 (security incident). This uses the mirrors the CDS lists:
SIMBAD at IDIA (TAP) and VizieR at CfA / NAOJ / IDIA (classic asu-tsv interface).

  rd4.py        every source of dark_all.csv -> lit.jsonl (one line per source, resumable)

Per source, around the RACS-mid catalogue position:
  simbad_ids     every SIMBAD identifier of every object within 15 arcsec
  simbad_refs    every paper SIMBAD attaches to those objects (bibcode, title)
  ned            NED names, types, redshifts within 15 arcsec
  vizier         every VizieR catalogue with at least one row within 10 arcsec (name: title)
  pulsar         ATNF pulsars (B/psr/psr) within 30 arcsec
  vlass          VLASS epoch 1 Quick Look components (J/ApJS/255/30/comp) within 5 arcsec, Dec > -40 only
All descriptive (PREREG_R.md rule 8).
"""
from __future__ import annotations

import csv
import io
import json
import time

import pandas as pd
import requests

import rd

HOME = rd.HOME
SIMBAD = "https://simbad.idia.ac.za/simbad/sim-tap/sync"
NED = "https://ned.ipac.caltech.edu/tap/sync"
VIZ = ("https://vizier.cfa.harvard.edu", "http://vizier.nao.ac.jp", "https://vizier.idia.ac.za")
R_LIT, R_VIZ, R_PSR, R_VLASS = 15.0, 10.0, 30.0, 5.0


def tap(url, q, timeout=60, tries=2):
    for k in range(tries):
        try:
            r = requests.post(url, data=dict(REQUEST="doQuery", LANG="ADQL", FORMAT="csv", QUERY=q), timeout=(10, timeout))
            if r.status_code == 200 and not r.text.lstrip().startswith("<"):
                return list(csv.DictReader(io.StringIO(r.text)))
        except Exception:
            pass
        time.sleep(3)
    return None


def asu(params, timeout=120):
    """Classic VizieR query on the first mirror that answers. Returns the text, or None."""
    for h in VIZ:
        try:
            r = requests.get(h + "/viz-bin/asu-tsv", params=params, timeout=(10, timeout))
            if r.status_code == 200 and "#INFO\tError" not in r.text and "QUERY_STATUS=ERROR" not in r.text:
                return r.text
        except Exception:
            pass
    return None


def rows(text):
    """Data rows of an asu-tsv answer (first table only): list of lists."""
    out, seen = [], False
    for line in text.splitlines():
        if line.startswith("#") or not line.strip():
            if seen and out:
                break
            continue
        if line.startswith("---"):
            seen = True
            continue
        if seen:
            out.append(line.split("\t"))
    return out


def one(p):
    ra, dec = p.ra_mid, p.dec_mid
    c = f"{ra:.6f} {dec:+.6f}"
    rec = dict(sid=p.sid, name=p.name)
    cone = f"1=CONTAINS(POINT('ICRS', b.ra, b.dec), CIRCLE('ICRS', {ra:.6f}, {dec:.6f}, {R_LIT / 3600:.6f}))"
    ids = tap(SIMBAD, f"SELECT b.main_id, b.otype, i.id FROM basic AS b JOIN ident AS i ON i.oidref = b.oid WHERE {cone}")
    refs = tap(SIMBAD, 'SELECT DISTINCT r.bibcode, r.title FROM basic AS b JOIN has_ref AS h ON h.oidref = b.oid '
                       f'JOIN ref AS r ON r.oidbib = h.oidbibref WHERE {cone}')
    rec["simbad_ids"] = None if ids is None else sorted({f"{r['id']} ({r['otype']})" for r in ids})
    rec["simbad_refs"] = None if refs is None else sorted(f"{r['bibcode']} {r['title'][:140]}" for r in refs)
    ned = tap(NED, "SELECT prefname, prefphytype, z FROM objdir WHERE "
                   f"1=CONTAINS(POINT('J2000', ra, dec), CIRCLE('J2000', {ra:.6f}, {dec:.6f}, {R_LIT / 3600:.6f}))", timeout=25, tries=1)
    rec["ned"] = ["query failed"] if ned is None else [f"{r['prefname']} ({r['prefphytype'] or '-'}, z={r['z'] or '-'})" for r in ned]
    t = asu({"-c": c, "-c.rs": R_VIZ, "-meta": "", "-out.max": 1})
    if t is None:
        rec["vizier"] = None
    else:
        cats, name = {}, None
        for line in t.splitlines():
            if line.startswith("#Name:"):
                name = line[6:].strip()
            elif line.startswith("#Title:") and name:
                title = line[7:].strip()
                top = "/".join(name.split("/")[:3]) if name.startswith("J/") else "/".join(name.split("/")[:2])
                if title or top not in cats:
                    cats[top] = title or cats.get(top, "")
        rec["vizier"] = [f"{k}: {v}" for k, v in sorted(cats.items())]
    t = asu({"-source": "B/psr/psr", "-c": c, "-c.rs": R_PSR, "-out": "PSRJ"})
    rec["pulsar"] = None if t is None else [r[0] for r in rows(t)]
    if dec > -40:
        t = asu({"-source": "J/ApJS/255/30/comp", "-c": c, "-c.rs": R_VLASS, "-out": "CompName,Ftot,Fpeak,DCMaj,_r", "-out.max": 5})
        rec["vlass"] = None if t is None else [" ".join(r) for r in rows(t)]
    return rec


def main():
    C = pd.read_csv(HOME / "dark_all.csv", dtype={"sid": str})
    f = HOME / "lit.jsonl"
    done = {json.loads(x)["sid"] for x in open(f, encoding="utf-8")} if f.exists() else set()
    t0 = time.time()
    for i, p in enumerate(C.itertuples(), 1):
        if p.sid in done:
            continue
        rec = one(p)
        failed = [k for k, v in rec.items() if v is None]
        if failed:
            print(f"{i}/{len(C)} {p.name[10:]} failed: {failed} (not saved, a rerun retries)", flush=True)
            continue
        with open(f, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec) + chr(10))
        if i % 10 == 0:
            print(f"{i}/{len(C)} in {(time.time() - t0) / 60:.1f} min", flush=True)
    n = sum(1 for _ in open(f, encoding="utf-8")) if f.exists() else 0
    print(f"DONE {n} of {len(C)} sources in lit.jsonl", flush=True)


if __name__ == "__main__":
    main()
