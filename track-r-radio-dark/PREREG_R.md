# Track R: radio sources with no Euclid counterpart. Rules fixed before the main run

Written 18 Nov 2026 by Claude Fable 5.2 (Claude Code, Claude subscription) with Romain Simon, after the development region was analysed and before any result outside it was computed. The code is `rd.py` and `rd2.py` next to this file. `rd2.py` refuses to run on the non-development sky until this file is published (it checks for a file named `FROZEN`).

No language model takes part in the selection. Everything below is catalogue queries and pixel measurements.

## Question

Which compact, isolated radio sources of the RACS-mid survey (ASKAP, 1367.5 MHz) that fall on Euclid DR1 have nothing, or almost nothing, at their position in the Euclid VIS and H mosaics?

Such sources are a known class (infrared-faint radio sources, a hunting ground for distant radio galaxies). The aim is a checked list over the DR1 sky, not a new kind of object. Every entry is an unverified candidate. Nothing here is called a discovery.

## What was already run, and on what

1. `rd.py parent`, `select`: 486,176 RACS-mid sources (CASDA table `AS110.racs_mid_sources_v01`) in the 5 x 5 degree boxes that hold a DR1 tile; 181,971 within 0.36 degrees of a tile centre. Kept: `flag = 0`, one Gaussian, peak >= 5 mJy/beam, peak / noise >= 20, no other RACS-mid source within 90 arcsec. Result: 10,021 sources. Each gets one control position 60 arcsec to the north.
2. `rd.py euclid all`: one 20 arcsec cone on `dr1.mer_catalogue_wide_survey` for each of the 20,042 positions (finished 18 Nov 2026, no failed query). These catalogue cones were downloaded for the whole sample, but they were read only for the development region.
3. Development region: RA 50 to 60, Dec -50 to -40. It holds 399 of the 10,021 sources. Every threshold below was chosen there.

## What the development region showed

- First rule tried: "no catalogued Euclid source within 2.5 arcsec". It was dropped after looking at the 14 sources it selected. Ten of them have a visible host that the catalogue lacks or flags (next to a bright star, inside a large galaxy, or seen in H only). And a random position has a catalogued source within 2.5 arcsec 47% of the time, so the rule would also lose about half of the truly empty positions. The selection is now made on the pixels.
- Astrometry: after removing one offset per RACS field (up to 0.7 arcsec), bright matches scatter by 0.39 arcsec per axis; 99% lie within 1.36 arcsec.
- Forced photometry check: at 129 control positions with no catalogued source within 3 arcsec, the 1.5 arcsec aperture gives S/N with median -0.4 and standard deviation 0.7 (VIS) and 0.8 (H); none exceeds 3 in VIS and one does in H. The noise estimate is slightly too large, which makes "S/N < 3" a little easier to pass than a true 3 sigma. Forced fluxes of 105 isolated matched sources reproduce the catalogue aperture magnitudes with a scatter of 0.09 mag (VIS) and 0.05 mag (H).
- Result on the development region with the rules below: 378 covered sources, 285 with deep enough data, 13 faint in both bands, 12 after the radio checks (4 "empty", 8 "faint host").

## Rules for the main run (fixed)

Code constants are named in brackets.

1. **Position.** RACS-mid `ra`, `dec_corr`, shifted by the median offset of its RACS field. The offset is the median (Euclid minus radio) of sources of that field whose nearest non-spurious Euclid source lies within 1.5 arcsec and has H < 21 (`BRIGHT_R`, `BRIGHT_H`); a field with fewer than 8 such matches gets the median of the whole run (`FIELD_MIN`). In the main run the offsets are recomputed from all sources.
2. **Covered.** At least 3 non-spurious Euclid catalogue sources between 8 and 20 arcsec from the position (`COVER_MIN`).
3. **Pixels.** VIS and NIR_H background-subtracted mosaics (`DpdMerBksMosaic`), 33 arcsec cutouts. A band is usable when at most 10% of pixels within 3 arcsec are missing (`BAD_MAX`). Flux is summed in a 1.5 arcsec radius aperture at the position. Background and noise are the median and the robust scatter (1.4826 x MAD) of 300 equal apertures centred 3.5 to 12 arcsec away (`RING`). Magnitudes use the mosaic's `MAGZERO`.
4. **Depth.** The local 5 sigma limit of that aperture must be at least 23.0 in VIS and 22.3 in H (`LIM_MIN`). This removes positions near bright stars and large galaxies, where an empty aperture means nothing.
5. **Faint in Euclid.** Aperture S/N below 3 in VIS and in H (`SNR_MAX`).
6. **Radio checks.** A RACS-high source (1655.5 MHz, `AS110.racs_high_sources_v01`) within 3 arcsec of the RACS-mid catalogue position (`HIGH_R`), and total / peak flux at most 1.3 in RACS-mid and in RACS-high (`TP_MAX`). This asks for a second, independent detection and removes resolved sources, whose centre need not be where the galaxy is.
7. **Two classes.** "empty": the highest pixel of the 0.3 arcsec smoothed image within 1.5 arcsec of the position stays below 5 times the local scatter in both bands (`PEAK_EMPTY`, `SEARCH_R`). Otherwise "faint host". Both are listed.
8. **Columns added for description only** (they never add or remove a source): spectral indices from RACS-low (943.5 MHz, value taken from the survey description, not checked against the table metadata), RACS-mid and RACS-high total fluxes, which were observed at different dates; nearest CatWISE2020 source within 5 arcsec. Pulsar catalogue, SIMBAD, NED and VLASS matches are added when the CDS services answer again (they were down on 18 Nov 2026); they are also descriptive.

## What a person or a model may still do

- Claude Fable 5.2 looks at the image sheet of every selected source. It may only remove a source for a visible data fault (diffraction spike, ghost, mosaic edge, cosmic-ray trail, residual of a masked star), and each removal is listed with its reason. It may not add a source, move a threshold or reorder the list.
- The list is ordered by RACS-mid peak flux, brightest first.

## Reporting

- The full table of selected sources is published, with the removed ones marked, and the counts at every step.
- The 12 development sources are reported separately and marked as not blind: the rules were tuned on them.
- Before any source is described as unusual, the literature is searched for it (infrared-faint radio sources, ultra-steep-spectrum samples, known high-redshift radio galaxies, pulsars). A steep, compact, optically empty radio source is also what a pulsar looks like in such a search; that reading is stated wherever it applies.
- Model, effort, harness and date are recorded with every published item. Unattended steps on the server make no model call.

## Known limits

- RACS-mid positions are good to about 0.4 arcsec per axis after correction. A faint host 1.5 to 3 arcsec away is not excluded by the aperture test; the image sheets show 32 arcsec around every source.
- A double radio source whose two lobes are blended into one compact RACS-mid component, with the galaxy in the middle, passes the compactness test only if the blend is unresolved at 10 arcsec in RACS-high too. VLASS (2.5 arcsec resolution) covers Dec > -40 and will be used as a later check where available.
- The depth cut and the S/N cut were tuned on 399 sources in one 10 x 10 degree region. The noise estimate is known to be about 20 to 30% too large there.
- "Nothing in Euclid" means fainter than roughly 24.4 (VIS) and 23.0 (H) at 5 sigma in a 1.5 arcsec aperture, the median limits of the development region. It does not mean no galaxy.
