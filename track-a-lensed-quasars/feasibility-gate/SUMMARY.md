# Track A feasibility gate: summary

Date: 13–14 Nov 2026. Rules ([RULES.md](RULES.md)) were committed before any evaluation; results are in [gate_summary.json](gate_summary.json). Amendments: [AMENDMENTS_v2.md](AMENDMENTS_v2.md).

Purpose: before freezing a revised lensed-quasar detector for a blind run, check whether any of 48 pre-declared rules (detection threshold × flux-ratio cap × separation window × galaxy veto) passes every development threshold at once.

**Verdict: not feasible. No rule passes.**

Best rule (T > 10,000, flux ratio ≤ 10, separation 0.15–1.8″, no galaxy veto):

| Check | Result [95% interval] | Bar | |
|---|---|---|---|
| P2 injection completeness | 97.4% (1098/1127) [96.3, 98.3] | ≥ 90% | pass |
| P3 separation at 50% completeness | 0.196″ | ≤ 0.3″ | pass |
| P4 false alarms on verified single stars | 0.24% (28/11,858) [0.16, 0.34] | ≤ 0.1% | **fail** |
| P4g isolated galaxies taken for pairs | 14.4% (201/1,395) [12.6, 16.4] | ≤ 5% | **fail** |
| P5 development planted set: recall / false claims | 97.8% / 1.6% | ≥ 85% / ≤ 3% | pass |

Completeness by separation: 0.15″ 11%, 0.2″ 53%, 0.3″ 92%, 0.4″ 93%, 0.6″ 95%, 1.0″ 99%, 1.5″ 100%.

Why it fails:

- About 0.2% of stars that the Euclid catalogue lists as single show a second component at 0.24–1.35″, with flux ratios of 5–10. They look like real faint companions, which no visible-band rule can reject. The two independent checks meant to confirm them (catalogue neighbours) report spurious neighbours 17–22% of the time and were declared inadmissible by the pre-set rule.
- A point-source-plus-galaxy model removes most galaxy confusions but drops completeness to about 65% and moves the 50% point to 0.47″.

Possible next steps (not started): confirm companions with the near-infrared bands or Gaia astrometry, and compare four models instead of two.
