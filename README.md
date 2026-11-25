# Euclid Oddities: looking for the unexpected in Euclid DR1 with Claude

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.24304792.svg)](https://doi.org/10.5281/zenodo.24304792)

Romain Simon, independent researcher, Antibes, France. November 2026.

**Browse every object the model flagged, with blind second opinions: [spacesim.co/euclid-oddities](https://spacesim.co/euclid-oddities).** The gallery is part of [SpaceSim](https://spacesim.co), a free browser universe simulator.

Euclid DR1 became public on 12 November 2026. Many teams will run dedicated machine-learning detectors on it, each looking for one kind of object. This project tries the opposite: a vision-language model (Claude) looks at survey images and flags whatever looks odd, including things that no targeted search is looking for.

The hard part is knowing when to trust it. So every test hides planted fakes under a sealed key (arcs, straight streaks, identical pairs, diffuse clouds, shapes with no physical meaning, and five kinds of instrument artefact), mixes in known objects without labels, and fixes its pass and fail thresholds in a pre-registration before any model sees an image.

## Results so far

### Open-ended anomaly hunt (Track D), Claude Haiku 5.5, about 2,500 Euclid cutouts

| Check | Result | Threshold fixed in advance | Verdict |
|---|---|---|---|
| Planted oddities found and located (brightness ≥ 40) | 17.9% (43/240) | ≥ 70% | FAIL |
| Known ECLIPSE grade A lenses found and located | 31.5% (63/200) | ≥ 60% | FAIL |
| Specific false features on untouched cutouts | 9.0% (54/600) | ≤ 10% | PASS |
| Planted artefacts explained as astrophysics | 6.7% (8/120) | ≤ 20% | PASS |
| Descriptions consistent with pixel measurements | 58.5% | ≥ 80% | FAIL |
| Test-retest agreement (Cohen's κ) | 0.72 | ≥ 0.6 | PASS |
| Inspector beats a pixel-score control on a 1% spiked pool (top 50) | +3.2 points [−2.0, +8.0] | interval excludes 0 | INCONCLUSIVE |
| Real sky, four arms, blind human judge | not done | reported | PENDING (needs an expert judge) |

Verdict under the pre-registered rule: Haiku does not run as a search. It rarely invents things, but it misses most of what is there. Full report: [track-d-anomaly-hunt/REPORT.md](track-d-anomaly-hunt/REPORT.md).

### Stronger models, same 60 sealed objects (exploratory)

| | Haiku 5.5 | Sonnet 5.5 | Fable 5.2 |
|---|---|---|---|
| Planted oddities found | 2/24 | 8/24 | 9/24 |
| Known lenses found | 5/10 | 4/10 | 5/10 |
| False features on untouched images | 3/20 | 2/20 | 4/20 |
| Planted artefacts called astrophysics | 0/6 | 0/6 | 1/6 |

Stronger models find about four times more planted oddities without inventing more, but still miss about two thirds. When they flag a planted item they almost always locate it correctly, so the bottleneck is noticing, not localisation. The read-out rule fixed before the calls (≥ 12/24) is not met. Details: [track-d-anomaly-hunt/MODEL_COMPARISON.md](track-d-anomaly-hunt/MODEL_COMPARISON.md).

### A larger view helps: Fable 5.2 on the development set, then on fresh sky (17 Nov 2026, exploratory)

Rules written and published before the calls: amendment A-fable in [AMENDMENTS_D.md](track-d-anomaly-hunt/AMENDMENTS_D.md).

| Rendering shown to Fable 5.2 | Planted oddities found (of 24) | False features on untouched (of 16) |
|---|---|---|
| Frozen strip of four 320 px tiles, prompt v1 | 9 | 2 |
| 2×2 grid at 536 px per tile, prompt asking to scan every quadrant | **14** | 3 |

The larger view passes the read-out bar (≥ 12/24) for the first time. Small samples: the arms differ by 5 objects.

The larger view was then run on 117 catalogue outliers from three DR1 tiles never used before (stopped by the weekly quota). Fable flagged 23. One met the strict lead definition: an S-shaped tidal stream attached to a disc galaxy, most likely an interacting pair; no SIMBAD entry and only WISE detections in NED. Four low-confidence possible lensing arcs and one small ring are not in ECLIPSE and need an expert look. Details: [fable-pass/FPASS.md](track-d-anomaly-hunt/fable-pass/FPASS.md).

### Compact lensed quasars (Track A), classical fit with injections

A one-versus-two point-source fit on Euclid VIS cutouts of Gaia quasar candidates.

- Probe 0 (40 tiles): known lensed quasars 6/9 recovered, injection completeness 69.5%, 50% completeness at 0.44″. FAIL on recovery, completeness and the blind planted set. [REPORT_probe0.md](track-a-lensed-quasars/REPORT_probe0.md), red-team challenge in [CHALLENGE_red_team.md](track-a-lensed-quasars/CHALLENGE_red_team.md).
- Feasibility gate for a revised detector (48 rules written before evaluation): the best rule recovers 97.4% of injected pairs and reaches 50% completeness at 0.20″, but false alarms on 11,858 verified single stars are 0.24% (bar ≤ 0.1%) and isolated galaxies are taken for pairs 14.4% of the time (bar ≤ 5%). Verdict: not feasible with the visible band alone. About 0.2% of catalogue-single stars appear to have real faint companions. [feasibility-gate/SUMMARY.md](track-a-lensed-quasars/feasibility-gate/SUMMARY.md).

Both tracks are published as null results with their sensitivities.

### Radio sources with no Euclid counterpart (Track R), measurements only

Compact, isolated RACS-mid radio sources (peak >= 5 mJy/beam) were matched to Euclid DR1 by forced photometry on the VIS and H mosaics at the radio position. No language model takes part in the selection. Rules were tuned on one 10 x 10 degree region and published before the rest of the sky was measured.

- 10,021 sources in the sample, 5,791 with usable and deep enough Euclid data, 227 kept: below 3 sigma in both bands, confirmed compact by RACS-high, and free of data faults in an image check by Claude Fable 5.2. 108 are empty in both bands, 119 show a barely visible host.
- Literature check (20 Nov 2026): none of the 227 is in seven published lists of distant radio galaxy candidates or infrared-faint radio sources that could be checked; SIMBAD attaches no dedicated paper to any; no known pulsar within 30 arcsec; no redshift known.
- This is a known class of object. The list is a set of unverified candidates, not a discovery, and most such sources with a measured redshift lie at z = 2 to 4.

Rules, counts, table, images and code: [track-r-radio-dark/RESULTS.md](track-r-radio-dark/RESULTS.md).

### Faint white dwarf candidates that moved (Track M), measurements only

Proper motions of Euclid DR1 point sources absent from Gaia, from Euclid positions against Legacy Surveys DR10 positions about eight years earlier, over about 1,650 deg2. No language model takes part in the selection. Rules were tuned on one 10 x 10 degree region and published before the rest of the sky was read.

- 44,602 sources moved by more than 30 mas/yr; 9,407 are white dwarf candidates by reduced proper motion (5.7 per deg2, median r = 22.3). The same cuts on extended sources predict at most 23 false ones.
- 143 of them show a near-infrared deficit against a blackbody and pass a pixel check. The reversed rule selects 89 sources, so part of the list is scatter. A check made after the results were read shows the blackbody is a biased reference for the reddest sources: against sources of the same colour, 102 remain and 49 are firm in two colours. None is in SIMBAD.
- Second stage (25 Nov 2026): every candidate fitted with white dwarf model atmospheres in seven bands, after calibration and tests on 3,364 Gaia white dwarfs. 41 candidates cannot be fitted without strong collision-induced absorption by molecular hydrogen (34 with a near-infrared deficit that is clear whatever the composition); 23 of them were among the 143. Noise alone, simulated, produces none. Five known Gaia white dwarfs show the same signature and are not attached to any paper on such objects in SIMBAD. The gallery now shows the 41.
- Known classes of objects, at the expected density. All entries are unverified candidates: no spectrum, no parallax.

Rules, counts, tables, images and code: [track-m-moving-faint/RESULTS.md](track-m-moving-faint/RESULTS.md) (first stage) and [track-m-moving-faint/RESULTS_M2.md](track-m-moving-faint/RESULTS_M2.md) (second stage).

## What is in this repository

| Folder | Contents |
|---|---|
| `track-d-anomaly-hunt/` | Pre-registration (`PREREG_D.md`, SHA-256 in `PREREG_D.sha256`), every amendment with its reason, the full report, the model comparison |
| `track-a-lensed-quasars/` | Pre-registration and amendments (with hashes), Probe 0 report, red-team challenge, feasibility-gate rules and results |
| `track-m-moving-faint/` | Faint white dwarfs beyond Gaia from Euclid against Legacy Surveys motions: rules fixed before the main run (`PREREG_M.md`), results, tables, cutout sheets, code |
| `track-r-radio-dark/` | Rules fixed before the main run (`PREREG_R.md`), results, candidate table, image sheets, literature answers, code |

Pre-registration hashes:

- `PREREG_D.md`: `54984a3c8ff30804be96fe2b73bbb38196a0b458915e4bf9da4e928a00cfee66` (frozen 13 Nov 2026, before any model call on a test image)
- `PREREG.md` (Track A): `81293f14c38dcd11d7d4ead1f1fddcb5f231b7b09a71ac040c7621c4f5393e38` (frozen 13 Nov 2026, before any pixel was fitted)

Amendments are listed with dates and reasons, including mistakes made during the work (for example, one command that may have used a paid API key, and one accidental view of a single unplanted row of the sealed key).

## How it was done

- Data: Euclid DR1 (ESA Euclid Science Archive, cutout service), Gaia DR3, the Euclid consortium ECLIPSE lens catalogue. No bulk download.
- Models: Claude Code in headless mode, one fresh session per image, only the file-read tool allowed, no coordinates or hints in the prompt. Run on the spare quota of a personal Claude subscription; every call was checked not to use a paid API key.
- Design, code and grading: written by Claude agents (Claude Opus, with Claude Fable 5.2 as advisor), reviewed by a separate red-team session. A separate program is the only reader of the sealed key.
- Human: the author set the goals, approved each step and is responsible for every claim here.

Code will be released separately.

## Limits

- Planted features are synthetic. Recall on real oddities may differ.
- All models tested so far are from one family (Claude), so they may share blind spots. A second model family is the next test.
- The blind human judging of real-sky candidates (D8) needs a judge who knows Euclid images; it has not been done.
- "Unexplained" in this project will mean a lead that survived a fixed list of checks, never a discovery.

## Licence

Text and tables: CC BY 4.0. Euclid data are © ESA/Euclid Consortium under CC BY-NC 3.0 IGO; the ECLIPSE catalogue is CC BY 4.0. This is a non-commercial research project.

## Note on names

Folder and file paths inside the frozen pre-registrations mention `claudestronomy`, the name of the grant programme that prompted this work. They are left unchanged because the files are hashed. This project is independent and is not run by that programme.
