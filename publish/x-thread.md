# X thread (draft, not posted)

1/
Euclid's DR1 came out this week. Instead of hunting for one kind of object, I asked Claude to look at the images and flag anything weird.

The catch: how do you know when to trust it? 🧵

2/
So I hid fake oddities in real Euclid images (arcs, streaks, pairs, clouds, instrument artefacts) under a sealed key, mixed in known lenses, and wrote down the pass/fail thresholds before Claude saw anything.

3/
Haiku, ~2,500 images:
✅ invents little: 9% false features
✅ rarely calls an artefact real: 7%
❌ finds 18% of planted oddities
❌ spots 31% of known lenses

4/
Same 60 images, stronger models:
Haiku 2/24 · Sonnet 8/24 · Fable 5.2 9/24 planted oddities found, with no more false features.

When they flag something, it's almost always in the right place. They just don't notice the rest.

5/
Next: show the images differently, add a second model family, and find an expert to judge real-sky candidates blind.

Everything, failures included: [LINK]
Thanks to @[Claudestronomy handle] for the push.
