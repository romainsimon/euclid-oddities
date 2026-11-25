# Track M, second stage: 41 faint white dwarf candidates that need strong molecular absorption, and 5 Gaia white dwarfs with the same signature

Run of 25 Nov 2026. Claude Fable 5.2 in Claude Code (interactive session, Claude subscription), with Romain Simon. Rules: [PREREG_M2.md](PREREG_M2.md), public before any fit of a candidate was read (commit `98d315d`, 25 Nov 2026, 08:55 UTC). First stage: [RESULTS.md](RESULTS.md).

No language model takes part in the selection. The model looked at the cutouts of the 47 selected sources and removed none beyond the pixel step.

**Every entry is an unverified candidate.** No spectrum. The faint ones have no parallax. Cool and infrared-faint white dwarfs are a known class (about 105 analysed in Bergeron et al. 2022).

## In short

- Each of the 9,407 white dwarf candidates of stage one was fitted with white dwarf model atmospheres in seven bands (g, r, i, z from Legacy Surveys, Y, J, H from Euclid): temperature, distance, velocity across the sky.
- The method was calibrated and tested on 3,364 Gaia white dwarfs in the same tiles. Temperatures agree with the Gaia catalogue within 3 % (median), photometric distances with the parallax distances within about 15 to 20 %.
- **41 candidates cannot be fitted without strong collision-induced absorption by molecular hydrogen**, with two independent flux measurements, clean pixels, and no entry in SIMBAD. 17 of them are "ultracool": every acceptable model is below 4000 K. These 41 replace the 143 of stage one as the list worth attention.
- A simulation of noise alone, with the real errors, produces 0 such sources in five draws of the whole sample.
- Stage one deflates further: of its 143 near-infrared deficit candidates, 23 are among the 41. Most of the others are ordinary cool white dwarfs, whose deficit against a blackbody is what a pure-hydrogen atmosphere gives anyway.
- By-product: **5 known Gaia white dwarfs** (G = 19.1 to 20.3, 68 to 119 pc) meet the same rule. SIMBAD lists them only in catalogue papers. Their parallaxes confirm the distances given by the same models within 2 to 21 %.
- No reliable halo white dwarf comes out of this stage.

## The 41 candidates (`stage2/interesting_candidates.csv`, `stage2/sheets/`)

| Step | Count |
|---|---|
| Candidates fitted | 9,407 |
| Quality (rule G) | 8,186 |
| Strong absorption with the aperture fluxes / with the template-fit fluxes | 74 / 65 |
| Strong absorption with both (rule H) | 47 |
| Rejected: missing pixels within 1.5 arcsec in Y, J or H | 5 |
| Rejected: cutout not obtained | 1 |
| Removed by eye | 0 |
| **Kept** | **41** |

| Class | Count |
|---|---|
| Ultracool: every model within 9 in chi2 of the best is below 4000 K (rule I) | 17 |
| Best model below 4000 K, warmer models not excluded | 3 |
| Mixed hydrogen-helium model at 4000 to 5050 K | 21 |

- Magnitudes r = 20.9 to 23.3 (median 22.5). Distances with the best model 120 to 407 pc (median 252). Velocity across the sky: median 58 km/s, none above 200.
- Best composition: He/H = 100 for 19, 1e5 for 8, 1e8 for 6, pure hydrogen for 8.
- SIMBAD, 10 arcsec cone: nothing for any of the 41.
- NOIRLab Source Catalog DR2 motion: compatible for 40, query failed for 1.
- Stage one status: 14 were in its "firm in two colours" subset, 9 others in its list of 143, 18 were not selected at all. Those 18 are mostly sources whose J band is already suppressed, which the J - H test of stage one could not see.
- One of the 41 has a forced J S/N below 5 on the pixels (row 42). It is kept, because the rules list only missing pixels, and flagged.
- Notes of the eye check (`eye_note`): a bright galaxy 5 arcsec from row 40, a faint neighbour 1.5 arcsec from row 44, a masked area 2.5 arcsec from row 35.

The four strongest cases (rows 0 to 3, r = 20.9 to 22.1) are blue in the optical and collapse from Y to H: no model without strong absorption comes within 190 in chi2.

## The 5 Gaia white dwarfs (`stage2/gaia_strong_absorption.csv`)

They come from the calibration sample (Gentile Fusillo et al. 2021), on which the thresholds were tuned, so they are not a blind result.

| Gaia DR3 | G | Parallax distance (pc) | Distance from the best model (pc) | Best model | Velocity (km/s) |
|---|---|---|---|---|---|
| 6487573599829346176 | 19.78 | 119 | 103 | He/H = 100, 5150 K | 74 |
| 4729108809392699392 | 19.23 | 80 | 78 | He/H = 100, 5100 K | 59 |
| 4727802456435996544 | 20.34 | 112 | 106 | He/H = 100, 4500 K | 47 |
| 4768450851559548672 | 20.30 | 91 | 72 | He/H = 1e5, 3200 K | 83 |
| 4922114228674321792 (LEHPM 1050) | 19.09 | 69 | 67 | He/H = 100, 4850 K | 66 |

- SIMBAD (IDIA mirror, 25 Nov 2026) attaches to them only catalogue and classification papers (Gaia white dwarf catalogues, random-forest classifications). Three carry a "DA" type that comes from an automatic classification of Gaia low-resolution spectra. None is attached to a paper on infrared-faint white dwarfs. We did not search beyond SIMBAD.
- They lie at Dec -52 to -65, south of the Pan-STARRS footprint used by Bergeron et al. 2022.
- They are bright enough for a spectrum on a 4 m class telescope, and they have parallaxes. They are the easiest part of this work to confirm or refute.

## Checks

**Calibration (1,365 warm Gaia white dwarfs).** Optical residuals below 0.01 mag. The Euclid aperture magnitudes are 0.26 to 0.27 mag fainter than the models in Y, J, H (0.07 to 0.09 for template-fit fluxes), with no trend in temperature or magnitude above 0.01 mag; removed.

**Validation (724 Gaia white dwarfs with a good parallax).** Our temperature over the catalogue one: median 1.00 to 1.03 in every bin, scatter 4 to 9 %. Photometric over parallax distance: median 0.88 (22 stars below 5000 K) to 1.06; 16 to 84 % range about 0.88 to 1.24.

**Faint end (rule L).** For the 1,079 warm candidates the median residual is -0.015, -0.023, -0.022 mag in Y, J, H and +0.021 in z. The zero points hold at VIS 20 to 24.

**Noise only (rule L).** Five draws of the 8,186 quality sources from their best ordinary model, with their errors and systematics: 0 strong-absorption sources in each. Gaussian noise does not make this list. Faults that are not Gaussian (blends, artefacts) are what the pixel step and the eye check are for.

**Tails (rule L).** H-band residual against the best ordinary model: 119 sources below -3 sigma, 150 above +3 sigma. A low H alone is therefore not evidence: the excess side is as populated. Rule H asks for more, a specific model that fits all seven bands.

**VIS band, check made after the results were read (`qc.py`, `stage2/vis_check.csv`).** VIS is not fitted and was taken in 2024-25, the optical bands in 2013-19. Observed minus model VIS - r: +0.116 for the whole sample (scatter 0.046), +0.095 for the 41 (scatter 0.063, extremes -0.05 and +0.22). No candidate is more than 0.25 mag from the population. So no sign of a source that faded between the surveys or of a wrong pairing.

## What did not come out

- **Halo white dwarfs.** Rule J flags 62 sources, of which only 6 pass the quality cuts; their median r is 24.2 and 22 of the 24 "above 500 km/s" have a motion above 100 mas/yr. This is the faint, badly measured end of the sample, not a halo population. The count is below the range expected before looking (100 to 2,300), which the conservative distance explains in part. The table is published (`stage2/halo_candidates.csv`) and nothing in it is presented as a find. With the best-fit distance 375 sources exceed 200 km/s, but the validation shows that a 20 % distance error is common, so that number is not a count of halo stars either.
- **Temperatures below 4000 K from simple fits.** 1,177 candidates have a best pure-hydrogen or pure-helium temperature below 4000 K. Only 17 pass rule I. At these temperatures the fit has two solutions and most sources are too faint to choose.

## How interesting is this

Plainly: this is the first part of Track M that a specialist may want.

- About 105 infrared-faint white dwarfs are analysed in the main published sample. 41 candidates and 5 Gaia stars would be a real addition if a fair share holds.
- The 5 Gaia stars are the strongest claim: bright, with parallaxes, and the model distances agree with them.
- The 41 are faint (r up to 23.3). Confirming them needs near-infrared photometry from another instrument or a spectrum on an 8 m class telescope. What Euclid adds is exactly the Y, J, H bands that define the class.
- Limits that a specialist would raise first: the models are not the high-density models of Blouin et al. 2018 used for this class, so the temperatures and compositions are indicative; no parallax for the 41; the two flux types share the same pixels; the thresholds were tuned on Gaia stars.

## Deviations from the plan

- The first absorption thresholds (-0.15 / -0.30) were replaced by -0.40 / -0.50 after the Gaia sample showed that they flagged ordinary pure-hydrogen white dwarfs near 4100 K. This was done before the freeze and is in the rules.
- The parallax error was not fetched; "good parallax" in the validation means parallax above 3 mas and G below 20.
- The source with a forced J S/N below 5 is kept and flagged; the source without cutout is rejected.
- `qc.py` (VIS check) and the columns "distance and velocity with the best model" were added after the results were read. Rule J uses the pure-hydrogen and pure-helium distances, which are wrong for a strong-absorption source; none of the 41 exceeds 200 km/s with either.
- NOIRLab Data Lab was down during part of the run: Legacy Surveys photometry came from the viewer catalogue service.

## Files (`stage2/`)

| File | Content |
|---|---|
| `interesting_candidates.csv` | The 47 strong-absorption sources with verdict (`kept`), class, fit, residuals, fluxes, pixel S/N, SIMBAD, third data set |
| `sheets/strong_absorption_*.jpg` | Cutouts (VIS, Y, J, H) in table order (`row`) |
| `gaia_strong_absorption.csv` | The 5 Gaia white dwarfs |
| `fits_all.csv.gz` | Fits of all 9,407 candidates |
| `halo_candidates.csv` | The 62 sources of rule J (not finds) |
| `vis_check.csv`, `cal.json` | VIS check; zero points and systematics |
| `qd.py`, `qg.py`, `qs.py`, `qm.py`, `qf.py`, `qo.py`, `qp.py`, `qr.py`, `qv.py`, `qc.py` | Data assembly, Gaia sample, model synthesis, fit and rules, summaries, final tables, literature, VIS check |

Models: Warwick white dwarf grids (Tremblay et al. 2011; Kowalski & Saumon 2006; Cukanovaite et al. 2021); Montreal mass-radius tables (Bedard et al. 2020). Filters: SVO Filter Profile Service. Data: ESA Euclid DR1, DESI Legacy Imaging Surveys DR10, Gaia EDR3 (Gentile Fusillo et al. 2021), NOIRLab Source Catalog DR2, SIMBAD.
