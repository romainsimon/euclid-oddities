# I asked Claude to look for weird things in Euclid's new sky images

*Draft for romainsimon.com. Not published.*

On 12 November, the European Space Agency released Euclid's first big data release: about 1,900 square degrees of sky, imaged sharper than any ground telescope can manage. A day later I came across Claudestronomy, a small grant programme for people using AI agents to find new things in public sky data. I couldn't resist.

## Searching the other way around

Most searches in a survey like Euclid are targeted. A team trains a detector for lenses, another for mergers, another for a specific kind of galaxy. That works well for what you already know to look for.

I wanted to try the opposite: let Claude look at the images and flag whatever looks odd, including the things nobody is searching for. Citizen scientists on Galaxy Zoo found some of the strangest objects of the last twenty years exactly this way, by asking "what is that?".

## The hard part is trust

A model that says "this is strange" is only useful if you know how often it is right. So before Claude saw a single image, I fixed the rules:

- **Planted fakes under a sealed key.** I hid synthetic oddities in real Euclid images: arcs, straight streaks, identical pairs, diffuse clouds, shapes that mean nothing, and five kinds of instrument artefact. Only a separate grading program can read the key.
- **Known objects without labels.** Real gravitational lenses from the Euclid team's own catalogue, mixed in.
- **Thresholds written down in advance**, with a SHA-256 hash, and every later change logged with its reason.

## What happened

Claude Haiku went through about 2,500 Euclid images.

| Check | Result | Target set in advance | |
|---|---|---|---|
| Planted oddities found | 18% | ≥ 70% | ❌ |
| Known strong lenses spotted | 31% | ≥ 60% | ❌ |
| False features on untouched images | 9% | ≤ 10% | ✅ |
| Artefacts mistaken for astrophysics | 7% | ≤ 20% | ✅ |
| Same answer when shown again (κ) | 0.72 | ≥ 0.6 | ✅ |

It rarely makes things up, but it misses most of what is there.

Then I showed the same 60 images to stronger models:

| | Haiku | Sonnet | Fable 5.2 |
|---|---|---|---|
| Planted oddities found | 2/24 | 8/24 | 9/24 |
| False features on untouched images | 3/20 | 2/20 | 4/20 |

Stronger models catch about four times more, without inventing more. They still miss two thirds. The interesting part is *how* they miss: when they flag something, they put it in the right place almost every time. They just don't notice the rest. That points at how the images are shown (small, compressed cutouts) more than at the model itself, so that is the next thing I'll test.

I also tried a classical search for very tight lensed quasars. It recovers 97% of simulated pairs down to 0.2 arcseconds, but it trips on something real: about one star in 500 that the catalogue calls single seems to have a faint companion. That is a null result too, and it is published with its sensitivity.

## What's next

- Show the images differently: zoomed crops, larger images, asking the model to list everything it sees.
- A second model family, so blind spots shared by all Claude models show up.
- An expert to judge real-sky candidates blind.

Everything (pre-registrations, amendments, reports, the failures) is here: [LINK TO REPOSITORY / ZENODO DOI].

None of this is a discovery. It is a measurement of how far a general-purpose model can be trusted to look at the sky, and so far the honest answer is "not far enough yet, but getting better fast".
