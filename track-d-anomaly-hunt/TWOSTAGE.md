# A-twostage: wide field first, then an independent close look (17 Nov 2026, exploratory)

Rules: prereg/AMENDMENTS_D.md, A-twostage, committed, pushed and archived (Zenodo DOI 10.5281/zenodo.24304793) before the first call.

16 development fields of 107 x 107 arcsec (12 with two planted arc/streak/pair/cloud each, 4 untouched). Claude Fable 5.2, effort high, Claude Code headless, subscription (apiKeySource none on all 144 calls). Weekly window 0.02 -> 0.04.

| | Planted found (of 24) | False flags |
|---|---|---|
| Stage 1: one look at the whole 107" field, up to 8 points | 14 | - |
| Final: stage-2 close look confirms (interest >= 2.6, within 5") | 9 | 4 in the 4 untouched fields; 19 away from plants in planted fields |
| Reference: one 32" 2x2 cutout per object (A-fable) | 14 | 3 of 16 untouched cutouts |

By class (final): arc 3/6, cloud 2/6, pair 1/6, streak 3/6. Stage 1 by level: 40: 3/8, 80: 4/8, 160: 7/8.

Read-out rule (>= 12/24 with <= 1 flag per untouched field): not met (9/24). Stage 1 alone matches the one-cutout recall while covering about 11 times more sky per call; the loss is in stage 2, which rejected 5 of the 14 plants stage 1 had found. Not scaled to real sky as is. The 19 off-plant flags in planted fields are either false alarms or real sky features; not yet inspected.

## A-twostage-b: targeted close look (same fields, same 128 stage-1 points)

Stage 2 judged the marked stage-1 point (orange circle) instead of re-searching the crop. Found 7/24 (arc 3/6, cloud 2/6, pair 1/6, streak 1/6; by level 40: 0/8, 80: 1/8, 160: 6/8). Flags: 4 in the 4 untouched fields, 16 away from plants in planted fields. Weekly window 0.04 -> 0.06. Read-out rule not met.

Conclusion across both variants: the close-look verification loses faint plants (it calls them ordinary); stage 1 alone recovers 14/24, the same as one 32" cutout per object, while covering about 11 times more sky per call. Its own false-alarm rate on untouched fields has not been measured yet.
