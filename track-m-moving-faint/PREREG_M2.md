# Track M, second stage: what are these objects? Rules G to L, frozen before the fits of the candidates are read

Written 25 Nov 2026 by Claude Fable 5.2 (Claude Code, interactive session, Claude subscription) with Romain Simon. Romain's instruction for this stage: keep only objects that are really interesting.

No language model takes part in the selection. This stage is **not blind** for stage one: the 9,407 white dwarf candidates and the 143 near-infrared deficit candidates of [RESULTS.md](RESULTS.md) have already been read, and five were looked at closely in the development box. What has not been read when these rules are committed: any model fit of a candidate.

**Every entry stays an unverified candidate.** No spectrum, no parallax. Cool, infrared-faint and halo white dwarfs are known classes.

## Question

For each of the 9,407 candidates: which white dwarf model atmosphere fits its seven bands, at what temperature and distance, and how fast does it move across the sky? Which ones cannot be fitted without strong collision-induced absorption by molecular hydrogen (the signature of the coolest and of the "infrared-faint" white dwarfs)?

## Data

- Optical: Legacy Surveys DR10 Tractor g, r, i, z with their errors, at the Legacy Surveys position (`stage2/qd.py ls`, viewer catalogue service). The Euclid catalogue also holds DECam fluxes, but they are fitted at the 2024 position on older images, which is wrong for a source that moved; they are not used.
- Near-infrared: Euclid DR1 Y, J, H, 2-FWHM aperture fluxes (primary) and template-fit fluxes (second measurement) (`qd.py eu`).
- VIS is not fitted (broad band, no model column to check it against); it is kept as a check.
- Extinction: full Galactic column of Schlegel et al. 1998 as given by Legacy Surveys, transmissions of Legacy Surveys for g, r, i, z, and A / E(B-V) = 0.88, 0.60, 0.41 for Y, J, H.

## Models (`qm.py`)

- Spectra: Warwick grids, pure hydrogen (Tremblay et al. 2011, with the Lyman alpha wing of Kowalski & Saumon 2006 and H2 collision-induced absorption) and helium-rich (Cukanovaite et al. 2021: pure helium, and He/H = 1e2, 1e5, 1e8 by number).
- Integrated by us through the DECam and Euclid filter curves of the SVO Filter Profile Service. Check: our Pan-STARRS g, r, i magnitudes reproduce the table published with the grid within 0.01 mag (median); the z and y columns of that table are swapped.
- Radii: Montreal mass-radius tables (Bedard et al. 2020). Fits assume 0.6 solar masses. A second distance is computed at 0.9 solar masses ("conservative": a more massive white dwarf is smaller, hence nearer and slower).
- Limit: these are not the high-density models of Blouin et al. 2018 used for published infrared-faint white dwarfs. Below about 4000 K a temperature or a composition from these fits is indicative only.

## Calibration and validation on Gaia white dwarfs (development, `qg.py`, `qs.py`, `qf.py cal`)

Gaia white dwarfs (Gentile Fusillo et al. 2021, Pwd > 0.75) in the measured tiles: 12,838 matched, 3,364 clean ones fetched (all 864 below 7000 K, 2,500 warmer at random). They cannot be candidates (candidates are absent from Gaia). Everything in this section was tuned on them.

- Warm calibrators (7500 to 14000 K, 1,365 stars), optical fit, near-infrared predicted: the observed Euclid magnitudes are fainter than the model by 0.261, 0.274, 0.258 mag in Y, J, H (aperture) and 0.083, 0.092, 0.067 mag (template fit). No trend with temperature or magnitude above 0.01 mag. These offsets are removed. Residual scatter beyond the photometric error is below 0.05 mag; a systematic of 0.05 mag per near-infrared band and 0.03 mag per optical band is added in quadrature.
- With the offsets applied, on 724 stars with a good parallax: our temperature over the catalogue temperature has a median of 1.00 to 1.03 in every temperature bin (scatter 4 to 9 %); our photometric distance over the parallax distance has a median of 0.88 (22 stars below 5000 K) to 1.06, with a 16 to 84 % range of about 0.88 to 1.24. The conservative distance is below the parallax distance for 98 to 100 % of them.
- Five of the 3,123 quality Gaia white dwarfs meet rule H below. None of them has a tangential velocity above 200 km/s from Gaia, and rule J flags none. What the literature says about those five is reported with the results.
- The absorption thresholds of rule H were set on this sample: the first setting (-0.15 / -0.30) flagged ordinary pure-hydrogen white dwarfs near 4100 K, which are not rare; the thresholds were moved to -0.40 / -0.50.

## Rules

G. **Quality.** A candidate is classified only if: g, r and z observed, `fracflux` below 0.1 in g, r, z, `maskbits = 0`; J S/N above 5; Y and H measured; Euclid flags 0 in Y, J, H.

H. **Strong absorption.** All five compositions are fitted on the seven bands (temperature 2500 to 20000 K, amplitude free). Each model has an absorption index: its J - H minus the J - H of pure helium at the same temperature. "Ordinary" models have an index above -0.40 (pure helium, pure hydrogen down to about 4000 K, helium-rich models with little hydrogen absorption). A candidate has strong absorption if:
   - the best ordinary model is worse than the best model by 16 or more in chi2,
   - the best model has an index below -0.50,
   - the best model is acceptable (chi2 probability above 0.001),
   - and all of this holds with **both** near-infrared flux types.

I. **Ultracool.** A strong-absorption candidate for which every model within 9 in chi2 of the best one is below 4000 K, with both flux types.

J. **Halo kinematics.** Conservative tangential velocity = 4.74 x (motion minus its error) x (distance at 0.9 solar masses, the smaller of the pure-hydrogen and pure-helium values). Above 200 km/s: halo candidate. Above 500 km/s: flagged "above the local escape velocity if the distance is right", which more likely means that the distance is wrong.

K. **Checks on the strong-absorption candidates only.** The pixel step of stage one (no missing pixel within 1.5 arcsec in Y, J, H). Motion from the NOIRLab Source Catalog DR2 as a column, if the service answers. Claude Fable 5.2 looks at the cutouts and may remove a source only for a visible data fault, with the reason listed. SIMBAD cone of 10 arcsec.

L. **Controls, reported with the results.**
   - Noise-only expectation (`qf.py sim`): for each quality candidate, synthetic fluxes drawn from its best ordinary model with its own errors and systematics, same rules, five draws. Primary fluxes only, so it is an upper bound.
   - Count of H-band residuals below -3 sigma and above +3 sigma against the best ordinary model.
   - Median residual per band of the warm candidates (7000 to 15000 K): if it exceeds 0.05 mag in a near-infrared band, the faint-end zero point is in doubt and this is said first.

## What is published

- Only the strong-absorption candidates that pass rule K are presented as "interesting". If there are none, or five, that is the result. No threshold is moved afterwards.
- The halo candidates are published as a table, not as individual finds. Expectation written before looking: Munn et al. 2017 find 135 white dwarfs with 200 to 500 km/s over 2,256 deg2 to r = 21.5; Qiu et al. 2024 find 235 over 165 deg2 to i = 24. Scaled to 1,650 deg2 that is about 100 to 2,300, and the conservative distance lowers it. A count far above 2,000 would mean contamination, not halo stars.
- Fits of all 9,407 as a table (temperature, distance and velocity for pure hydrogen and pure helium, with the chi2).
- A plain statement of how interesting the result is.

## Known limits

- No parallax: the distance assumes a mass. The validation gives about 15 to 20 % scatter for Gaia white dwarfs; a low-mass or a very massive white dwarf is off by more.
- A source in the box that is not a white dwarf (a cool subdwarf of the halo) gets a meaningless fit. Its distance as a white dwarf is too short, so it cannot create a false halo flag, but it can create a bad chi2.
- The offsets are measured on stars of VIS 18.5 to 21; the candidates have VIS 20 to 24. Rule L checks this on the warm candidates.
- The aperture and template-fit fluxes come from the same pixels: asking for both guards against a measurement problem, not against noise.
