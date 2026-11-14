# A-mini: Haiku vs Sonnet vs Fable on 60 objects (14 Nov 2026, exploratory)

Same 60 sealed objects, same rendering (ZA), prompt (v1), flag cut (interest >= 2.6) and scoring as run A. Rule fixed before the calls (AMENDMENTS_D, A-mini): a larger run is worth it if a model finds >= 12/24 planted oddities with <= 4/20 false features.

| Metric | Haiku 5.5 | Sonnet 5.5 | Fable 5.2 |
|---|---|---|---|
| Planted oddities found (arc, streak, pair, cloud; brightness >= 40) | 2/24 | 8/24 | 9/24 |
| Known ECLIPSE lenses found | 5/10 | 4/10 | 5/10 |
| False features on untouched images | 3/20 | 2/20 | 4/20 |
| Planted artefacts called astrophysics | 0/6 | 0/6 | 1/6 |
| Interest score AUC, planted vs untouched | 0.60 | 0.70 | 0.69 |

Read-out: neither stronger model reaches 12/24, so by the pre-set rule no larger run of either is triggered as is. Both find about four times more planted oddities than Haiku on these objects (Haiku's 2/24 here is below its 18% on the full set; small-sample noise). Misses are failures to flag, not to locate: every flagged planted item but one was located correctly. The interest score separates planted from untouched only modestly (AUC about 0.7), so a model-specific cut would not close the gap.

Cost: 60 Fable calls moved the Fable meter from 0.21 to 0.22; 60 Sonnet calls moved the weekly meter from 0.67 to 0.68. apiKeySource none on all 120 calls; 1 Sonnet answer invalid JSON.
