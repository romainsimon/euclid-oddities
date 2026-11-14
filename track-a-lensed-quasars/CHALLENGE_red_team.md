# Probe 0: fresh-agent challenge (rubric item 4)

Reviewer: an independent Claude agent that did not write the Probe 0 code. Scope: find what is wrong or unproven, not rescue the result. The authors' files are unchanged. All scripts, intermediate CSVs, PNG panels and cached archive answers (anonymous TAP queries, about 1 request/s) are in `output/claudestronomy/probe0/challenge/`. Every analysis reads the authors' cache offline (`CLAUDESTRONOMY_OFFLINE=1`) through their own `cutout.py`, `detect.py` and `manifest.py`. Re-fits reproduce the tabulated T exactly (see `a5_companions_mer.csv`, `T_table` = `T_refit`).

Severity scale: **B** blocks a conclusion; **W** weakens one; **M** minor.

## Bottom line

1. **The authors' explanation of the failure holds in substance but is mis-described, and it has bigger consequences than they draw.** The stars that set T* do have real faint neighbours: 8 of the top 11 calibration stars have a separate MER catalogue source within 0.04″ of the fitted companion, with matching VIS magnitude. 2 more look double in the panels, and 1 is a pipeline failure. The rate of these companions matches chance projection: MER density predicts 0.51% at VIS < 22, against 0.55% observed on clean stars. These companions are not "ratio 20–40 at ~0.8″" as A6 and the REPORT say. They span ratios 2.6–40 (most 4–11) at 0.5–1.5″, and several sit inside the P2 injection range.
2. **The main consequence is a design error in the pre-registration.** The T* null ("clean" Gaia singles) contains the signal: about 0.5–1% of those stars have real VIS-detected neighbours. No threshold on T can satisfy P2 ≥ 90% and the real-star P4 ≤ 0.1% at the same time. P2 ≥ 90% needs T* ≤ ~2×10⁴, which flags 2.5% of real held-out clean stars. P2 ≥ 80% needs T* ≤ ~1.3×10⁵, which flags 1.3%. Under the pooled frozen P4 rule, the P2 ≥ 90% threshold also fails: 41/21,653 = 0.19%. Separately, the statistic itself is weak below about 0.5″. At fixed host brightness (VIS 19.5–20.5, no deflector), median T for equal-flux pairs is 2.5×10⁴ at 0.4″ against 9×10⁶ at 0.6″, even though the fitted separations are correct. So P3 and the 0.3–0.4″ misses are a detector-statistic limitation that would remain under a clean null.
3. **Two of the PASS verdicts (P4 and P6) are artefacts of how they were defined.** P4 passes only because 20,000 noiseless synthetic singles, all with T ≤ 36, dilute 1,653 real stars. The real held-out rate is 0.48%, five times the limit. P6 passes only because the baseline was compared at its untuned 29% false-claim rate. Swept to a ≤ 1% false-claim rate, the simple photutils baseline's point estimate leads by 2–10 points. The bootstrap intervals include 0, so the ordering there is unresolved (post hoc).
4. Pipeline and catalogue defects distort P1 and P4b and slightly contaminate T*:
   - MER rows are split across tables.
   - The server returns NaN fluxes as "greater than" any cut.
   - One tile has a corrupted PSF.
   - Masked (zero) pixels pass the validity checks.
   - Fits with zero single-PSF flux are kept as valid.

## Findings

### F1 (B, design). The T* calibration null contains real doubles; P2 and the real-star P4 are mutually infeasible

**Evidence.**
- **T* is a real-star quantile.** T* = 467,558 is the 11th-largest in-window T among 21,661 calibration sources. The 20,000 synthetic singles all have T ≤ 35.7 (`a1_tstar_population.py`), so T* is in fact the 11th of 1,661 real clean stars. That is the 0.66% quantile of real stars, not 0.05%.
- **The T*-setting stars have real neighbours** (`a5_companions_mer.py`, `a5_companions_mer.csv`, `challenge/png/`). For the top 12 calibration stars and the 8 flagged held-out stars, the fainter fitted component was converted to RA/Dec and matched against `dr1.mer_catalogue_wide_survey` (or `wide_mode`, see F4).
  - **Calibration top 11:** 8 have a MER source 0.005–0.041″ from the fitted companion. Its VIS PSF magnitude agrees with the fitted companion magnitude to 0.0–0.5 mag (e.g. T* star 1434686580589095424: MER 21.76 vs fit 21.63, offset 0.041″).
  - **The other three of the top 11:**
    - Rank 8 (2554632906845355008) is a single-fit failure on a zero-masked hole with no star in the box (F5).
    - Two (4786315746551163264 at 0.50″ and 1393975891264342016 at 0.52″) have no MER counterpart, but the panels show a clearly elongated second peak. They are most likely real pairs that MER did not deblend.
  - **Held-out "false alarms":** 8 of 8 have a MER source 0.003–0.018″ from the fitted companion, with matching magnitude.
  - **NISP:** MER lists H-band template fluxes for all matched companions, 1–2 mag brighter than in VIS (red objects). These are forced at VIS positions, so they are supportive, not independent. A direct NISP-image check was **not tested**.
- **Position angles.** For the 42 clean stars with in-window T > 10⁵, the position-angle distribution is mildly non-uniform (χ² p = 0.049). The excess bin (60–90°, 10 stars) is spread over 8 tiles and separations 0.4–1.5″. Three of those were checked and all have MER counterparts. This is a watch item, not evidence of an artefact.
- **Chance projection.** At VIS < 22 (finite fluxes only, correct MER table per tile, two zero tiles dropped), MER source density predicts a chance-projection probability of **0.51%** in the 0.15–1.5″ annulus (0.40% at VIS < 21.5, 0.66% at < 22.5). The observed flag rate is 0.55% on clean stars and 0.85% on all proper-motion stars. The companions are quantitatively explained by chance projections, plus physical binaries among the proper-motion stars.
- **T does not mainly measure PSF mismatch.** Single stars with no strong companion (T < 2×10⁴) have median T of 180–550, rising with brightness, and reduced χ² of 2.5–6 for the single fit (`a14_noise_model.py`). Real companions give T of 10⁵–10⁷. The bulk of T reflects PSF mismatch plus a noise model with no source Poisson term. The tail that sets T* is signal.
- **Infeasibility** (`a13_p2_decomp.py`). Over the P2 subset:

| Threshold | P2 | Real held-out clean-star flag rate |
|---|---|---|
| Frozen T* = 467,558 | 69.3% | 0.48% |
| T* minus the failure and the 8 MER-confirmed calibration stars (95,615) | 80.8% | 1.33% |
| P2 ≥ 80% (T* ≤ ~128,000) | 80% | 1.33% |
| P2 ≥ 90% (T* ≤ ~19,800) | 90% | 2.48% |

- **How the P2 misses split** (2,272 trials):
  - 591 have T ≤ T* with the separation in the window. They are dominated by faint image VIS 22–22.5 (83% of the trials in that bin miss) and by separations of 0.4″.
  - 99 have a fitted separation outside the window, mostly just above 1.5″.
  - 7 are single-fit failures.
  - 10 detections have the wrong geometry (|fitted − true separation| > 0.2″), all with a deflector.

**What it means.** The authors are right that "real faint companions" set T*. But their framing as a nuisance that made thresholds fail undersells it. Under the frozen definitions, a perfect two-point-source detector would also FAIL, because it would correctly flag the real doubles in the "clean" pool. The P4 "false alarms" on real stars are mostly true detections.

**Recommended v2 change.**
- Define the null as objects verified to have **no** catalogue neighbour within 2″ brighter than (primary + 5 mag), checked in every MER table and in NISP. Report "astrophysical neighbour rate" as its own reported-only metric.
- Calibrate T* on real objects only, or on synthetic singles built from real star stamps with source noise. Never pool in noiseless same-PSF synthetics.
- Before freezing, check on dev tiles that some threshold satisfies all PASS bars at once (a feasibility gate).

### F2 (B for P4). P4 PASS is vacuous

**Evidence.**
- Pooled P4 is 8/21,653 = 0.04%. The 20,000 synthetic singles use the detector's own PSF, add no source noise and sit on pre-screened empty sky, so T ≤ 36 by construction (reduced χ² = 1.00–1.04).
- The real held-out rate is 8/1,653 = 0.48% (CI 0.21–0.95%), above the 0.1% bar.
- The REPORT notes "the real held-out rate is the informative number" but still prints P4 = PASS.

**Recommended v2 change.** Grade the real and synthetic rates separately, with the real rate binding. If synthetic singles are kept, render them from real star stamps (or the PSF plus measured mismatch residuals) with Poisson noise.

### F3 (W, and B for P3). The noise model is not calibrated, so T is not a likelihood-ratio statistic, and T collapses below about 0.5″

**Evidence.** The pixel variance is σ_b² + (0.03·M₁)², with no source photon term. Reduced χ² after the two-component fit is still 2–5 for singles and 4–60 for the top companion stars. T grows with flux even with no companion (median T 180 at VIS 20–20.5, 550 at VIS 17–18). Any threshold on T is therefore empirical and depends on brightness. Injections without a deflector on VIS 19.5–20.5 hosts give these median T values, while the fitted separations are correct to 0.003″ (`a15_followups.py`):

| Separation | Ratio 1 | Ratio 5 |
|---|---|---|
| 0.15″ | 4.0×10³ | — |
| 0.3″ | 1.8×10⁴ | 3.2×10⁴ |
| 0.4″ | 2.5×10⁴ | 1.6×10⁵ |
| 0.6″ | 9.2×10⁶ | 4.4×10⁵ |
| 1.0″ | 1.2×10⁷ | 5.5×10⁵ |

The jump of more than two orders of magnitude between 0.4″ and 0.6″ at ratio 1 suggests that the 0.03·M₁ term de-weights exactly the core pixels where close pairs differ from one PSF. P3 (0.44″) therefore fails because of the statistic, independently of the contaminated null.

**Recommended v2 change.** Add the source Poisson term (gain × exposure from the mosaic header). Calibrate the PSF-mismatch term on dev stars so the median reduced χ² ≈ 1 across magnitudes. Consider a brightness-dependent T* or a normalised statistic, such as T divided by the single-fit reduced χ².

### F4 (W, and B for N_known and P4b). MER queries hit only one of several DR1 MER tables, and NaN fluxes pass "greater than" cuts

**This is a specification defect, not an implementation bug:** PREREG 3.3 and 3.11 name `wide_survey`.

**Evidence** (`a3_mer_zero_tiles.py`, `a4_mer_zero_followup.py`, `a4b_mer_tables.py`, `a4c_dropped_known.py`).
- **The four zero-row tiles.** Three of them (102090830, 102092269, 102139830) have valid VIS pixels but no rows in `dr1.mer_catalogue_wide_survey`. Their sources are in `dr1.mer_catalogue_wide_mode`, with 111–181 rows within 30″ of a valid star. The fourth (102153718) has its tile centre in a data hole: 75% of its cutouts are non-finite, while `wide_survey` has rows where pixels exist. So the zeros are a query-scope bug in three tiles and a footprint hole in one, not real emptiness. TAP_SCHEMA gives no table descriptions, so I do not infer what "mode" vs "survey" means.
- **Dropped known systems.** Three of the six systems dropped for "no MER row" are in other tables:
  - COSMOS5921+0638 (1.0″, `deep_mode`);
  - SDSSJ1524+4409 (`wide_mode`) = ECLIPSE EUCL-DR1-L017819;
  - WISE2344-3056 (`wide_mode`) = ECLIPSE L005653.
- **Effect on P1.** The last two were fitted in the ECLIPSE-A set and are both flagged, but at separations of 0.18″ and 0.73″ against literature values of 1.80″ and 2.18″ (see F6). With them, N_known ≥ 11 and P1 as graded is about 8/11 (still FAIL). COSMOS5921 was not fitted.
- **NaN flux rows.** On the ESA TAP server, `flux_vis_psf > x` also returns rows whose flux is NaN, which the schema says marks NIR-only objects. In a 3′ cone on tile 102008213, the query `flux_vis_psf > 9.12` (VIS < 21.5) returned 987 rows, of which only 91 have a finite flux. The authors' P4b density (`grade.chance_density`, VIS < 24.5) and its 7.21% figure are therefore inflated by NIR-only rows and deflated by the four zero tiles. Both biases are uncontrolled, so the number should not be used. The fix is to add `AND flux_vis_psf < 1e9`, or an explicit NaN exclusion.

**Recommended v2 change.**
- Query all DR1 MER catalogue tables (`wide_survey`, `wide_mode`, `deep_survey`, `deep_mode`), or resolve the tile to its table first.
- Always bound flux predicates on both sides.
- Re-derive the known set and N_known.
- Assert non-zero MER density for every tile with valid pixels.

### F5 (W). Pipeline defects that pass the validity checks

**Evidence** (`a2_psf_health.py`, `a6_failures.py`, `a7_zero_masked_boxes.py`).
- **Corrupted PSF on tile 102153718 (root cause likely, not proven).** Its centroid is offset −1.89 px in x (all other tiles are within ±0.15 px), it has a −5% negative lobe and a ring structure (`png/psf_102153718_vs_102154088.png`), and photutils warned "All unmasked data values in star cutout are zero".
  - **Root cause.** `build_psf` accepts a stamp when σ_b = 0, because the test `peak < 50·σ_b` cannot reject anything when σ_b = 0. The zero-masked stamps then enter the stack. This is consistent with `main_log.txt`, where the last "All unmasked data values in star cutout are zero" warning comes immediately before `psf 102153718 20`. Six such warnings occur in total, so other tiles may be mildly affected, but no other tile fails the centroid or negativity checks.
  - **Consequences.** 7 of the 50 valid star fits on that tile have f1 = 0, and the tile's median star T is 10,724 against about 350 elsewhere. The tile also carries 60 injections and 4 blind files.
- **f1 = 0 fits are kept as valid.** When the single-PSF amplitude is clipped to 0, chi1 is the empty-model χ² and T becomes meaningless. This affects 9 real, 10 injection and 1 blind fit; 4 of the injection cases count as "detections".
- **Masked (exactly zero) pixels are not rejected.** They appear in the fit box of 68 star fits, 8 parent fits and 8 of the 686 sky patches used. One case, a Gaia "clean" star whose position is a zero-filled mask hole with no star present (`png/fail_2554632906845355008_cutout.png`), ranks 8th in the T* list at T = 721,460. Removing it alone moves T* only to 437,787 (P2 70.3%), so this is a contamination, not the cause of the failure.
- **Window edge.** The 1.5″ injection grid point equals the window bound. 21% of the 1.5″ trials have a fitted separation in (1.5″, 1.6″], and ratio ≤ 2 completeness at 1.5″ is 78.5% against 97.5–99% at 0.6–1.0″. The REPORT notes this (A9), but it is a built-in loss inside the P2 range.

**Checked and fine.**
- The pixel scale is 0.1″: CD = ±2.78×10⁻⁵ deg, north up, east left, as `common.PIX` assumes.
- The cutout crop places the target within ±0.5 px of (60, 60), with no off-by-one.
- The ePSF array (83×83 at oversampling 2) is centred as `PSF.render` assumes; the centroid is within ±0.15 px on 59 of 60 tiles.
- The fitted VIS magnitude minus Gaia G is −0.33 (median), which is plausible.
- My own scripts a1 and a5 hard-code zero point 24.5. Six tiles use 24.4, so the derived magnitudes there are 0.1 mag off. No conclusion depends on this.

**Recommended v2 change.**
- Reject boxes or stamps containing exact zeros or non-finite pixels.
- Mark f1 ≤ 0 as invalid.
- Add PSF sanity gates (centroid < 0.2 px, negative fraction < 0.1%, FWHM in range) with a fall-back to the neighbouring tile.
- Set the window bound away from grid points, or extend it to 2″.

### F6 (W). P1 counts detections, not recovered lens geometry

**Evidence** (`a10_p1_geometry.py`). Fitted components were converted to RA/Dec and compared with MER sources around each kept system:
- **Four of six recoveries match two MER sources within 0.15″**, so the pair is a real recovery: DESJ0115-5244, DESJ0405-3308 (two images of the quad at 1.39″), HE0512-3329 and QJ0158-4325.
- **J0530-3730 (quad, 1.04″):** only one fitted component matches (MER has a single blended entry), so this one is partial.
- **DESJ0501-4118 (literature 3.72″):** neither fitted component matches a MER source (0.24″ and 1.04″ away). The panel (`png/known_DESJ0501-4118.png`) shows the fit straddling the lens galaxy and one image. This is not a recovery of the lensed pair.
- **Not a chance match.** Unlensed parent quasars brighter than VIS 19 are flagged at 2/57 (3.5%), and those fainter than 19 at 0/606. Flags on known lenses are therefore not chance. But for systems wider than 1.5″, extra structure (the lens galaxy or other images) in the ±2″ box makes some flag almost inevitable.
- **The same pattern** appears in the ECLIPSE-A set: L005653 is flagged at 0.73″ against a literature 2.18″, and L017819 at 0.18″ against 1.80″.
- **Strict P1** (components within 0.2″ of literature or MER image positions) is 4/9, or 5/9 counting J0530. As graded it is 6/9.

**Recommended v2 change.**
- Make P1 eligibility 0.3″ ≤ literature separation ≤ the window maximum.
- Score a recovery only when the fitted components match image positions (for example within 0.2″ or 0.2 × separation).
- Report wide systems separately.
- Bring in the arXiv:2206.07714 tables to raise N_known.

### F7 (W). P6 PASS is an operating-point artefact; a tuned baseline beats the detector at science-grade false-claim rates

**Evidence** (`a11_experiments.py base`, `a11_baseline_sweep.csv`; post hoc, scored with the key after the authors' grading). Sweeping the photutils detection threshold on the 472 blind files:

| photutils threshold | Baseline recall | Baseline false-claim rate | Ours at the same false-claim rate |
|---|---|---|---|
| 1.5σ (frozen) | 91.5% | 28.8% | 100% (T_b = 229) |
| 20σ | 94.7% | 3.7% | 97.9% at ≤ 3% |
| 50σ | 93.6% | 1.3% | 84.0% at ≤ 1% |
| 100σ | 93.6% | 0.8% | 80.9% at ≤ 0.79% (≈ T*) |

Stratified bootstrap of the recall difference (ours minus baseline) at matched false-claim rate, 2,000 resamples (`a15_followups.py`):

| Baseline threshold | False-claim rate | Difference | 95% interval |
|---|---|---|---|
| 100σ | 0.8% | −9.6 pts | [−21.3, +2.1] |
| 50σ | 1.3% | −2.1 pts | [−18.1, +6.4] |
| 20σ | 3.7% | +3.2 pts | [0.0, +8.5] |

At false-claim rates of 1% or lower, the ordering is **unresolved** (378 unplanted files means about 3 allowed false claims). The frozen P6 PASS at 29% says nothing about the science operating point. Under the PREREG's own logic ("a P6 failure means the simpler baseline is used going forward"), the baseline would probably be preferred. This is a post hoc sweep on the blind set, so it is a warning, not a verdict.

**Recommended v2 change.** Use a larger unplanted set. Pre-register the baseline's threshold family and tune it on dev tiles. Compare full ROC curves and grade P6 at a pre-registered false-claim rate (≤ 1%), not at the baseline's own point.

### F8 (W). Blinding: the timeline is clean, but the design leaks

**Evidence** (`a9_blind_leak.py`; git log; file times).
- **Timeline and code paths are clean:**
  - The freeze commit 946c26f is at 16:23:47.
  - The key and blind files were written at 16:27:22–16:27:29, and `blind_results.csv` at 16:28:53.
  - After 946c26f, the code diff is only report text in `grade.py` and the `inj_` column rename in `run_main.py` (the detection code is untouched).
  - `seal.py` prints only a count. No code besides `grade.py` opens `key.json`, and `stage_blind` reads only the `.npz` files.
  - I found no evidence that the key influenced any threshold or code.
- **Leak path.** The unplanted blind files are bit-identical to the cached raw cutouts sitting in the same cache. Comparing each blind file with the cached cutouts of blind-pool sources in its tile recovers the planted flag for **472/472 files (94/94 planted, 378/378 unplanted)** and the source id for 472/472, without the key.
- **Weaker channels.** The plants are anchored on the detector's own single-fit position and flux. The injection stage was re-run after the key existed (A8), although with frozen code.
- **Conclusion.** Blinding currently rests on process discipline in one agent session, not on structure.

**Recommended v2 change.**
- Seal in a separate process or session whose output is the only input the detection process can read: the detection sandbox gets no raw-cache access.
- Perturb every blind file the same way (an independent noise realisation, or re-rendering), so unplanted files are not bit-identical to the archive.
- Publish blind-file hashes and a hash commitment of the key before detection.
- Run P2/P3 injection before sealing.

### F9 (M). Injection realism: reusing the same PSF is not a material optimism at T*, but the deflectors inflate completeness

**Evidence.**
- **Same PSF vs real star** (`a12_realstar_B.py`, 880 matched draws at 0.4/0.6/1.0″ × ratio 1/2/5). Image B rendered from a real, unflagged single star in the same tile (shifted, background-subtracted, carrying its own colour, position and noise) gives completeness 0.607, against 0.610 with the tile PSF. The P2-like subset gives 0.643 against 0.646.
- **Same PSF vs another tile's PSF** (`a11_experiments.py xpsf`, 600 draws): 0.605 against 0.603. At this T*, detection is limited by companion flux, not by PSF fidelity. That would no longer hold at a lower, F1-corrected threshold. The null side, where synthetic singles share the PSF, is where reuse matters (F2).
- **Deflector only** (`a11_experiments.py defl`, 320 trials with no image B, same geometry). 6.2% are flagged overall, rising to 11% and 10% at the 1.0″ and 1.5″ geometries. The "with deflector" completeness gain (75% vs 38% at 1.5″) is therefore partly the galaxy being detected or pulling the fitted separation inside the window. All 10 wrong-geometry P2 detections carry a deflector.
- **Not modelled:**
  - source Poisson noise;
  - image colour differences and microlensing or time-delay flux anomalies;
  - extended quasar hosts or arcs;
  - injection beside real hosts with companions (the hosts were selected undetected).

**Recommended v2 change.** Add deflector-only null trials and geometry scoring to P2 and P5. Add Poisson noise. Include an empirical-star-B arm. Draw deflector magnitudes from a lens-galaxy population model conditioned on separation.

### F10 (M). Smaller points

- **PSF-stack contamination.** None of the 1,199 PSF stars appears in the stars, parent or blind-pool samples, as PREREG 3.4 requires.
- **Sample sizes.** P1 window 4/4 has a confidence interval of 40–100%, and the blind set is 472 files with 94 planted, so P5 recall has about ±8 pts of uncertainty. Neither near-miss is decisive.
- **The A6 numbers came from dev tiles.** The report reuses "ratio 20–40 at 0.7–0.8″" for the main run, where the observed companions differ (F1).
- **The REPORT says P4b's 7.21% "is an upper bound".** Given F4 it is not a valid bound in either direction.
- **The parent sample is 705, not 1,500 (A5).** Injection hosts are drawn with replacement from 663 valid, undetected hosts, so trials are correlated through shared hosts. Bootstrap by host, not by trial.

## Does the authors' explanation hold?

**Partly.** The claim that real faint companions in "clean" Gaia stars set T* is supported: 8 of the top 11 have catalogue-confirmed counterparts, 2 more look double, and 1 is a pipeline failure. Their rate matches chance projection (0.51% predicted vs 0.55% observed). Their characterisation (ratio 20–40 at ~0.8″) is wrong for the main run. They also miss the bigger implications:

- the P4 real "false alarms" are mostly true doubles;
- the frozen thresholds cannot all be met by any T threshold;
- the two PASSes on P4 and P6 are artefacts.

The FAIL verdict is valid under the letter of the pre-registration. Its P2 and P4 parts say little about the detector, because the null was contaminated. Its P3 part points to a real weakness of the statistic at 0.3–0.4″ (F3).

## Must-fix list for a pre-registered v2

1. Redefine the null as catalogue- and NISP-verified singles. Report the astrophysical neighbour rate separately. Calibrate T* on real objects only, with no noiseless same-PSF synthetics in the pool.
2. Add a feasibility gate on dev tiles: show that one threshold meets P2 and the real-object false-alarm rate together before freezing. Otherwise grade completeness at a fixed real false-alarm rate (ROC-based).
3. Grade P4 on the real held-out rate; report synthetic separately.
4. Calibrate the noise model: add the Poisson term and a mismatch term set so reduced χ² ≈ 1. Re-test T at 0.3–0.5″ on dev tiles before freezing.
5. Validity gates: reject exact-zero or masked pixels in boxes and PSF stamps, reject f1 ≤ 0 fits, and add PSF centroid, negativity and FWHM checks.
6. Query all DR1 MER tables, and bound flux predicates on both sides (NaN rows). Re-derive N_known; add the arXiv:2206.07714 tables.
7. Score P1, P2 and P5 recoveries on geometry. Bound P1 eligibility to the detection window. Add deflector-only null trials.
8. Pre-register a tuned baseline and compare at a pre-registered false-claim rate of 1% or lower.
9. Blinding: separate the sealing process, perturb every blind file the same way, keep the raw cache away from the detection process, publish hash commitments, and finish injection before sealing.
10. Move the window bound off the 1.5″ grid point (or widen it to 2″). Bootstrap by host.

## Chance-projection rate (A8)

This uses `a8_chance_rate.py` and `a8_chance_by_tile.csv`. Densities come from 3′ cones at the tile centres, using `wide_mode` for tiles 102090830, 102092269 and 102139830. Tile 102153718 is excluded (data hole at its centre) and 102092269 is dropped (zero rows at its centre even in `wide_mode`). Only finite `flux_vis_psf` values are counted. The figures are star-weighted chance probabilities over 0.15–1.5″:

| VIS limit | Chance probability |
|---|---|
| < 21.5 | 0.40% |
| < 22.0 | 0.51% |
| < 22.5 | 0.66% |
| < 24.5 | 2.25% (vs the authors' 7.21%) |

The observed in-window flags at T* are 0.55% on clean stars and 0.85% on all proper-motion stars.
