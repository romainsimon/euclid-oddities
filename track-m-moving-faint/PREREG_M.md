# Track M: faint white dwarfs that moved. Rules fixed before the main run

Written 23 and 24 Nov 2026 by Claude Fable 5.2 (Claude Code, interactive session, Claude subscription) with Romain Simon, who approved rules A to E on 24 Nov 2026. Published before any result outside the development box was read. The measurement of every tile (`tm.py all`) started on 23 Nov; it applies no selection, and its outputs outside the development box have not been opened: only the status and error lines of its log were read, to follow the run. The selection scripts `ms.py` and `mp.py` refuse to run on the whole sky until this file is public (they check for a file named `FROZEN`).

Code next to this file: `tm.py` (measurement), `ms.py` (rules A, B, C catalogue step, D, E), `mp.py` (rule C pixel step).

No language model takes part in the selection.

## Question

Which faint point sources of Euclid DR1, absent from Gaia, have moved since the Legacy Surveys DR10 images (2013 to 2019), and which of them are white dwarfs? Among those, which show a near-infrared flux deficit?

White dwarfs and infrared-faint white dwarfs are known classes. The reduced-proper-motion method is classical and has been applied to SDSS, CFIS, Pan-STARRS1 and DECam data. The aim is a checked list of candidates beyond the Gaia limit over the Euclid DR1 south, with Euclid Y, J, H photometry. Nothing here is called a discovery.

## Data and measurement (code `tm.py`, constants in brackets)

1. Per Euclid tile: epoch = middle of the VIS observations (`dr1.mosaic_product`). Euclid sources: `dr1.mer_catalogue_wide_survey`, VIS PSF flux above 0.9 microJy (`VIS_FLUX_MIN`), `spurious_flag = 0`.
2. Legacy Surveys DR10 south Tractor catalogues of the bricks whose centre lies within 0.55 degrees of the tile centre (`BRICK_R`), `brick_primary` sources.
3. Pairs: mutual nearest neighbours within 3 arcsec (`PAIR_R`).
4. Tie: galaxies (not PSF in Legacy Surveys, `point_like_prob < 0.2`, VIS 19.5 to 23, pair within 0.6 arcsec, not a Gaia reference source) define zero motion; median offset per cell of a 4 x 4 grid, cells with fewer than 15 galaxies use the tile median (`GRID`, `CELL_MIN`).
5. Motion = (Euclid minus Legacy Surveys minus tie) / baseline, baseline = Euclid epoch minus the Legacy Surveys mid-epoch.
6. Motion error per axis = quadratic sum of the Legacy Surveys position error (from `ra_ivar`, `dec_ivar`), the tie error of the cell and a floor of 8 mas, divided by the baseline.

## Development box and what it showed

RA 50 to 60, Dec -50 to -40: 274 wide-survey tiles, about 68 deg2 (162 more tiles there belong to the Euclid Deep Field South and are not in the wide catalogue).

- Gaia stars: measured minus Gaia motion, 0.85 / 0.92 mas/yr per star and per axis (robust), tile offsets 0.2 mas/yr.
- Galaxies after the tie: 12 to 19 mas per axis, about 2 mas/yr.
- With the candidate cuts below: 1,901 movers among 139,819 clean non-Gaia point sources. The same cuts on 901,356 extended sources give 23 false movers, 21 of them at VIS 23.5 to 24. Scaled to the point-source counts: at most 0.7 false movers of 1,901.
- White dwarf box, first version (H_r > 15.5 + 3.5 (r - z)): 512 candidates. Tested on Gaia stars against Gentile Fusillo et al. 2021: it keeps 169 of 169 catalogued white dwarfs but only 38 % of the box is a catalogued white dwarf at VIS 18.5 to 19.8. Raising the line by 1.5 mag gives 90 % (65 of 72) and 92 % (49 of 53 at VIS 19.8 to 20.5), keeping 65 of 71 and 49 of 49. With that line: 406 candidates, about 6 per deg2.
- Near-infrared colours of box sources with J S/N above 8 follow a blackbody at the same g - r with a scatter of 0.09 mag. With the rules below, eight sources are selected at the catalogue step and three by the same rule with signs reversed (the noise tail). Of the eight, two are rejected at the pixel step for missing pixels and six pass. Of those six, three are clean and well beyond the scatter, two are mild, and one lies 5 arcsec from a bright galaxy that may bias its H flux.

## Rules for the main run

A. **Mover.** Mutual pair with separation below 2.5 arcsec; no Gaia identifier in Euclid and not a Gaia reference source in Legacy Surveys; `point_like_prob > 0.9`; Legacy Surveys type PSF and `maskbits = 0`; `det_quality_flag = 0`; VIS 20 to 24; VIS minus r between -1.2 and 0.6 (the same object at both epochs); r and z measured; motion above 30 mas/yr and above 5 times its error; no second Legacy Surveys source within 2 arcsec.

B. **White dwarf candidate.** r - z < 0.9 and H_r > 17.0 + 3.5 max(r - z, -0.5), with H_r = r + 5 log10(motion in arcsec/yr) + 5. Counts are also reported for the line at 15.5 (looser) and 17.5 (stricter).

C. **Near-infrared deficit candidate.** A white dwarf candidate with catalogue J S/N above 8 whose J - H lies more than 3 times its error below the blackbody value for its g - r, or whose J - H and Y - J both lie more than 2 times their error below it (error = photometric error and 0.08 mag in quadrature, after removing the median offset of the sample). Then, on 24 arcsec cutouts: no missing pixel within 1.5 arcsec in Y, J and H, and the forced J - H (0.8 arcsec aperture) at least 0.4 mag below the blackbody value. Candidates failing the pixel step are listed as rejected with the reason.

   Details fixed on 24 Nov, before the freeze, where the rule was silent: "the sample" is every white dwarf candidate of the run with J S/N above 8, not a per-tile sample. When the H flux is below 2 times its error, 2 times the error is used in its place, in the catalogue and on the pixels; J - H is then an upper limit. On the pixels, J must be detected above 5 sigma. Fluxes are the catalogue 2 FWHM apertures. A bright neighbour has no rule: such cases stay in the list with a note.

D. **Control, reported with the results.** The mover cuts applied to extended sources (`point_like_prob < 0.2`, not PSF in Legacy Surveys), per magnitude bin, scaled to the point-source counts. The count of sources with a near-infrared excess under rule C with signs reversed, as the noise tail.

E. **Checks per tile, reported.** Gaia motion recovery; tiles where the per-star scatter exceeds 2 mas/yr on either axis or the tie has fewer than 100 galaxies are dropped and listed. Tiles with fewer than 20 Gaia stars for the check are kept and counted.

F. **Bookkeeping.** An object present in two tiles is kept from the tile with the lower index. For the near-infrared deficit candidates only, the NOIRLab Source Catalog DR2 proper motion is added as a column from a third data set, with a flag when it differs from ours by more than 3 sigma. It is reported, it removes nothing.

## What a person or a model may still do

Claude Fable 5.2 looks at the cutouts of the near-infrared deficit candidates only, and may remove one only for a visible data fault, with the reason listed. It may not add a source or move a threshold.

## Known limits (to be printed with any result)

- Motions above about 0.3 arcsec per year are lost by the 2.5 arcsec pairing: the nearest and fastest objects are missing.
- The Legacy Surveys position is an average over up to five years of images; for fast objects it is smeared.
- Two epochs only in the selection. The NOIRLab Source Catalog DR2 motion is a reported column for the near-infrared deficit candidates, not a selection step. In the development box it agrees for the bright ones; so the brighter candidates could already be selected from that catalogue alone.
- Sky: only where Legacy Surveys DR10 south exists. The Euclid DR1 tiles north of about Dec +32 have no such catalogue and are not measured.
- The forced J - H in a 0.8 arcsec aperture comes out about 0.2 mag bluer than the catalogue colour for the development candidates. The 0.4 mag pixel threshold therefore removes data faults; it does not by itself prove a deficit. The catalogue step carries the selection.
- The noise tail is not negligible: in the development box, 8 sources on the deficit side against 3 on the excess side.
- The box purity (about 90 %) is measured on Gaia stars 1.5 to 4 mag brighter than the candidates; the contaminants (halo and thick-disc stars) change with magnitude.
- No parallax: nothing here gives a distance, a temperature or an age. "Infrared-faint" rests on four bands and a blackbody reference, not on a model atmosphere.
- Not done before the freeze: comparison with reduced-proper-motion white dwarf lists from the NOIRLab Source Catalog DR2, DES and DELVE, lists of known infrared-faint white dwarfs (Bergeron et al. 2022, Kilic et al. 2020), and a check that no Euclid Collaboration paper already lists these objects.

## Reporting

- Tables of movers, white dwarf candidates and near-infrared deficit candidates, with the counts at every step, the controls, and the development sources marked as not blind.
- Every entry labelled "unverified candidate". Model, harness and date recorded.
- A plain statement of how interesting the result is.
