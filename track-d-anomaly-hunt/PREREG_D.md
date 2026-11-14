# Probe D0 pre-registration: can a Claude inspector be trusted to look for oddities in Euclid DR1 cutouts?

Frozen: 2026-11-13, before any Track D pixel was fetched and before any test-set cutout was inspected. Parent specification: `businesses/claudestronomy/track-d-test-spec.md` in the CEO workspace (status 13 Nov 2026; its metric table is copied verbatim in section 1). Context: `protocol.md` section 6A. Any later change goes to `AMENDMENTS_D.md`, labelled **planned fill-in** (values this file says will be set on the development set before sealing) or **post hoc** (anything else). This file is hashed into `PREREG_D.sha256` and committed before the first pixel request.

The task brief names the files `prereg/PREREG.md` / `AMENDMENTS.md`; the spec names them `PREREG_D.md` / `AMENDMENTS_D.md`. The spec's names are used.

Catalogue-only orientation made before freezing (no pixels, no model call on any image): `TAP_SCHEMA.columns` for `dr1.mer_catalogue_wide_survey` and `dr1.mer_morphology_wide_survey` (591 columns; every column named below exists), `TAP_SCHEMA.tables` (the Euclid TAP has no Gaia table), and one scrubbed-environment `claude -p` text-only call ("Reply with OK", model alias `haiku`): `apiKeySource: none`, model `claude-haiku-5-5`, Claude Code 2.1.323, stream contains a `rate_limit_event` with `seven_day.utilization = 0.38`.

## 1. Metrics and thresholds (copied verbatim from the spec)

| ID | Metric | PASS | FAIL | INCONCLUSIVE |
|---|---|---|---|---|
| D1 | Hit rate on planted arc, streak, pair and cloud, brightness ≥ 40, run A (n ≈ 240) | ≥ 70% | < 50% | 50–70% |
| D1s | Same for the linear streak alone (n ≈ 60) | reported; "named target usable" if ≥ 60% | n/a | n/a |
| D2 | Specific-false-feature rate on untouched S_R, run A (n = 600) | ≤ 10% | > 20% | 10–20% |
| D2b | Sham excess: flag rate on shams minus flag rate on S_R | ≤ 5 points | > 10 points (D1 is then void) | 5–10 points |
| D3 | Astrophysical explanation of planted artefacts, brightness ≥ 40 (n ≈ 120) | ≤ 20% | > 40% | 20–40% |
| D3b | Pooled false-explanation rate | ≤ 25% | > 40% | 25–40% |
| D4 | ECLIPSE grade A lenses flagged and located, run A | ≥ 60% | < 40% | 40–60%, or fewer than 50 objects |
| D4b | Known mergers flagged; known lensed quasars flagged | reported only | n/a | n/a |
| D5 | Measurement agreement on flagged items (all four checks) | ≥ 80% | < 60% | 60–80% |
| D6 | Test–retest: Cohen's κ on the flag, run C against run A | ≥ 0.6 | < 0.4 | 0.4–0.6 |
| D6b | Cross-model agreement on flag and location, run B against run A | reported only | n/a | n/a |
| D7 | Spiked pool, 1,000 seeded resamples. Negatives: all 600 of S_R, the 150 shams and the 200 planted artefacts (so an anomaly score that likes artefacts is penalised). Positives: 10 drawn from planted oddities at brightness ≥ 40 and known lenses (about 1%). Metric: mean precision in the top 50 when ranked by the inspector (run A), minus the better of random order and the pixel baseline on the same pool. This isolates the inspector; the full funnel (pre-filter plus inspector) is what D8 compares. | > 0, 95% interval excludes 0 | < 0, interval excludes 0 | interval includes 0 |
| D8 | Real sky, four arms (R, B, L, F), K = 100 cards each, blind human judge: yield and lift Y(F) − max(Y(R), Y(B)) | reported; "supported" only if the 95% interval excludes 0 | n/a | expected outcome |
| D9 | Hint test: rise in specific-false-feature rate with the leading prompt, run E against run A on the same objects | reported only | n/a | n/a |
| D10 | Rendering: change in D1 and D2 between run F and run A | reported only | n/a | n/a |
| D11 | Batching: change in D1 and D2 between run D and run A on the same objects | batching is adopted for the campaign only if hit rate drops by ≤ 5 points and false features rise by ≤ 3 points | n/a | n/a |
| D12 | Billing guard: `apiKeySource` is `none` | 100% of calls | any other value | none |
| D13 | Isolation: only `Read`, only inside the batch folder | 100% of scored answers | any violation scored | none |
| D14 | Valid JSON answers | ≥ 98% | < 90% | between |
| D15 | Every pixel and table has a manifest row with a matching SHA-256 | 100% | below 100% | none |
| D16 | Cost: tokens per object, calls, wall time, usage-meter change, requests, bytes | reported only | n/a | n/a |

**Overall** (verbatim): Track D enters the campaign **as a search** if D1, D2 and D3 pass, D2b is not FAIL, and D12, D13, D15 pass. If none of D1–D3 fails but at least one is inconclusive: **measurement-only mode**. If any of D1–D3 fails: Track D does not run as a search. D4–D11 are reported and shape the campaign settings; they do not gate it.

These thresholds are design choices made before seeing any answer. They are not derived from data.

## 2. Seeds

| Name | Value | Use |
|---|---|---|
| SEED_D_TILES | 20261130 | choice of 8 test tiles among Probe 0's 40 random tiles |
| SEED_D_POOL | 20261131 | Pool-R draw (a seeded permutation of the pool; first 3,000 usable) |
| SEED_D_SETS | 20261132 | S_R and hosts (a seeded permutation of Pool-R) |
| SEED_D_LENS | 20261133 | ECLIPSE grade A draw (test 200 and development 50, one permutation) |
| SEED_D_DEV | 20261134 | development objects (150 untouched, 100 injected) from the two development tiles; open development key |
| SEED_D_IF | 20261135 | `random_state` of both isolation forests |
| SEED_D_ORDER | 20261136 | run A call order; run C/D/E/F/B subset draws |
| SEED_D_TIE | 20261137 | seeded hash for the final ranking tie-break |
| SEED_D_BOOT | 20261138 | intervals, D7 resamples, D8 bootstrap |
| SEED_D_CARDS | 20261139 | card draw and shuffling |
| Test injection seed | drawn by `seal.py` from `os.urandom` at seal time, stored only under `E:\claudestronomy-cache\trackd\sealed\` | class, level and geometry of every planted item; neutral names |

Per-item randomness is derived from `(seed, item id)` with NumPy `SeedSequence`, never from worker order.

## 3. Operational definitions

### 3.1 Tiles and parent pool
- Test tiles: Probe 0's 40 random tiles (role `random` in its `tables/tiles.csv`), sorted ascending, 8 drawn with SEED_D_TILES. Development tiles: Probe 0's two `dev` tiles. Neither is used for anything else here.
- Pool query (Euclid TAP, one per tile): `dr1.mer_catalogue_wide_survey` joined to `dr1.mer_morphology_wide_survey` on `object_id`, `tile_index` = tile, and (`smooth_or_featured_smooth <= 1` or `segmentation_area > 1200`), and `spurious_prob < 0.1` (bounded from above, so NaN rows are excluded). Columns kept are listed in `pool.py`.
- Edge cut (operational, needed for a full cutout): object at least 20″ inside the tile's pixel grid (tile WCS from `dr1.mosaic_product` as in Probe 0's `parent.tile_wcs`).
- Gaia star cut: Gaia DR3 sources from the ESA Gaia archive TAP (`gea.esac.esa.int`, one cone per tile); a pool object is removed if a Gaia source with proper-motion significance sqrt((pmra/pmra_error)² + (pmdec/pmdec_error)²) > 5 lies within 1″.
- Usable cutout: non-empty response in every fetched band, and at most 2% of the central 320×320 pixels NaN or exactly zero. Every draw below is a seeded permutation; unusable objects are skipped and the next one taken; the count skipped is reported.

### 3.2 Samples (sizes from the spec)
- Pool-R: first 3,000 of the SEED_D_POOL permutation of the test pool.
- Pool-C: top 3,000 of the catalogue score D1a (isolation forest, 300 trees, SEED_D_IF, fitted on the whole test pool) on: log10 VIS, Y, H template-fit fluxes, VIS−Y and Y−H (log ratios), log `segmentation_area`, `ellipticity`, log `kron_radius`, `mumax_minus_mag`, `point_like_prob`, `gini`, `concentration`, `asymmetry`, `smoothness`, `moment_20`, `merging_merger`, `smooth_or_featured_artifact_star_zoom`; missing values replaced by the column median. Score = negative `score_samples` (higher = more anomalous).
- S_R: first 600 usable of the SEED_D_SETS permutation of Pool-R. Hosts: the next 850 usable. These need no pixel baseline and are fetched first.
- S_B: top 600 by the pixel score among (Pool-R ∪ Pool-C) minus S_R minus hosts, usable cutouts only.
- Known lenses: ECLIPSE (Zenodo 19654904, the file Probe 0 verified by MD5 `56433fecbdc459046ffe9eca44bb4dcf`) rows with `Expert_Grade == "A"`, sorted by `Unique_Identifier`, permuted with SEED_D_LENS; excluding the 8 test tiles and the 2 development tiles; the first 200 usable are the test set and the next 50 usable the development lenses. Each is fetched from the tile in its own row, centred on `RA_obj`, `DEC_obj`.
- Known mergers: pool objects in the 8 test tiles, not in S_R, S_B or hosts, with `merging_merger` between 0.5 and 1 inclusive, highest first, up to 200 usable. If fewer than 50 qualify, the set is skipped and logged.
- Known lensed quasars: Probe 0's `known.csv` rows with `kept = True` (9), reported only.
- Development set: from the two development tiles' pool (same cuts), SEED_D_DEV permutation: first 150 usable untouched, next 100 usable injected with an open key (all classes, levels spread evenly); plus the 50 development lenses. **Spec deviation fixed here, before any pixel:** the spec places the 50 development lenses in the two development tiles, but Probe 0 counted only 32 grade A lenses in 40 tiles, so two tiles cannot hold 50. They are drawn from the footprint outside test and development tiles, disjoint from the 200 test lenses.

### 3.3 Cutouts
- ESA SAS cutout service, URL form of Probe 0's `cutout.py` with `POS=CIRCLE,ra,dec,0.00889` (32″ diameter), collection MER, tile from the object's own row; one request per band. Bands rendered: VIS, NIR Y, NIR H (`dr1.mosaic_product`, `product_type='DpdMerBksMosaic'`, same tile; one row per tile and instrument/filter chosen as in Probe 0: `DATA_RELEASE` preferred, then latest `creation_date`).
- All bands come on the VIS grid (0.1″/pixel). The central 320×320 pixels (32.0″) around the object's pixel position are used for everything.
- Every response is cached content-addressed under `E:\claudestronomy-cache\trackd\raw` and gets a manifest row (URL, time, SHA-256, bytes) in `output/claudestronomy/trackd/probe_d0/manifest.csv`, through a copy of Probe 0's `manifest.py` with its own cache root (see AMENDMENTS_D A1).
- Network: at most 1.5 requests per second in total to ESA hosts from this probe (Probe 0's fetch stage had finished; its main run still shares the host), 6 connections at most. Anonymous, TLS verification on.
- PSFs for VIS, Y and H, per tile (8 test + 2 development): Gaia DR3 stars with 18 < G < 20, proper-motion or parallax significance > 3, no other Gaia source within 5″; 6″-radius cutouts; each star re-centred by its flux-weighted centroid (sub-pixel shift), normalised to unit sum, median-stacked over at least 8 stars (first 30 by G). Check on held-out stars (one third, seeded): the stack must give a median FWHM within 20% of the held-out stars' median FWHM, else the tile is rebuilt with the held-out stars included and the failure logged.

### 3.4 Pixel baseline (arm B)
`features.py` on the VIS cutout of each Pool-R and Pool-C object (central 320×320): background σ by MAD; segmentation (photutils, 3σ threshold on the image smoothed with a 2-pixel-FWHM Gaussian, 10 pixels minimum, deblended); main segment = the one at or nearest the centre. Features: concentration (r80/r20), asymmetry (180° rotation), smoothness (residual after 0.5″ boxcar), Gini, M20, ellipticity and largest-segment elongation (second moments), number of segments, fraction of flux outside the main segment, VIS−Y and Y−H aperture colours (3″ diameter, log ratios) where Y and H exist (else median). Isolation forest (300 trees, SEED_D_IF) fitted on Pool-R only; score = negative `score_samples`, applied to every object including planted cutouts (after sealing, on final pixels). The optional embedding baseline is not run unless time remains after run A (it is not required).

### 3.5 Injection (`inject.py`, applied by `seal.py`)
Counts as in the spec: arc, linear streak, identical pair, diffuse cloud, nonsense shape 100 each (5 levels × 20); five artefact types × 40 (5 levels × 8); sham A 75 and sham B 75 (5 levels × 15). Hosts receive exactly one item each.

- **Brightness level** = integrated signal-to-noise of the feature inside its own footprint in its reference band: footprint F = pixels where the PSF-convolved model is at least 10% of its peak; SNR = Σ_F model / (σ_band √|F|), σ_band from the host cutout by MAD. Levels 10, 20, 40, 80, 160; "bright" = ≥ 40. Reference band = VIS, except the diffuse cloud (its single band). The model is scaled to the target SNR exactly.
- **Position**: uniform in the central 24″. Arcs, streaks and pairs are attached to the nearest suitable galaxy to that point (segment of at least 80 pixels, not saturated, within the central 24″); if none, a new point is drawn (at most 20 times, then the nearest segment of any size).
- **Colour**: other bands are scaled relative to the reference band by flux ratios in native units: "typical" = median Y/VIS and H/VIS ratio of the tile's pool galaxies (3″ apertures); "bluer than host" = host ratios × 0.5.
- **PSF and noise**: every synthetic model is convolved with the tile's PSF for that band. Mosaics are sky-noise dominated at these levels, so the cutout's own noise is the matched noise; no extra noise is added to synthetic models. Pasted real pixels carry their own noise.
- **Arc**: an elliptical Sérsic source (n = 1, R_e 0.15″–0.4″, axis ratio 0.5–1) lensed by a singular isothermal sphere plus external shear (γ ≤ 0.1) centred on the host galaxy, Einstein radius 0.8″–2.5″, source offset 0.05–0.6 θ_E; only the lensed light is added; colour bluer than host.
- **Linear streak**: thin line of length 3″–15″, intrinsic Gaussian width 0.05″–0.12″ (axis ratio ≥ 20 after convolution is checked; else length is increased), brightness along the line modulated by smoothed noise (clumpy), one end at the host centre, random angle; bluer than host.
- **Identical pair**: the host galaxy's own pixels inside its segment (all three bands) copied and added at an offset of 0.5″–5″ in a random direction; the copy is identical in shape and colour, with flux scaled to the target SNR.
- **Diffuse cloud**: smoothed Gaussian random field (correlation 0.3″) times an elliptical envelope (radius 1″–3″), offset 3″–10″ from a galaxy, in one band only (VIS, Y or H, uniform).
- **Nonsense shape**: hollow square, checkerboard patch, triangle outline, plus sign or concentric squares (uniform), size 1.5″–4″, line width 0.2″, typical colour, free position.
- **Artefacts**, added only in the band(s) where the instrument would produce them (adding a cosmic ray to three bands would make it a source by construction; AMENDMENTS_D A2): cosmic-ray track (VIS only, not PSF-convolved, 0.5″–3″ long, 1–2 pixels wide); ghost ring (one band, annulus radius 1.5″–4″, width 0.2″–0.5″, convolved); satellite trail (one band, straight line crossing the whole cutout, PSF width; its footprint is the part inside the central 24″); stacking step (one band, a background offset over a half-plane whose boundary passes through the central 24″; footprint = a 1″ band along the boundary; SNR computed on that band); extra spike (all three bands, a thin line 2″–6″ long radiating from the nearest compact source at an angle not on the cutout's existing spike axes, convolved).
- **Sham A**: a real ordinary galaxy (segment pixels, three bands) cut from another host's cutout in another tile and pasted at a free position, scaled to the target SNR. **Sham B**: a single Sérsic (n 0.5–4, R_e 0.2″–1″, axis ratio 0.3–1), typical colour, free position, same convolution path.
- **Location truth**: the footprint mask (VIS, or the cloud's band) plus its flux-weighted centroid.
- **Realism check**: before sealing, 50 open-key examples (all classes, seeded, separate draw from development hosts, never reused) are shown to a fresh agent session that is not an inspector and that is asked which look pasted or cartoon-like. If more than 10 look pasted, the injector is fixed and the check repeated.

### 3.6 Rendering
- Tile: central 320×320 pixels, 1:1, no resampling. σ per band by MAD over the cutout.
- Rendering 1 (960×320): left VIS, `asinh(x / (3σ))` mapped from −1σ to the 99.7th percentile; middle colour R = H, G = Y, B = VIS, each band `asinh(x / (3σ_band))` scaled by the 99.7th percentile of the maximum over bands; right VIS `asinh(x / (0.5σ))` mapped from −0.5σ to the 98th percentile.
- Rendering 2: soft stretch `asinh(x / (2σ))` to the 99.5th percentile, hard `asinh(x / (0.8σ))` to the 97th; every tile mirrored left–right then rotated 90° counter-clockwise; tile order: hard grey, colour, soft grey. Reported positions are mapped back before scoring.
- Development candidates (at most three, chosen by rule 3.9): **R1** as above; **ZA** = R1 plus a fourth tile (1280×320 total) showing a 3× nearest-neighbour enlargement of the 106×106-pixel box centred on the brightest non-stellar segment (segment second-moment size above 1.5 times the PSF's); **Z2** = R1 for a first call, then a second call on R1 plus a fourth tile with the 3× enlargement centred on the position the first call reported; the second answer is the answer.
- File names: 12 random hex characters from `os.urandom`; PNG written by Pillow with no text chunks; metadata check in the tests.

### 3.7 How the model is called
As in the spec ("How the model is called"), plus: `--no-session-persistence` (a single call otherwise writes a session file under `C:\Users\Romain\.claude\projects`, and C: has 10 GB free) and `--tools Read` if the init record then lists only `Read` (else `--allowedTools Read` alone, as in the spec). Environment allow-list: PATH, SystemRoot, SYSTEMROOT, WINDIR, SystemDrive, ComSpec, PATHEXT, USERPROFILE, HOMEDRIVE, HOMEPATH, APPDATA, LOCALAPPDATA, TEMP and TMP pointed at `E:\claudestronomy-cache\trackd\tmp`, CLAUDE_CONFIG_DIR if set, `DISABLE_AUTOUPDATER=1`. Any variable starting with `ANTHROPIC_` or naming Bedrock, Vertex or Foundry is asserted absent.

- Billing guard: the first `system`/`init` record must have `apiKeySource == "none"`; otherwise the runner kills the call, writes an `error` event and stops the whole probe.
- Isolation: answer invalid if any `tool_use` other than `Read` appears, or a `Read` path is outside the call's batch folder.
- Valid answer: the final text contains exactly one JSON object (or, for run D, one JSON array of eight objects) parsing with every field present and in range; `interest`, `weirdness` rounded to one decimal. Invalid answers are not retried; they are scored as not flagged and counted in D14.
- Models: alias `haiku` for runs A, C, D, E, F and development; alias `sonnet` for run B; full ids from the init records written to `AMENDMENTS_D.md` as a planned fill-in before sealing and asserted on every call afterwards. Claude Code 2.1.323, `DISABLE_AUTOUPDATER=1`.
- Pacing: at most 3 concurrent processes; on any rate-limit message or `rate_limit_event` with status other than `allowed`, no new call is started until the reset time (if within 2 hours) or the probe stops cleanly; a call is retried at most twice and only for process or transport errors, never for content.
- **Quota rule.** The runner records `seven_day.utilization` from every call. It stops starting new calls when utilization reaches 0.65, or when it has risen 0.20 above its value at the probe's first call (0.38). Runs are executed in the spec's order (A in seeded random order, then C, F, B, D, E), so a stop leaves a valid random subsample of A. If the projected cost of the remaining runs exceeds the budget after the development set, the later runs (E, D, B, F, C in that order) are shrunk or dropped before run A is touched, and this is logged.

### 3.8 Prompts
`prompts/inspect_v1.txt` (neutral), `prompts/inspect_hint.txt` (leading, run E only), `prompts/inspect_batch.txt` (run D), and `prompts/panels.json` (the panel description for each rendering) are committed and hashed in `prompts/PROMPTS.sha256` before sealing. The neutral prompt says the image shows one patch of sky 32″ wide in several renderings, asks for a description, and asks for one JSON object with the spec's fields; it does not say anything may be planted, names no class in prose, and gives no example. Development may try at most three wordings; the one used is frozen by hash before sealing.

### 3.9 Development rules (frozen now; the numbers are planned fill-ins)
- **Flag cut**: for each candidate rendering, the lowest one-decimal value c of `interest` such that at most 5% of the 150 untouched development objects have `interest ≥ c` (invalid answers count as not flagged).
- **Rendering choice**: for each candidate, at its own cut, compute the development score = mean of (hit rate on bright arc/streak/pair/cloud) and (fraction of the 50 development lenses flagged and located). Choose the highest; Z2 (two calls per object) is chosen only if it beats the best one-call rendering by at least 5 points; ties go to the cheaper and then the simpler (R1 < ZA < Z2).
- **Location tolerance**: 5″, unless 8″ raises the development hit rate on bright arc/streak/pair/cloud by at least 10 points and the chance location rate at 8″ (uniform random positions scored against the development planted footprints) is at most 20%.
- Development objects never enter a test metric. At most 1,500 development calls.

### 3.10 Runs
| Run | Model | Rendering | Prompt | Objects | Calls |
|---|---|---|---|---|---|
| A | haiku | chosen | neutral | all test objects (~2,459), one per call, order a SEED_D_ORDER permutation | ~2,459 (×2 if Z2) |
| C | haiku | chosen | neutral | 300 uniform from A's objects, new names | 300 |
| F | haiku | rendering 2 (plus the zoom tile if the chosen rendering has one, built after the same transform) | neutral | 150 S_R + 150 bright arc/streak/pair/cloud | 300 |
| B | sonnet | rendering 2 | neutral | 800: S_R 150, S_B 100, planted 350 (proportional to class counts), lenses 100, mergers up to 91 (shortfall to S_R), known lensed quasars 9 | 800 |
| D | haiku | R1 tiles, 8 per call | batch | 480 = 240 S_R + the 240 bright arc/streak/pair/cloud; each object in two different batches; batches shuffled | 120 |
| E | haiku | chosen | hint | 200: 100 S_R, 50 shams, 50 artefacts | 200 |

Run subsets that need the key (F, B, D, E) are drawn by `seal.py` with SEED_D_ORDER and written as call lists without labels.

## 4. Scoring rules (from the spec, with operational detail)

- **Flag** = valid answer with `interest` ≥ cut.
- **Ranking** = `interest` desc, then `weirdness` desc, then run C score, else run B score, where one exists, then SHA-256 of (SEED_D_TIE, neutral name).
- **Located** = reported (x, y), mapped to cutout pixels (x · 320, y · 320 in the left tile, undoing rendering 2's transform), lies within the tolerance of the planted footprint (any footprint pixel) or its centroid. Known lenses: within the tolerance of the catalogue position (cutout centre). Chance rate: the same test applied to the reported positions of shams against a footprint drawn for another host, reported.
- **Hit** = flag and located.
- **Specific false feature** = flag on an untouched S_R cutout with `feature` ≠ `none`.
- **Astrophysical explanation of an artefact** = planted artefact, flagged, located, `nature` ≠ `artefact`, confidence medium or high.
- **False explanation (pooled)** = the previous, plus nonsense shapes (flagged and located) with `nature = known_rare_class` and confidence medium or high, plus planted astrophysical classes that are hit with confidence high and a wrong `feature` (correct: arc → arc or ring; streak → straight_line; pair → pair; cloud → diffuse_patch or irregular). Denominator: all flagged-and-located planted artefact, nonsense, arc, streak, pair and cloud items (shams excluded).
- **Measurement agreement (D5)**, on run A flagged items with a valid position (measured by `measure.py` on the exact pixels shown, VIS, 3σ detection, 2-pixel-FWHM smoothing, 10 pixels minimum, deblended): (a) `n_compact_within_3as` within ±1 of the count of segments with centroid within 3″ of (x, y) and second-moment semi-major axis ≤ 0.5″; (b) `elongated` equals (axis ratio of the segment containing (x, y), or nearest within 1″, > 3); (c) if elongated by measurement, `angle_deg` within 25° (mod 180) of the measured angle, counter-clockwise from the tile's horizontal; (d) `brighter_in`: c = log10[(F_VIS/m_VIS)/(F_IR/m_IR)] for the segment's flux, with F_IR = mean of Y and H and m the tile's median pool-galaxy fluxes; unsure zone |c| < 0.2: not scored; outside it the answer must be `optical` (c > 0) or `infrared` (c < 0). D5 = pooled fraction of applicable (item, check) pairs that agree; per-check and all-four-per-item rates are reported. Items with no segment within 1″ of (x, y): checks (b)–(d) count as disagreements.
- **Intervals**: Wilson 95% intervals for proportions; differences of proportions by bootstrap (2,000 resamples, SEED_D_BOOT); κ with bootstrap interval. A verdict compares the point estimate with the thresholds (the spec's table); intervals are reported next to it.
- **D7**: 1,000 resamples with SEED_D_BOOT: negatives = S_R (600) + shams (150) + planted artefacts (200); positives = 10 drawn without replacement from bright planted arc/streak/pair/cloud plus the test lenses. Ranking by the inspector (rule above); random order = seeded shuffle; pixel baseline = arm-B score on the final pixels. Precision in top 50; metric = inspector − max(random, baseline) per resample (the better control is chosen per pool by mean over all resamples, then the difference is computed per resample); interval = 2.5–97.5 percentiles.
- **D8**: arms on the real sky. R = first 100 of a SEED_D_CARDS permutation of S_R; B = top 100 of S_B by the pixel score; L = top 100 of S_R by the inspector ranking; F = top 100 of S_B by the inspector ranking. Duplicates across arms are shown once and credited to every arm that holds them. Cards: rendering 1 tiles (no zoom), new neutral names, shuffled with SEED_D_CARDS; no model text, no arm, no score. Choices: ordinary, artefact, rare known class, cannot classify. The judge's sheet is hashed before the arm labels are joined. Y(arm) = fraction judged rare known class or cannot classify; lift = Y(F) − max(Y(R), Y(B)); bootstrap interval over cards (2,000, SEED_D_BOOT). No model judges the cards.
- **D6**: κ between run A and run C flags on the same objects (invalid answers = not flagged). **D6b**: agreement on flag (κ) and, for objects flagged in both, the fraction with positions within the tolerance after undoing rendering 2.
- **D9**: on the 100 S_R objects of run E, specific-false-feature rate in E minus in A (same objects). **D10/D11**: D1 and D2 recomputed on the run's objects for that run and for run A on the same objects; for D, each object's two answers are both scored (rate over answers).
- **D12–D15** as in the table; D15 is checked by re-hashing every cache object and every output table against the manifest.

## 5. Blinding
- `seal.py` writes the key, the name map and the run call lists under `E:\claudestronomy-cache\trackd\sealed\`, prints counts only, and is run after the prompts, the runner and `grade_d.py` are committed (commit hash recorded in `AMENDMENTS_D.md`). It is run in the same agent session that wrote the code (no separate session was available); that agent does not open the sealed folder afterwards and does not view test panels. `grade_d.py` is the only program that opens the key.
- Inspector sessions see one batch folder of neutral-named PNGs, no coordinates, tile, magnitude, arm or set. The planted fraction is never stated.
- Catalogue (dashboard) entries: flagged objects are added live by neutral name with the inspector's text and panel; planted objects are added and marked with `set_injected` only by `grade_d.py` after unblinding.
- Cards are judged by Romain only; the sheet is hashed before joining.

## 6. Disk and network caps
E: at most 8 GB for this probe (raw cache, arrays, panels, venv excluded since it lives on D:), D: at most 1 GB (venv about 460 MB, code, tables). Nothing on C:. If a cap would be exceeded, sample sizes are shrunk (logged) before any rule is relaxed.
