# Probe 0 amendments

Each entry: date, type (planned fill-in / post hoc / clarification), what changed, why. Entries are append-only.

## A1. 2026-11-13, clarification (source substitution, before pixels used for any metric)
The live Lemon lensed-quasar database returned HTTP 500. Used the Wayback Machine snapshot of 2025-01-20 (`web.archive.org/web/20250120070059id_/https://research.ast.cam.ac.uk/lensedquasars/`). The archived response is cut at exactly 1,048,576 bytes; it contains 218 systems and ends at RA 356.07 deg, so systems with RA > 356.07 deg are missing from this source. Unioned with SIMBAD (Harvard mirror, `otype='LeQ'`, 188 rows; CDS SIMBAD unreachable). arXiv:2206.07714 tables not used (lower in the preference order). Result: 238 systems, 15 inside DR1 VIS tile polygons, 9 kept with a `dr1.mer_catalogue_wide_survey` row within 2″. Six systems inside tile polygons have **no MER wide-survey row within 10″** (COSMOS5921+0638, DESJ0247-6349, DESJ0600-4649, J1623+7533, SDSSJ1524+4409, WISE2344-3056), although ECLIPSE lists some of them; this looks like a MER wide-survey catalogue coverage gap and is not investigated further in Probe 0.

## A2. 2026-11-13, clarification (cutout route)
IRSA IBE rejects `center`/`size` cutout parameters on these files ("Unexpected query parameters"). The ESA Euclid archive SAS cutout service (`https://eas.esac.esa.int/sas-cutout/cutout?filepath=…&collection=MER&tileindex=…&POS=CIRCLE,ra,dec,r`) works anonymously. On dev tile 102163137 its 121×121 output was bit-identical to the same section assembled from 121 single-range IRSA requests, and a 120×120 PSF-star cutout was again identical. PREREG 3.4 named an "official IRSA cutout route"; the ESA archive's own cutout service is used instead (one request per cutout, 4 parallel connections), with IRSA range reads kept as the cross-check / fallback.

## A3. 2026-11-13, clarification (PSF implementation, dev tiles only, before T*)
PSF = photutils `EPSFBuilder` (iterative sigma-clipped median stack, oversampling 2, 41×41 native stamps) of the first 20 usable isolated stars per tile, evaluated by cubic spline. Chosen on dev tile 102163137 because it roughly halved the single-PSF χ² on held-out dev stars versus a native-grid shifted median stack. The fit uses 7 double-fit starts (3 matched-filter peaks of the single-fit residual + 4 symmetric 1.5 px splits).

## A4. 2026-11-13, spec gap noted (no change to verdict rules)
P1 has no upper separation bound but a detection requires a fitted separation ≤ 1.5″. Five of the nine kept known systems have literature separations > 1.5″ (1.57″–4.29″), so P1 as written can be at most 4/9. The verdict is computed as written; the 0.3″–1.5″ variant is reported only (PREREG 3.3).

## A5. 2026-11-13, shortfall (PREREG 3.2 rule applied)
1,205 parent-eligible Gaia quasar candidates in the 40 random tiles. Blind pool drawn first (500); parent sample = 705 (target ~1,500). Not filled from other tiles.

## A6. 2026-11-13, dev-tile finding and one reported-only variant (post hoc; dev tiles only; before any non-dev source was fitted and before T*)
On the two dev tiles (3,000 synthetic singles, 156 Gaia proper-motion stars, 67 quasar candidates, 540 injections), synthetic singles give T ≤ ~30 (99th percentile) but real stars give a median T ≈ 275 with 27% of fits in the separation window, mostly a tiny second component (fitted ratio 20–1000) absorbing PSF mismatch. A handful of *clean* stars (ruwe < 1.2, ipd_frac_multi_peak = 0) have fitted companions at ratio 22–40, 0.74″–0.82″, T ≈ 3×10⁵; these look like real faint companions, which no change of the noise term would remove. With the frozen rule they would set T* at ~10⁵ and push completeness at 0.4″ to ~50% on dev data. **No frozen element is changed** (ε, statistic, T* rule, window): P2/P3/P5 may fail as frozen, and that is reported.
Reported-only variant V1 (labelled post hoc, no verdict): add "fitted flux ratio ≤ 10" (the injection-grid maximum) to the detection rule and re-derive T* with the same 0.05% rule on the same calibration pool. Coded in `grade.py` before the blind key exists.
Pipeline fix found in the blind-path dress rehearsal (scratch key on dev quasars, discarded): `scikit-image` was missing, so photutils deblending had silently failed; it is now installed and errors are no longer swallowed.

## A7. 2026-11-13, planned fill-in: T*
T* = 467558.0401030904 (rule of PREREG 3.6; N_cal = 21,661 valid calibration sources = 20,000 synthetic + 1,661 calibration-half clean stars; k = 10). Source: `output/claudestronomy/probe0/tables/tstar.csv`. Not to be changed. SHA-256 of this file after this entry is in `AMENDMENTS.sha256`.
Process fixes before this fill-in (no frozen element changed): table floats written at full round-trip precision (a `%.6g` format had truncated RA/Dec used as cache keys and broke cutout lookups); P8 in `grade.py` measures manifest coverage, with empty service responses (outside coverage) reported separately.

## A8. 2026-11-13, post-freeze process notes (no threshold, rule or detector change)
- Blind set: 472 of 500 blind-pool cutouts gave a valid fit (others: NaN pixels or box off the image) and were sealed; 20% = 94 planted. Seal run at commit 946c26f, in the same agent session.
- Injection stage crashed on a column-name collision (`xb`, `yb`, `fb` in both the plant metadata and the fit row); metadata columns were prefixed `inj_` and only that stage was re-run. Detection code untouched.
- After the key existed, `grade.py` gained only report text (limitations and tool disclosure); no computation changed.

## A9. 2026-11-13, corrections to the record (post hoc; no verdict changed)
- **A4 was wrong.** It said P1 "can be at most 4/9". The grader counts 6/9: all 4 in-window systems (literature separation 0.3″–1.5″) plus 2 of the 5 wide ones, which were flagged at an in-window fitted separation: DESJ0405-3308 (literature 1.57″, fit 1.39″) and DESJ0501-4118 (literature 3.72″, fit 1.26″). The DESJ0501 flag does not match the literature geometry.
- `AMENDMENTS.sha256` hashes this file as of commit 946c26f (through A7). It is reproduced by `git show 946c26f:tools/claudestronomy/prereg/AMENDMENTS.md | sha256sum`. A8 and A9 were appended later and are not covered by it.
- Line endings: `.gitattributes` (`* -text`) was added for `prereg/` and `output/claudestronomy/probe0/` so that a Windows checkout keeps LF bytes and PREREG.sha256 and the P7 hashes still verify.
- MER check: 4 of the 40 random tiles return **zero** `dr1.mer_catalogue_wide_survey` rows in a 3′ cone at the tile centre. ECLIPSE lists a MER object id for WISE2344-3056 (L005653), yet a 10″ cone finds no row. The "MER coverage gap" in A1 is therefore unexplained (possibly a gap in the TAP table, not in the sky). P4b's 7.21% chance-projection figure is averaged over tiles that include those zeros and is biased low for them. Two of the six dropped known systems (SDSSJ1524+4409, WISE2344-3056) appear in the ECLIPSE-A set and were fitted there.
- P2/P3 edge cell: of the 349 misses at 1.5″, 176 have a fitted separation just above 1.5″ (the window edge) and 239 have T ≤ T*.
- Not done: the Track B variability statistic and Gaia DataLink (named in the spec without a step or threshold); `figures/`; the IRSA range-read fallback for the 14 empty SAS responses (`cutout.get` returns None); the arXiv:2206.07714 tables.
