# Track R results: 227 compact radio sources with no Euclid counterpart

18-19 Nov 2026. Rules: [PREREG_R.md](PREREG_R.md), published before the main run. Code: `rd.py`, `rd2.py`, `rd3.py`. Table: [candidates.csv](candidates.csv). Images of every selected source: [sheets/](sheets/).

Every entry is an unverified candidate. This is a known class of object (infrared-faint radio sources); the list is offered as a checked target list, not as a new kind of object. A steep, compact radio source with no optical counterpart is also what a pulsar looks like.

## Counts

| Step | Sources |
|---|---|
| RACS-mid sources within 0.36 degrees of a DR1 tile centre | 181,971 |
| Compact, isolated, peak >= 5 mJy/beam, S/N >= 20 | 10,021 |
| On sky covered by the Euclid catalogue | 8,229 |
| Both mosaics fetched | 8,029 |
| At most 10% of pixels missing within 3 arcsec, both bands | 7,480 |
| Local 5 sigma limit >= 23.0 (VIS) and 22.3 (H) | 5,791 |
| Forced S/N < 3 in VIS and in H | 245 |
| RACS-high source within 3 arcsec, compact in both surveys | 229 |
| Kept after the image check | 227 |

Of the 227: 108 "empty" (no smoothed peak above 5 times the local scatter within 1.5 arcsec in either band), 119 "faint host". 12 lie in the development region, where the rules were tuned; they are marked `dev` and are not blind.

Median spectral index between RACS-low (943.5 MHz) and RACS-mid (1367.5 MHz): -1.18. The surveys were observed at different dates and the RACS-low frequency was not checked against the table metadata, so single values are indicative only.

156 of the 229 selected sources have no CatWISE2020 source within 5 arcsec.

## Image check

Claude Fable 5.2 (Claude Code, interactive session) looked at all nine sheets on 18-19 Nov 2026, only to remove data faults. Two sources were removed:

- RACS-MID1 J010708.0-580626: in VIS, a patch of low-coverage noise with a masked hole covers the position.
- RACS-MID1 J043500.4-243104: in H, the edge of the mosaic lies about 3 arcsec from the position and the data are noisy.

Noted but kept: several sources have a galaxy 1.5 to 4 arcsec from the radio position (for example J044929.6-315717 and J021023.6-544656). The aperture test does not exclude such a host; the sheets show it.

## Literature check (incomplete)

- The 30 brightest were looked up in SIMBAD and NED within 15 arcsec on 18 Nov 2026. All are known only as radio-survey detections (NVSS, SUMSS, GLEAM). None has a redshift. J023623.6-350755 lies 4 arcsec from a WISE source that SIMBAD lists as a BL Lac candidate and NED as a QSO.
- Not done yet: the same lookup for the other 197 (running), comparison with published samples of high-redshift radio galaxy candidates and ultra-steep-spectrum sources, pulsar catalogue, VLASS morphology north of Dec -40. The CDS VizieR service could not be reached on 18-19 Nov 2026.
- Until these are done, no source here should be described as previously unstudied.

## Deviations from the rules

- The public copy of the rules was pushed about one minute after the main run was started (the first push was rejected because the repository had moved). The private repository held the rules before the start, and no selection result existed for several hours after it.
- The rules say pulsar, SIMBAD, NED and VLASS columns are added "when the CDS services answer again". SIMBAD and NED were reached through other mirrors; pulsars and VLASS are still missing.

## The ten brightest

| Source | Peak (mJy/beam) | Class | Index low-mid | Euclid 5 sigma limits (VIS, H) | Known as |
|---|---|---|---|---|---|
| J030746.3-371558 | 65.8 | empty | -1.37 | 24.9, 23.5 | NVSS J030746-371558 |
| J042613.9-442946 | 58.3 | faint host | -1.48 | 24.8, 23.3 | SUMSS J042613-442946 |
| J042027.0-404055 | 57.7 | empty | -1.50 | 24.0, 22.6 | GLEAM J042027-404056 |
| J043442.6-182258 | 48.2 | faint host | -1.57 | 24.9, 23.1 | NVSS J043442-182257 |
| J023343.9-553520 | 42.6 | empty | -1.24 | 24.9, 23.6 | SUMSS J023343-553519 |
| J022629.0-602733 | 41.9 | faint host | -1.05 | 24.2, 23.1 | none found |
| J023215.7-413658 | 36.9 | empty | -0.57 | 25.0, 23.5 | GLEAM J023215-413658 |
| J032209.5-362815 | 31.5 | faint host | -0.78 | 24.7, 23.3 | NVSS J032209-362814 |
| J020655.1-571021 | 30.2 | faint host | -1.31 | 24.7, 23.2 | SUMSS J020655-571023 |
| J023124.3-371321 | 28.8 | faint host | -1.38 | 24.4, 22.9 | NVSS J023124-371322 |
