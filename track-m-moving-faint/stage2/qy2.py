"""Track M, second stage: titles of the VizieR catalogues that contain the five Gaia white dwarfs, and a debug of the VHS query."""
import os, re
import pandas as pd
import requests
H = os.path.expanduser("~/trackm")
HOSTS = ("https://vizier.cfa.harvard.edu", "http://vizier.nao.ac.jp", "https://vizier.idia.ac.za")


class qy:
    @staticmethod
    def viz(params, timeout=(10, 90)):
        for h in HOSTS:
            try:
                r = requests.get(h + "/viz-bin/asu-tsv", params=params, timeout=timeout)
                if r.status_code == 200 and "#" in r.text:
                    return r.text
            except Exception:
                pass
        return None

    @staticmethod
    def rows(text):
        return None if text is None else [x for x in text.splitlines() if x.strip() and not x.startswith("#")]


codes = """1252 1284 1297 1305 1317 1324 1352 1355 2391 4039 6042 102002 1047001501 17570083 19700181 19840058 22460004 22470066 22530058 36490006 36570007 36580022 36740022 36740033 36790127 36820005 36920115 36990003 51590084 51610234 74824570 74855573 75083877 75185106""".split()
J = {"1": "J/ApJ", "2": "J/ApJS", "3": "J/A+A", "5": "J/AJ", "7": "J/MNRAS"}
def name(c):
    if len(c) == 4: return {"1": "I", "2": "II", "4": "IV", "6": "VI"}[c[0]] + "/" + c[1:].lstrip("0")
    if len(c) == 8:
        v, p = int(c[1:4]), int(c[4:])
        return f"{J[c[0]]}/{v}/{'A' if c[0] == '3' and v >= 641 else ''}{p}"
    return c
if __name__ == "__main__":
  for c in codes:
      n = name(c)
      t = qy.viz({"-source": n, "-out.max": 0, "-meta": 1}, timeout=(10, 40)) or ""
      m = re.search(r"#Title:\s*(.*)", t) or re.search(r"#INFO\s+Title.*", t)
      d = re.findall(r"^#(?:Name|Title|Table).*", t, flags=re.M)[:2]
      print(c, n, "|", (m.group(1) if m else " ; ".join(d))[:150])
  A = pd.read_csv(H + "/m2/gwd.csv", dtype={"GaiaEDR3": str})
  c = A[(A.Gmag < 17.5) & (A.DE_ICRS < -45)].drop_duplicates("GaiaEDR3").iloc[0]
  for src in ("II/367", "II/367/vhs_dr5", "II/359/vhs_dr4", "II/246/out"):
      for rad in (5, 60):
          t = qy.viz({"-source": src, "-c": f"{c.RA_ICRS:.6f} {c.DE_ICRS:.6f}", "-c.rs": rad, "-out.max": 3, "-out": "_r,RAJ2000,DEJ2000,Jap3,Hap3,Jmag,Hmag"})
          L = qy.rows(t)
          print(src, rad, "arcsec:", "no answer" if L is None else L[:6], "| tables:", re.findall(r"^#Name:\s*(\S+)", t or "", flags=re.M))
