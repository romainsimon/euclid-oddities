"""Track M, second stage: the subset of Gaia white dwarfs sent to the photometry fetch (calibration and validation sample).
All clean ones with a catalogue temperature below 7000 K, and 2500 warmer ones drawn at random (seed 1)."""
import os

import pandas as pd

H = os.path.expanduser("~/trackm/m2")
G = pd.read_csv(H + "/gwd.csv", low_memory=False)
C = G[(G.det_quality_flag == 0) & (G.vis > 18.5) & (G.ls_maskbits == 0) & (G.point_like_prob > 0.9) & (G.ls_type == "PSF") & G.TeffH.notna()]
cool, warm = C[C.TeffH < 7000], C[C.TeffH >= 7000]
S = pd.concat([cool, warm.sample(min(2500, len(warm)), random_state=1)])
S.to_csv(H + "/gcal.csv", index=False)
print(f"Gaia white dwarfs matched {len(G)}, clean {len(C)}, below 7000 K {len(cool)} (below 5000 K {int((C.TeffH < 5000).sum())}), sent to the fetch {len(S)}")
