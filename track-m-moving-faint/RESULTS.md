# Track M results: faint white dwarf candidates that moved, and those with a near-infrared deficit

Run of 23 to 25 Nov 2026. Claude Fable 5.2 in Claude Code (interactive session, Claude subscription), with Romain Simon. Rules: [PREREG_M.md](PREREG_M.md), public before any result outside the development box was read (commit `fc60a7f`, 24 Nov 2026, about 16:50 UTC; the whole-sky selection started at 20:51 UTC).

No language model takes part in the selection. The model looked at the cutouts of the near-infrared deficit candidates only, and removed five for a visible data fault.

**Every entry is an unverified candidate.** Nothing here has a spectrum, a parallax or a temperature. White dwarfs and infrared-faint white dwarfs are known classes.

## In short

- Proper motions of Euclid DR1 point sources absent from Gaia, from the Euclid position (2024 to 2025) against the Legacy Surveys DR10 position (2013 to 2019), over 6,601 Euclid tiles (about 1,650 deg2 before overlaps, Dec -67 to -18).
- 44,602 sources moved by more than 30 mas/yr at more than 5 sigma. The same cuts on 20 million extended sources predict at most 37 false ones.
- 9,407 fall in the white dwarf box of the rules, 5.7 per deg2, median r = 22.3. At most 23 false ones expected from the control.
- 221 of them have a near-infrared colour below a blackbody by the catalogue rule. 143 remain after the pixel step and the eye check.
- The same rule with signs reversed selects 89 sources. So part of the 221 is the tail of the noise. See "How much of this is noise" below.
- A check made after the results were read shows that the blackbody is a biased reference for the reddest sources. Compared with white dwarf candidates of the same colour, 102 of the 143 are still selected, and 49 are firm in two colours. Those 49 are the part to take seriously.
- None of the 143 has an entry in SIMBAD within 10 arcsec.

## Counts at every step

| Step | Count |
|---|---|
| Euclid wide tiles listed | 10,990 |
| Not measurable: no Legacy Surveys DR10 south at that position (all north of Dec +30) | 2,077 |
| Too few Euclid sources (deep-field tilings with no rows in the wide catalogue, edges) | 2,248 |
| Too few galaxies for the astrometric tie | 63 |
| Failed (dense tile still truncated by the archive: 102028713) | 1 |
| Measured | 6,601 |
| Dropped by rule E (Gaia scatter above 2 mas/yr, or tie on fewer than 100 galaxies) | 0 |
| Clean point sources, not in Gaia, VIS 20 to 24 | 4,789,781 |
| A. Movers | 44,602 |
| B. White dwarf candidates (line 17.0) | 9,407 |
| B. Same with the looser line 15.5 / the stricter line 17.5 | 12,191 / 8,723 |
| White dwarf candidates with J S/N above 8 | 8,232 |
| C. Near-infrared deficit, catalogue step | 221 |
| C. Rejected on the pixels: missing pixels within 1.5 arcsec | 50 |
| C. Rejected on the pixels: forced J - H not 0.4 mag below the blackbody | 22 |
| C. Rejected: cutout not obtained | 1 |
| Removed by eye for a visible data fault (artefact on the source in J) | 5 |
| **Near-infrared deficit candidates kept** | **143** |

Seven of the 143 lie in the development box (RA 50 to 60, Dec -50 to -40), where the rules were tuned. They are marked `dev_box` and are not blind.

## Checks

**Gaia motions (rule E).** For the Gaia stars of each tile, our motion minus the Gaia motion has a median per-star scatter of 0.84 / 0.86 mas/yr per axis; the worst tile has 1.60. No tile is dropped.

**Extended sources under the same cuts (rule D).**

| VIS | Extended sources | False movers | In the box | Point sources | Movers | Expected false, at most | Box | Expected false, at most |
|---|---|---|---|---|---|---|---|---|
| 20.5 to 21.5 | 774,293 | 2 | 1 | 1,066,746 | 17,123 | 2.8 | 1,121 | 1.4 |
| 21.5 to 22.5 | 3,056,039 | 24 | 18 | 2,122,311 | 19,016 | 16.7 | 4,503 | 12.5 |
| 22.5 to 23.5 | 8,303,933 | 79 | 40 | 1,541,503 | 8,207 | 14.7 | 3,622 | 7.4 |
| 23.5 to 24.0 | 8,184,172 | 407 | 192 | 59,081 | 255 | 2.9 | 161 | 1.4 |

The bin VIS 20.0 to 20.5 holds 140 point sources and 1 mover; no extended-source count was stored for it. Galaxies centroid worse than stars, so these numbers are upper bounds for the astrometric false positives. They say nothing about real stars that are not white dwarfs (next point).

**Purity of the box.** Not measured on this sample. On Gaia stars of the development box, 1.5 to 4 mag brighter, about 90 % of the box sources are catalogued white dwarfs (Gentile Fusillo et al. 2021). The contaminants are halo and thick-disc stars; their share at r = 22 to 23 is not known from this work.

**Third data set (rule F).** NOIRLab Source Catalog DR2 motions for the 143: compatible 127, differing by more than 3 sigma 9, query failed 7. After a retry of the 7 (`posthoc.csv`): compatible 133, differing 10. The 10 are kept and flagged.

## How much of this is noise

The catalogue rule selects 221 sources on the deficit side and 89 on the excess side. The excess side is not pure noise (a white dwarf with a cool companion is red in J - H), and it did not go through the pixel step, so it is an imperfect mirror. With that caveat:

- Deficit in J - H beyond 3 sigma **and** in Y - J beyond 2 sigma: 75 on the deficit side at the catalogue step, 17 with both colours in excess.
- Among the 143 kept: 118 have both colours below the blackbody by more than 2 sigma, 92 have J - H beyond 3 sigma, and 66 have both, with no disagreement in the third data set. This "two colours" subset was defined after the results were read; it is not part of the rules.
- Two of the 143 have a high J against both Y and H (`j_high`), which is the signature of a fault in J rather than of a deficit in H.

A fair reading at this stage: a few tens of the 143 are expected to be scatter. The next section reduces the firm part further.

## Check made after the results were read: the reference is biased with colour (`mx.py`, `posthoc.csv`)

Rule C removes one median offset for the whole sample. That is not enough. The residual of the 8,232 white dwarf candidates against the blackbody depends on colour:

| g - r | Sources | Median J - H minus blackbody | Robust scatter |
|---|---|---|---|
| below 0.2 | 1,007 | +0.05 | 0.11 |
| 0.2 to 0.4 | 1,458 | +0.06 | 0.09 |
| 0.4 to 0.6 | 1,416 | +0.05 | 0.10 |
| 0.6 to 0.8 | 1,500 | +0.01 | 0.09 |
| 0.8 to 1.0 | 1,198 | -0.06 | 0.09 |
| 1.0 to 1.2 | 528 | -0.17 | 0.12 |
| 1.2 to 1.4 | 449 | -0.01 | 0.09 |
| above 1.4 | 676 | -0.04 | 0.06 |

The scatter also grows with magnitude, from 0.08 at r = 21 to 0.19 beyond r = 23. Half of the 143 have g - r above 1.16, so many of them sit where the whole population is already below the blackbody. The dip at g - r of 1.0 to 1.2 may be real physics shared by ordinary cool white dwarfs (hydrogen absorption sets in at these temperatures) or a change in the mix of contaminants; this work cannot tell.

Re-scored against a running median in g - r (401 sources), with the same thresholds:

- 102 of the 143 are still selected.
- 49 of the 66 "two colours" sources remain. They are flagged `firm` and `local_firm` in `posthoc.csv`.
- Over the whole sample, the local rule selects 177 sources on the deficit side and 88 on the excess side; in two colours, 60 against 17.

The frozen list of 143 is not changed. The 49 are the candidates to look at first, and the two-colour asymmetry (60 against 17) is the evidence that some real near-infrared deficits are present.

**SIMBAD.** A 10 arcsec cone around each of the 143 (IDIA mirror, 25 Nov 2026) returns nothing.

## What the deficit means, and what it does not

The reference is a blackbody at the temperature given by g - r. A real white dwarf with a hydrogen or helium atmosphere is not a blackbody, and the forced J - H in a 0.8 arcsec aperture comes out about 0.2 mag bluer than the catalogue colour. So the measured deficits (median 0.57 mag on the pixels, 0.4 to 1.4) are not atmospheric parameters, and they are not compared here with published colours of infrared-faint white dwarfs: that needs a common photometric system and model atmospheres. The mildest ones may be ordinary cool white dwarfs.

## How interesting is this

Plainly: moderate.

- The method is classical and the classes are known. The density found, 5.7 per deg2, is what Galactic models predict for this depth and motion limit.
- A web search on 24 Nov 2026 found no published list of white dwarf candidates from Euclid motions, and no southern reduced-proper-motion white dwarf catalogue beyond r = 21. It is a search, not a proof of absence.
- Bergeron et al. 2022 (arXiv:2206.03174, abstract re-read on 25 Nov 2026) analyse 105 infrared-faint white dwarfs, 70 new and 35 known, drawn from samples within about 100 pc. According to the literature search they have g of about 18 to 21; that range was not re-checked. The candidates here have r = 20.9 to 23.7 (91 of 143 fainter than r = 22) and Y, J, H photometry from Euclid.
- After the colour check above, the part worth a specialist's time is about 49 sources, not 143.
- The brighter ones already have a motion in the NOIRLab Source Catalog DR2. Euclid adds the precision at r above 22 (1 to 3 mas/yr against 10 to 20) and the near-infrared bands.
- Confirming any of them needs a spectrum at r = 21 to 23, which is 8 m class telescope time.

## Deviations from the plan

- The whole-sky measurement ran once. Instead of a full second pass, only the 59 dense tiles that had been truncated by the Euclid archive (50,000-row limit) were measured again in declination strips: 48 measured, 10 with too few tie galaxies, 1 still failing.
- `mn.py` (third data set column) was written after the freeze and before any non-development result was read.
- "Differs by more than 3 sigma" in rule F is computed on the two axes together (quadratic sum).
- The model's eye check went beyond missing pixels: five sources were removed for an artefact on the source in J. Reasons are in the table.
- The literature check was a web search run by a sub-agent on 24 Nov. Only Bergeron et al. 2022 was re-opened afterwards.
- The public tables and the site data were assembled from the outputs of `ms.py`, `mp.py` and `mn.py` by short one-off commands that are not in this folder. The five eye removals and their reasons are in the `verdict` column.

## Files

| File | Content |
|---|---|
| `ir_deficit_candidates.csv` | The 221 catalogue-step sources with verdict (`passes`, `rejected: ...`, `removed by eye: ...`), colours, significances, pixel measurements, third data set motion |
| `white_dwarf_candidates.csv.gz` | The 9,407 white dwarf candidates: position, magnitudes, motion, Euclid Y, J, H fluxes |
| `movers.csv.gz` | The 44,602 movers |
| `irexcess.csv` | The 89 sources of the reversed rule |
| `sheets/deficit_*.jpg` | Cutouts (VIS, Y, J, H; 10 arcsec shown, circle radius 1 arcsec) of the 143 kept, in table order (`row`) |
| `sheets/rejected_*.jpg` | Cutouts of the rejected and removed ones |
| `tiles_dropped.csv` | Tiles dropped by rule E (none) |
| `posthoc.csv`, `mx.py` | Checks made after the results were read: score against the local median, SIMBAD cone, retried third data set queries |
| `tm.py`, `ms.py`, `mp.py`, `mn.py` | Measurement, selection, pixel step, third data set |

Data: ESA Euclid DR1 (Euclid Collaboration), DESI Legacy Imaging Surveys DR10, NOIRLab Source Catalog DR2, Gaia.
