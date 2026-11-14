# Track A v2 feasibility gate: candidate rules and selection procedure (pre-specified)

Written 13 Nov 2026 and committed **before** any candidate rule is evaluated on gate data. Parent plan:
`ceo/claudestronomy/businesses/claudestronomy/v2-improvement-plan.md` (sections 3.1 principle 4, 3.2-3.4, 6).
Evaluation code: `evaluate.py` in this folder implements exactly this file; any deviation is listed as an amendment
at the end of the report, with its reason, never silently.

Development data only: the 60 tiles of Probe 0 (`output/claudestronomy/probe0/tables/tiles.csv`). No fresh tile
is drawn, listed or touched. Tile 102153718 (corrupted PSF stack, red-team F5) is excluded everywhere. Nothing
here freezes v2 or produces a v2 result.

What was looked at before this file was written (none of it is a bar statistic): star counts per tile from cached
Gaia queries; MER table names and per-tile row counts; a smoke test of the third model and the photutils check on
one dev-tile star (102163137) with hand-planted companions and galaxies; a failed empirical gain fit (below).

## 1. Detector (fixed)

- v1 one-vs-two PSF fit (`src/detect.py`), unchanged, including its weights (sky sigma plus 3% model term), so
  that T keeps the meaning it has in the plan's thresholds. v1 per-tile PSFs (`work/psf`).
- Validity gates: fit box (41x41) with any non-finite or exactly-zero pixel is invalid; single-PSF flux <= 0 is
  invalid; sigma_b <= 0 is invalid. PSF gate per tile: centroid offset <= 0.2 px, negative fraction <= 0.1%,
  FWHM 0.12-0.25"; a failing tile is excluded (no neighbour fall-back in this gate). Invalid fits count as
  non-detections for injected and planted objects and are excluded from the null-star denominator (reported).
- Third model: one PSF plus one Sersic convolved with the tile PSF stamp, n fixed at 1 and at 4 (best chi2 of the
  two), Re in [0.15", 1.0"], axis ratio >= 0.25, free centres inside the fit box; amplitudes linear and
  non-negative; same pixel weights as the two-PSF fit. Starts: PSF on the brighter two-PSF component and galaxy
  on the fainter, and both on the single-PSF centre. Statistic Tg = (chi2_gal - chi2_2PSF) / 3, both chi2
  evaluated with identical weights. Run on every object passing the loosest rule (it can only remove flags).
- Window 0.15" <= fitted separation <= 1.8" (upper edge off the 1.5" grid point; the lower edge stays at the
  plan's 0.15", which is a grid point; noted, affects only the P3 curve).

## 2. Candidate rules (48)

A flag requires: valid fit, T > T_det, fitted flux ratio <= cap, separation in window, and the veto condition.

- T_det in {1000, 3000, 10000}
- cap in {10, 15}
- veto in, in this order: V0 none; A0 Tg > 0; A30 Tg > 30; A300 Tg > 300; R05 (chi2_gal - chi2_2)/chi2_2 > 0.05;
  R20 same > 0.20; Q30 two-PSF reduced chi2 (chi2_2 / 1674) <= 30; Q10 same <= 10.

## 3. Samples (development data)

- **Verified null (P4).** v1 Gaia "clean" stars on all 59 usable v1 tiles (G 18-20.5, parallax/error > 5 or
  proper-motion significance > 5, > 15" from tile edge, no Gaia source within 3", ruwe < 1.2,
  ipd_frac_multi_peak = 0), minus the v1 PSF-stack stars. MER check against all four DR1 MER catalogue tables
  (wide_survey, wide_mode, deep_survey, deep_mode), pulled per tile_index with two-sided flux predicates (VIS or H
  flux between 25.5 mag and 1e9 uJy; NaN rows excluded, H-only rows kept; row count checked against COUNT(*)):
  MER primary within 0.5" and no other MER source within **2.5"** (plan 3.3) brighter than primary + 5 mag in VIS
  or in H. A tile with zero MER rows is dropped and listed. Fit sample: every star of the 2.0" null (superset) with
  a cached cutout plus a seeded draw of the rest, 13,000 in total; P4 is graded on the 2.5" subset and reported on
  the 2.0" set. **No P4 verdict below 10,000 valid fits.**
- **Donor-star injection (P2, P3).** Hosts: v1 parent quasars, valid gated fit, not flagged by the loosest rule.
  Grid 0.15, 0.2, 0.3, 0.4, 0.6, 1.0, 1.5" x ratio 1, 2, 5, 10; 100 trials per cell, alternately without and with a
  deflector. Image B is a real star from the same tile (verified null, valid, not loose-flagged), background
  subtracted, shifted by whole pixels and scaled; donor flux >= 2x the planted flux when such a donor exists, else
  the brightest donor >= 1x (scale reported). Deflector: Sersic n ~ U[2.5, 5.5], Re ~ U[0.2, 0.6]", q ~ U[0.6, 1],
  VIS ~ U[20.5, 22.5], at fraction ratio/(1+ratio) along A->B, convolved with the donor star stamp (not with the
  model PSF). Poisson noise on all added light with an effective gain of 7,880 e- per ADU/s.
- **Galaxy-only trials (P4g).** Same hosts, grid and deflector generator, with no image B: 1,400 trials.
- **Blind-style set (P5; development, NOT blind).** v1 blind-pool quasars (raw cached cutouts), valid gated fit.
  20% planted (seeded) among hosts with VIS <= 22.5, with the v1 seal distribution (sep U[0.4, 1.5]", ratio
  log-uniform in [1, min(5, 10^((22.5 - m)/2.5))], half with a deflector) using donor stars, deflector and Poisson
  noise as above. The rest are unplanted, unchanged.
- Effective gain: the mosaic headers carry no GAIN or EXPTIME. An empirical fit of residual variance against
  model value failed (PSF mismatch dominates; `calib_gain.json`). Adopted: 4 x 566 s x 3.48 e-/ADU = 7,880
  e- per ADU/s (nominal VIS wide-survey values, from memory, to be checked). Sanity check: a sky of about 22.2
  mag/arcsec^2 gives sigma about 0.0034 ADU/s per pixel at this gain, against measured sigma_b of 0.003.

## 4. Bars (point estimates decide; intervals reported)

Geometry scoring for P2, P3, P5: a recovery counts only if |fitted sep - true sep| <= max(0.1", 0.2 x true sep).

| ID | Metric | PASS |
|---|---|---|
| P2 | Donor injections, nominal sep 0.4-1.5", ratio <= 5, faint image VIS <= 22.5, both deflector states pooled; detection with geometry | >= 90% |
| P3 | Same injections, ratio <= 2, faint VIS <= 22.5, pooled: separation of the first upward 50% crossing, linear interpolation between grid points (<= 0.15" if already >= 50% at 0.15") | <= 0.3" |
| P4-A | Raw flag rate on the 2.5" verified null (valid fits) | <= 0.1% |
| P4-B | Flags on the 2.5" verified null not confirmed by the check (section 5) | <= 0.1% |
| P4g | Galaxy-only trials flagged (any geometry) | <= 5% |
| P5 | Blind-style recall on planted (geometry) and false-claim rate on unplanted | >= 85% and <= 3% |

Intervals: Clopper-Pearson 95% for every proportion; P2 also by bootstrap over hosts (1,000); P3 by bootstrap
over trials (1,000).

## 5. Confirmation check (P4-B)

photutils segmentation of the cutout (3 sigma_b, 5 pixels, Gaussian kernel FWHM 1.5 px) and deblending, two
settings: K1 (nlevels 32, contrast 1e-3) and K2 (nlevels 64, contrast 1e-5). A flag is confirmed iff the segments
nearest to the two fitted components are distinct and their separation agrees with the fitted separation within
0.15". No NISP leg in this gate (budget); every flag the check cannot resolve counts as a false alarm.

Admissibility: on a seeded random 2,000 stars of the null fit sample, among those not flagged by the loosest rule,
the fraction with >= 2 segments within 1.8" must be <= 1.0%. The most sensitive admissible setting is used (K2 if
admissible, else K1); if neither is admissible, P4-B = P4-A. Its sensitivity (confirmation rate of loose-flagged
no-deflector injections at 0.4-1.5") is reported.

## 6. Verdict and selection

- A rule passes if every bar in section 4 passes. P4 is taken under definition B ("pass-B") and under definition A
  ("pass-A"). Verdict: **feasible** if some rule is pass-A (hence pass-B too unless the check is degenerate);
  **feasible only under definition B** if some rule is pass-B and none is pass-A; **not feasible** otherwise.
- Selection among passing rules (pass-A preferred over pass-B only): smallest T_det, then the veto order of
  section 2, then cap 15 before 10. The first is the selected rule.
- If no rule passes: for each rule compute excess ratios e (<= 0 means the bar passes):
  P2: (1 - P2)/0.10 - 1; P3: crossing/0.3 - 1; P4: rate/0.001 - 1 (definition B); P4g: rate/0.05 - 1;
  P5 recall: (1 - recall)/0.15 - 1; P5 false claims: rate/0.03 - 1. The best rule minimises max(e), ties broken
  by the selection order. The gap is that rule's failing bars with their values and excess ratios. The Pareto
  frontier over the six error quantities is reported in full.
- Reported, not graded: P4 on the 2.0" null; flags by separation bin, tile and magnitude; P2 with and without a
  deflector; check sensitivity; donor scale distribution; invalid-fit counts by reason.

## 7. Out of scope here

P1, P1b, P6, the photutils baseline ROC, noise-model recalibration (v1 weights kept on purpose), the NISP
confirmation leg, the colour test, and anything on fresh tiles.
