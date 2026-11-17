# A-fable: Fable pass on fresh sky (17 Nov 2026, exploratory)

Rules in prereg/AMENDMENTS_D.md (A-fable and notes 1-3), committed and published before the calls they govern.

## Rendering A/B on the open development key (Fable 5.2, 80 calls, all valid)

| Arm | Planted oddities found (of 24, brightness >= 40) | False features on untouched (of 16) |
|---|---|---|
| ZA (frozen 1x4 strip, prompt v1) | 9 | 2 |
| BG (2x2 grid at 536 px per tile, prompt "scan") | 14 | 3 |

Rule (BG if +3 hits and at most +2 false features) chose BG. 14/24 passes the A-mini read-out bar (12/24 with <= 4/20 false features) for the first time. Small samples: 24 and 16 objects, the two arms differ by 5 hits.

## Main pass (arm BG), stopped by the quota at 100% of the old week, then by the 07:59 UTC deadline

126 of 330 calls done (124 valid, 2 errors): 117 top-ranked fresh-sky objects, 4 random fresh controls, 5 development controls. Fresh tiles 102015586, 102016883, 102159389.

- Flagged (interest >= 2.6): 23 of 117 top-ranked objects, 1 of 4 fresh controls, 1 of 5 development controls. Labelled artefact: 24 of 117.
- Strict leads (interest >= 3.5, rare or unexplained, confidence medium or high): 1. An S-shaped tidal stream about 12 arcsec long attached to a disc galaxy (RA 63.50657, Dec -53.19399; WISEA J041401.59-531138.1 in NED). Fails the fixed bright-star check (a G < 16 star within 40 arcsec), clearly real in VIS and NISP (S/N 136 and 280). Most likely an interacting pair with a tidal tail: pretty, not new physics.
- Below the lead bar, the model offered 4 possible lensing arcs (all low confidence) and one small blue ring. None is within 10 arcsec of an ECLIPSE lens; NED has only WISE/2MASS detections there. Other Euclid lens catalogues were not checked. These need an expert look before they mean anything.

Page with images and checks: fpass_leads/index.html. Tables: tables/fpass_*.
