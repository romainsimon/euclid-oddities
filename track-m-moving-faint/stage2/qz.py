"""Track M, second stage: the public tables were written with positions rounded to 4 decimals (0.36 arcsec). Restore 6 decimals from the fit table."""
import os

import pandas as pd

H = os.path.expanduser("~/trackm")
O = pd.read_csv(H + "/m2/out/fit_all.csv.gz", usecols=["object_id", "right_ascension", "declination"]).drop_duplicates("object_id").set_index("object_id")
for f in ("interesting_candidates.csv", "fits_all.csv.gz", "halo_candidates.csv", "fits_no_model.csv"):
    T = pd.read_csv(f"{H}/pub2/{f}")
    T["right_ascension"] = T.object_id.map(O.right_ascension).round(6)
    T["declination"] = T.object_id.map(O.declination).round(6)
    assert T.right_ascension.notna().all()
    T.to_csv(f"{H}/pub2/{f}", index=False)
    print(f, len(T), T.right_ascension.iloc[0], T.declination.iloc[0])
