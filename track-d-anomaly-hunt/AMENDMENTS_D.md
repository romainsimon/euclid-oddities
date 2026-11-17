# Probe D0 amendments

Each entry: date, label (pre-registered deviation from the spec / planned fill-in / post hoc), what changed, why.

## A1 (2026-11-13, pre-registered deviation from the spec, before any pixel) Separate raw cache
The spec puts raw responses in Probe 0's shared cache `E:\claudestronomy-cache\raw`, written through Probe 0's `manifest.py`. That module writes its manifest relative to its own file (so importing it in place writes into Probe 0's worktree) and appends to the shared `index.jsonl` with an in-process lock only, while Probe 0 is still running. Track D therefore uses a copy of `manifest.py` (attributed) with its own cache root `E:\claudestronomy-cache\trackd\` (`raw\`, `index.jsonl`) and its own manifest `output/claudestronomy/trackd/probe_d0/manifest.csv`, plus a real cross-thread limiter (1.5 requests/s total). Probe 0's code is read, never imported in place or written.

## A2 (2026-11-13, pre-registered deviation from the spec, before any pixel) Artefacts only in the band(s) the instrument would affect
The spec adds every planted feature in all three bands. For cosmic-ray tracks, ghost rings, satellite trails and stacking steps that would turn an artefact into a multi-band source by construction, which biases D3 towards "astrophysics". They are added in one band (cosmic rays: VIS only); the extra spike is added in all three bands. Details in PREREG_D 3.5.

## A3 (2026-11-13, pre-registered deviation from the spec, before any pixel) Development lenses from outside the development tiles
The spec puts 50 grade A lenses in Probe 0's two development tiles; Probe 0 counted 32 grade A lenses in 40 tiles, so two tiles cannot supply 50. They are drawn from the footprint outside the test and development tiles, disjoint from the test lenses (PREREG_D 3.2).

## A4 (2026-11-13, incident, outside the probe) One unscrubbed `claude` invocation
While checking CLI options, the implementing agent ran `claude config list` from its own shell, which still had `ANTHROPIC_API_KEY` set. The CLI treated it as a one-line prompt and answered it (default model), so that single call was most likely billed to the API key rather than the subscription. It is not a probe call, saw no image, and is excluded from every metric; it is reported here and in the final report. From then on `claude` is invoked only through the scrubbed runner.

## A5 (2026-11-13, pre-registered addition, before any pixel) `--no-session-persistence` and `--tools Read`
A scrubbed one-line call left a 196 kB session file under `C:\Users\Romain\.claude\projects`; about 5,000 image calls could put gigabytes on C:. Every call adds `--no-session-persistence`. Claude Code 2.1.323 offers `--tools <list>`, which removes the other built-in tools instead of denying them; it is used if the init record then lists only `Read` (checked on the first image call and recorded below).

## A6 (2026-11-13, clerical correction before any pixel) Cutout request radius
PREREG_D 3.3 gives `POS=CIRCLE,ra,dec,0.00889` and calls it "32″ diameter"; 0.00889° is 32″ as a radius, i.e. a 64″ cutout (four times the bytes). The intent stated in the same line and in the spec (32″, about 326 pixels) is kept: the radius is 0.00458° (16.5″, about 330 pixels square), cropped to the central 320×320 as frozen.

## A7 (2026-11-13, observation, no rule change) Pool outcome
The frozen tile draw gave 8 test tiles, but tile 102139830 has no rows in `dr1.mer_catalogue_wide_survey` (count 0), so the test pool comes from 7 tiles: 12,032 objects after the edge and Gaia-mover cuts (spec planning figure about 20,000). `merging_merger` is 0.0 at most (checked on one tile and over the whole pool), so no object reaches 0.5 and the known-merger set is skipped and logged, as the spec allows. Total test objects: 600 + 600 + 850 + 200 + 9 = 2,259. Run B's 91 merger slots go to S_R (PREREG_D 3.10).

## A8 (2026-11-13, operational clarification before any pixel) Catalogue-score flux columns
PREREG_D 3.2 says "VIS, Y, H template-fit fluxes"; the catalogue has no VIS template-fit flux, so VIS uses `flux_detection_total` (the VIS detection flux) and Y, H use `flux_y_templfit`, `flux_h_templfit`.

## A9 (2026-11-13, operational clarification before sealing) Colour reference for the `brighter_in` check
PREREG_D 4 (d) uses "the tile's median pool-galaxy fluxes". `measure.py` must work without the key, and the tile of a neutral name is sealed, so the reference ratio is the median Y/VIS and H/VIS 3″-aperture ratio over S_R and host centres pooled across the test tiles (`tables/typ_pooled.json`). The MER mosaics share one flux scale, so the tile-to-tile difference is expected to be small.

## A10 (2026-11-13, operational clarification before sealing) Extra-spike angle
"An angle not on the cutout's existing spike axes": the spike axes are not measured per cutout; the planted spike's angle avoids ±10° around 0°, 45°, 90° and 135° in the array frame.

## A11 (2026-11-13, planned fill-in before sealing) Model identifiers and tool restriction
Init records from scrubbed calls: alias `haiku` → `claude-haiku-5-5`; alias `sonnet` → `claude-sonnet-5-5`; Claude Code 2.1.323; `apiKeySource: none`. With `--tools Read` the init record lists only `Read` (checked on a real image call), so the flag is used on every call (A5). Every call asserts the pinned id. One image call measured about 11,600 input tokens (7,200 cache read, 4,400 cache write) and 1,260 output tokens, about a quarter of the spec's 50,000 because the other tools are no longer loaded.

## A12 (2026-11-13, operational note) Quota meter includes other sessions
The quota rule (PREREG_D 3.7) reads the account-wide `seven_day.utilization`. It also moves with this agent's own session and with the Probe 0 agent working in parallel (0.38 → 0.40 in the first hour with no probe image calls), so the 0.20 budget is conservative for the probe itself.

## A13 (2026-11-13, realism check result, before sealing) Injector kept
50 open-key examples on separate development hosts (`E:\claudestronomy-cache\trackd\realism\`) were reviewed by a fresh agent session (Claude Sonnet via a Claude Code subagent; not an inspector, never shown test data). It judged 2 of 50 "pasted": a level-160 streak (ruler-straight, uniform, sharp ends) and a level-160 identical pair (the copied segment's hard threshold edge visible in the colour tile); 2 borderline (a level-80 checkerboard with crisp cells, a level-80 spike that looks drawn). The frozen limit is more than 10, so the injector is not changed. Its other remarks are reported as weak points: ghost rings are thin and perfect; single-band steps, trails and clouds look very saturated in the colour tile and have razor edges; spikes are attached to compact galaxies rather than bright stars; several level-40 items were not visible to the reviewer (expected for extended features at integrated SNR 40). Bright pairs and streaks may therefore be easier to spot than real ones, which would inflate D1 for those classes; D2b (shams) does not measure this.

## A14 (2026-11-13, planned fill-in before sealing) Development results and frozen choices
Development set (300 objects, open key; 900 calls: R1 300, ZA 300, Z2 second calls 300, all valid except 1 ZA answer; weekly meter 0.47 → 0.49 over the three runs, mostly other sessions). Results at each rendering's own cut (rule 3.9):

| Rendering | Cut (interest ≥) | Untouched flagged | Bright arc/streak/pair/cloud hit (n=24) | Lenses flagged and located (n=50) | Score |
|---|---|---|---|---|---|
| R1 | 2.6 | 4/150 | 3/24 (12.5%) | 19/50 (38%) | 0.253 |
| ZA | 2.6 | 6/150 | 6/24 (25%) | 20/50 (40%) | 0.325 |
| Z2 | 2.9 | 5/150 | 3/24 (12.5%) | 23/50 (46%) | 0.293 |

Frozen: **rendering ZA**, **flag cut interest ≥ 2.6**, **location tolerance 5″** (8″ gives the same development hit rate, 25%, so the 10-point condition fails). Chance location rate for uniform random positions against the development footprints: 16.6% at 5″, 30.1% at 8″ (the spec's "about 8%" assumed compact features). Prompt wording: `inspect_v1.txt` only (no alternative tried; JSON validity 899/900). Hashes in `prompts/PROMPTS.sha256`. Development objects enter no test metric.

Consequence of ZA for the other runs (fixed by `seal.py` before sealing): runs A, C and E use ZA panels (1280×320); run F and run B use rendering 2 without a zoom tile (the spec defines rendering 2 as three tiles); run D batches use the three R1 tiles.

## A15 (2026-11-13, operational, before sealing) PSF width for tiles without a PSF
The ZA zoom picks "the brightest non-stellar segment", using the tile's VIS PSF width. Lens cutouts come from tiles with no PSF stars fetched; they use the median VIS FWHM of the 10 built tiles (1.95 px). Five of 30 band PSFs failed the 20% held-out FWHM check, mostly because the half-maximum-area FWHM estimator is quantised at VIS sampling (1.60 / 1.95 / 2.26 px steps); as the rule says, they were rebuilt from all stars.

## A16 (2026-11-13, disk management, before sealing) Panels deleted after use, hashes kept
The E: cap (8 GB) does not fit the raw cache (~5.7 GB) plus every rendered panel (~0.7 MB each). Development panels (900 files, hashed in `tables/dev_panels_sha256.csv`) were deleted after the development choice; they can be regenerated from the open-key arrays. Test panels of runs B and F are hashed and deleted after their runs end; run A panels (catalogue images) are kept; runs C, D and E reuse run A's or R1 files through hard links.

## A17 (2026-11-13, post hoc, after sealing, before any test inspection) Raw pool cutouts deleted to stay under the E: cap
After sealing, the probe's E: folder was 8.2 GiB (8.8 GB), above the 8 GB cap (raw 5.0 GiB, panels 2.5 GiB, arrays 0.55 GiB). The raw VIS responses of the 3,195 Pool-R/Pool-C objects that are in no inspected set (used only for the pixel-baseline features, which are already in `tables/pixel_features.csv`) were re-hashed (3,195/3,195 matched their manifest SHA-256), listed in `tables/deleted_raw.csv` and deleted (1.43 GB), as protocol 6A.3 plans for the campaign. Every pixel shown to an inspector is still in the cache. `grade_d.py` (frozen at 6be06a7) was changed in the D15 line only, after sealing, to count these as "verified before deletion" instead of missing; this is labelled post hoc. The pip cache and the smoke-test panel were also removed. Usage after: 6.8 GiB (7.3 GB); run B and F panels are deleted after their runs (A16).

## A18 (2026-11-13, post hoc, run outcome) Quota stop, grader bug fix, empty cache object
- **Quota stop.** Runs A (2,257), C (300) and F (300) completed. Run B (Sonnet) stopped under the frozen quota rule at 476 of 800 calls when the account-wide `seven_day.utilization` reached 0.59 (rule: ≥ 0.58 = 0.38 + 0.20). Runs D (batching) and E (hint) were not started. D6b is computed on the 476 run-B objects answered; D9 and D11 are not available. Run A is complete, so D1–D7 are unaffected.
- **Grader bug fix after unblinding.** The first `grade_d.py` call crashed before computing anything (`run_frame` did not receive the masks: `NameError`). The argument was passed; no rule, threshold or definition changed. A marker file keeps the catalogue step from running twice.
- **Empty cache object.** D15 first showed 59 unverified index entries: all zero-byte responses (unusable cutouts), which share one content-addressed empty file; A17 deleted that file together with an unselected object's empty response. The empty file (SHA-256 e3b0c442…b855, by definition empty) was restored; D15 then verified 12,572/12,572.
- Run F panels were hashed (`tables/panels_sha256_runF.csv`) and deleted after the run (A16); run B panels are still on E: because the driver deletes only after a completed run (E: use 6.6 GiB, under the cap).

## A19 (2026-11-13, post hoc, before any judging) D8 handling
- `grade_d.py --d8` now excludes unjudged cards and reports judged/total, instead of counting them as "not rare". Dry-run on a fake sheet in a temporary folder (deleted); the real cards folder has no sheet.
- Blinding risk for D8: the campaign dashboard lists the 307 run-A flagged objects with the inspector's text and the same panel the cards show, and after grading names arm R or B for the 189 flagged real objects. The judging instructions therefore start with "judge before opening any Track D dashboard entry"; if Romain has already browsed them, D8 is reported as not blind.

## A-judge (14 Nov 2026, before any card was judged; judge_sheet.csv absent or empty)

PREREG_D §4 D8 lists the four choices but not which object on a card is judged. Romain asked on card 1. Rule fixed now, before any answer: the judge classifies the **whole card** by its most notable content, with priority rare known class > cannot classify > artefact > ordinary; when hesitating between two choices, take the more ordinary one. Reason: the inspector was asked about anything in the cutout, so the arms are scored on the whole card. A guide page with development-set examples only (zero overlap with judged objects, checked by object id) is at output/claudestronomy/trackd/probe_d0/judge_examples/index.html. No model output, arm or score is shown in it.

## A-judge (14 Nov 2026, before any card was judged)

PREREG_D §4 D8 lists the four choices but not which object on a card is judged. Romain asked on card 1, before answering any card. Rule fixed now: the judge classifies the **whole card** by its most notable content, with priority rare known class > cannot classify > artefact > ordinary; when hesitating between two choices, take the more ordinary one. Reason: the inspector was asked about anything in the cutout, so the arms are scored on the whole card. A guide page with development-set examples only (zero overlap with judged objects, checked by object id) is at output/claudestronomy/trackd/probe_d0/judge_examples/index.html. No model output, arm or score is shown in it.

## A-mini (14 Nov 2026, before any call): small model comparison, exploratory

Romain asked for a quick, low-quota test of stronger models. `mini.py select` draws 60 run-A objects with SEED_MINI = 20261114: 24 planted arc/streak/pair/cloud at brightness >= 40 (6 per class), 6 planted artefacts at brightness >= 40, 20 untouched S_R, 10 ECLIPSE grade A lenses. The same files, rendering (frozen ZA), prompt (v1) and scoring rules as run A are sent to claude-sonnet-5-5 (run MS) and claude-fable-5-2 (run MF), and Haiku is scored on its existing run-A answers for the same objects. Reported only: no PASS/FAIL. Read-out rule fixed now: a larger, pre-registered run of a model is worth doing if it finds at least 12 of the 24 planted oddities (Haiku's rate on the full set is 18%) without more than 4 of 20 false features on untouched images. Quota stops: Sonnet stops if the seven-day window reaches 0.72; Fable stops if any non-seven-day window reaches 0.40 (Romain reported Fable at 21%).

Disclosure: while writing mini.py the agent printed the header and the first row of sealed/key.csv and names.csv (one untouched S_R object and its run-A name). No planted row was seen. Recorded here; that object is not excluded.

## A-fable (17 Nov 2026, before any call): Fable pass on fresh sky, exploratory

Romain asked for a deeper Fable search capped at 10 points of weekly quota. Code: `fpass.py`. Nothing here changes Probe D0's pre-registered metrics or touches the sealed key.

1. Selection (no model): 4 random DR1 tiles from Probe 0's random list never used by Probe D0, drawn with SEED_FP = 20261117 (one returned no catalogue rows). Same catalogue cuts and Gaia mover removal as the Probe D0 pool, ranked by the Pool-C isolation-forest score. The first 300 usable objects in rank order, plus 15 random controls from below rank 360.
2. Rendering A/B on the open development key: 24 planted arc/streak/pair/cloud at brightness >= 40 and 16 untouched development objects (SEED_FP + 1), each shown to Fable twice: arm ZA (frozen rendering, prompt v1) and arm BG (the same four tiles in a 2x2 grid at 536 px per tile, prompt `inspect_scan.txt`, which asks to scan the whole tile quadrant by quadrant). Scoring as Probe D0: flag cut interest >= 2.6, tolerance 5 arcsec with the injection mask. Rule fixed now: the main pass uses BG if BG finds at least 3 more of the 24 than ZA and has at most 2 more false features on the 16 untouched; otherwise ZA.
3. Main pass: the 300 ranked objects, the 15 random controls and 15 further untouched development objects, shuffled, in the chosen arm (330 calls). The recall measured in step 2 is this pass's recall.
4. Quota stops: weekly window 0.93 or more than 0.20 above its start, any other window (the Fable meter) 0.45, and a hard ceiling of 410 Fable calls in total (about 7 points measured on A-mini).
5. A lead is a fresh-sky object with interest >= 3.5, nature known_rare_class or cannot_explain and confidence medium or high. Leads are then checked without the model: position against SIMBAD, NED and ECLIPSE (5 arcsec), Gaia stars and diffraction spikes, and presence of the feature in both VIS and NISP. Leads that survive are reported as "leads that survived fixed checks", never as discoveries.

Note (17 Nov 2026, 06:45 UTC, before any result was graded): the dev run stopped after 3 calls by the quota rule, because Romain's own use had taken the weekly window to 0.98 and the Fable meter to 0.45. The pass resumes after the 08:00 UTC reset with stricter stops: the weekly window at 0.10 absolute in the new week (Romain's own use included) and the Fable meter at 0.12. The 3 answers already recorded are kept. Steps and rules above are unchanged. Triage code: `ftriage.py`.

Note 2 (17 Nov 2026, 06:52 UTC, before the resumed calls): Romain asked to use the rest of the old week before the reset. Calls now run until the weekly window reads 0.99, then pause until 08:03 UTC and continue under the post-reset stops above (0.10 weekly, 0.12 Fable meter). The status "allowed_warning" no longer pauses the runner. Rules and selection unchanged.

Note 3 (17 Nov 2026, 06:58 UTC, during the dev run, before any grading): Romain asked to stop at the reset and allowed 100% of the old week before it. No call starts after 07:59 UTC (runner deadline, plus a watchdog that stops the runner at 07:59:30); the post-reset continuation is cancelled. The weekly stop before the reset is removed (rate-limit rejection is the limit). Whatever is done by then is graded with the rules above.

## A-twostage (17 Nov 2026, before any call): wide field first, then an independent close look, exploratory

Code: `ftwo.py`. Open development key only (two development tiles); nothing touches the sealed key.

1. Fields: 16 fields of 107 x 107 arcsec (1072 px, native 0.1 arcsec/px) centred on development-pool positions drawn with SEED_TW = 20261118, at least 130 arcsec apart, with <= 2% bad pixels. 12 fields get two planted arc/streak/pair/cloud each (24 plants, levels 40/80/160 in turn, one per half of the field), 4 stay untouched.
2. Stage 1: Fable 5.2 (effort high) sees the whole field as one grey VIS image (prompt `inspect_list.txt`) and lists at most 8 points.
3. Stage 2: every listed point is cropped to a 32 arcsec cutout, rendered as the 2x2 BG grid and sent to a new, independent Fable 5.2 call (effort high, prompt `inspect_scan.txt`, no stage-1 label shown).
4. Scoring as Probe D0: a plant counts as found when a stage-2 answer with interest >= 2.6 points within 5 arcsec of it (injection mask included). Reported: stage-1 recall, final recall (of 24), flags with a feature in the 4 untouched fields, flags away from plants in planted fields. Reference: the one-cutout BG view found 14/24 with 3/16 false features.
5. Read-out rule fixed now: the two-stage search is worth scaling to real sky if it finds at least 12 of 24 with at most 1 flag per untouched field on average.
6. Quota: weekly window may rise by at most 0.05 over this test, the Fable meter is capped at 0.20, and calls stop at either.
