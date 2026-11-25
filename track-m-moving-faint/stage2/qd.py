"""Track M, second stage (characterisation): data assembly. No selection, no model.
qd.py ls <in.csv> <out.csv>   Legacy Surveys DR10 Tractor row at each (ls_ra, ls_dec), from the viewer catalogue service (all bands with errors)
qd.py eu <in.csv> <out.csv>   Euclid DR1 MER columns by object_id (template-fit and aperture near-infrared fluxes, Galactic E(B-V))
Input needs object_id, ls_ra, ls_dec. Both modes resume."""
import csv
import io
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd
import requests

LSV = "https://www.legacysurvey.org/viewer/ls-dr10/cat.fits"
EU = "https://eas.esac.esa.int/tap-server/tap/sync"
B = "griz"
LS_COLS = (["ra", "dec", "type", "brick_primary", "maskbits", "fitbits", "ebv", "ref_cat", "flux_w1", "flux_w2", "flux_ivar_w1", "flux_ivar_w2"]
           + [f"{k}_{b}" for k in ("flux", "flux_ivar", "mw_transmission", "nobs", "fracflux", "fracmasked", "rchisq", "anymask", "psfdepth", "psfsize") for b in B])
R_BOX, R_MATCH, THREADS = 1.0, 0.3, 4
EU_B = [f"{b}_ext_decam" for b in B] + ["y", "j", "h"]
EU_COLS = (["object_id", "gal_ebv", "flux_vis_psf", "fluxerr_vis_psf", "flag_vis", "flag_y", "flag_j", "flag_h", "det_quality_flag", "spurious_flag", "point_like_prob"]
           + [f"{k}_{b}_templfit" for b in EU_B for k in ("flux", "fluxerr")] + [f"{k}_{b}_{a}fwhm_aper" for b in "yjh" for a in (1, 2) for k in ("flux", "fluxerr")])


def ls_one(row):
    from astropy.table import Table
    oid, ra, dec = row
    dd = R_BOX / 3600
    dr = dd / np.cos(np.radians(dec))
    for k in range(4):
        try:
            r = requests.get(LSV, params=dict(ralo=ra - dr, rahi=ra + dr, declo=dec - dd, dechi=dec + dd), timeout=(15, 60))
            if r.status_code == 200:
                T = Table.read(io.BytesIO(r.content))
                if not len(T):
                    return [oid, "none"] + [""] * (len(LS_COLS) + 1)
                d = np.hypot((np.array(T["ra"]) - ra) * np.cos(np.radians(dec)), np.array(T["dec"]) - dec) * 3600
                i = int(np.argmin(d))
                if d[i] > R_MATCH:
                    return [oid, "far"] + [""] * (len(LS_COLS) + 1)
                v = []
                for c in LS_COLS:
                    x = T[c][i]
                    v.append(x.decode().strip() if isinstance(x, bytes) else (str(x).strip() if c in ("type", "ref_cat") else x))
                return [oid, "ok", round(float(d[i]), 3)] + v
        except Exception:
            pass
        time.sleep(3 * (k + 1))
    return [oid, "failed"] + [""] * (len(LS_COLS) + 1)


def ls(inp, out):
    I = pd.read_csv(inp, usecols=["object_id", "ls_ra", "ls_dec"])
    done = set()
    if os.path.exists(out):
        O = pd.read_csv(out, usecols=["object_id", "status"])
        done = set(O.object_id[O.status != "failed"])
        pd.read_csv(out)[lambda d: d.status != "failed"].to_csv(out, index=False)
    todo = [tuple(x) for x in I[~I.object_id.isin(done)].itertuples(index=False)]
    print(f"{len(I)} positions, {len(done)} done, {len(todo)} to fetch", flush=True)
    new = not os.path.exists(out)
    with open(out, "a", newline="") as f, ThreadPoolExecutor(THREADS) as ex:
        w = csv.writer(f)
        if new:
            w.writerow(["object_id", "status", "d_arcsec"] + LS_COLS)
        for n, row in enumerate(ex.map(ls_one, todo)):
            w.writerow(row)
            if n % 200 == 0:
                f.flush()
                print("  ", n, len(todo), time.strftime("%H:%M"), flush=True)


def eu(inp, out):
    I = pd.read_csv(inp, usecols=["object_id"]).object_id.drop_duplicates().tolist()
    parts = []
    for k in range(0, len(I), 300):
        q = f"SELECT {', '.join(EU_COLS)} FROM dr1.mer_catalogue_wide_survey WHERE object_id IN ({', '.join(str(x) for x in I[k:k + 300])})"
        for a in range(4):
            try:
                r = requests.post(EU, data=dict(REQUEST="doQuery", LANG="ADQL", FORMAT="csv", QUERY=q), timeout=(15, 300))
                if r.status_code == 200 and not r.text.lstrip().startswith("<"):
                    parts.append(pd.read_csv(io.StringIO(r.text)))
                    break
            except Exception:
                pass
            time.sleep(10)
        else:
            print("chunk failed at", k, flush=True)
        if k % 3000 == 0:
            print("  ", k, len(I), flush=True)
    E = pd.concat(parts, ignore_index=True)
    E.to_csv(out, index=False)
    print(f"{len(I)} ids asked, {E.object_id.nunique()} returned")


{"ls": ls, "eu": eu}[sys.argv[1]](sys.argv[2], sys.argv[3])
