# Looking for the unexpected in Euclid DR1 with Claude

Romain Simon, independent researcher, Nice, France. November 2026.

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

### Compact lensed quasars (Track A), classical fit with injections

A one-versus-two point-source fit on Euclid VIS cutouts of Gaia quasar candidates.

- Probe 0 (40 tiles): known lensed quasars 6/9 recovered, injection completeness 69.5%, 50% completeness at 0.44″. FAIL on recovery, completeness and the blind planted set. [REPORT_probe0.md](track-a-lensed-quasars/REPORT_probe0.md), red-team challenge in [CHALLENGE_red_team.md](track-a-lensed-quasars/CHALLENGE_red_team.md).
- Feasibility gate for a revised detector (48 rules written before evaluation): the best rule recovers 97.4% of injected pairs and reaches 50% completeness at 0.20″, but false alarms on 11,858 verified single stars are 0.24% (bar ≤ 0.1%) and isolated galaxies are taken for pairs 14.4% of the time (bar ≤ 5%). Verdict: not feasible with the visible band alone. About 0.2% of catalogue-single stars appear to have real faint companions. [feasibility-gate/SUMMARY.md](track-a-lensed-quasars/feasibility-gate/SUMMARY.md).

Both tracks are published as null results with their sensitivities.

## What is in this repository

| Folder | Contents |
|---|---|
| `track-d-anomaly-hunt/` | Pre-registration (`PREREG_D.md`, SHA-256 in `PREREG_D.sha256`), every amendment with its reason, the full report, the model comparison |
| `track-a-lensed-quasars/` | Pre-registration and amendments (with hashes), Probe 0 report, red-team challenge, feasibility-gate rules and results |

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
