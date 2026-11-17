# Euclid Oddities: agent rules

Public record of an open-ended search of ESA Euclid DR1 images with Claude. Code that runs the search lives in the private research repository (`tools/claudestronomy/trackd`); this repository holds what is published.

## Publish every new find and every review

Romain's standing instruction (17 November 2026): every new find and every review (AI second opinion, catalogue check, expert reply) is published both here on GitHub and on https://spacesim.co/euclid-oddities, without asking again each time.

1. After a run, export with `fexport.py`; put reviews in `site/data/reviews/<slug>.json` (one file per review; never edit or delete a published review, add a new one).
2. Run `bash site/publish.sh "<one line: what changed>"` from Git Bash on the Windows PC. It exports, commits and pushes this repo, regenerates the SpaceSim gallery on a fresh branch from `origin/main`, syncs the SpaceSim changelog boundary, runs the four focused SpaceSim tests and pushes to SpaceSim `main` (Coolify deploys it).
3. Check that https://spacesim.co/euclid-oddities and one new find page return 200.

If a test fails, or SpaceSim `main` changed in a way that conflicts, stop and tell Romain; do not force-push.

## What may be published

- Only finds produced by a run whose rules were committed (and pushed here) before its first model call. Record them in `track-d-anomaly-hunt/AMENDMENTS_D.md`.
- Every entry stays labelled as an unverified model suggestion until an astronomer has looked at it. Never call anything a discovery.
- Record the model id, effort setting, harness and date for every find and every review.
- Reviews are blind: the reviewer does not see the original model's description.
- No personal data: no e-mail addresses, tokens or private paths beyond what the hashed pre-registrations already contain.

## Design

Follow SpaceSim's static-page conventions and Romain's style: no borders or separators, large rounded cards, pill controls, no native selects or sliders, self-hosted fonts. The generator is `site/build.py`; never hand-edit generated HTML in SpaceSim.

## Pre-registrations

Files with a `.sha256` next to them are frozen. Never change them (`.gitattributes` keeps their bytes exact).
