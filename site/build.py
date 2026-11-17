"""Static gallery for Euclid Oddities: one gallery page with filters and one page per find.

Usage: python build.py <out_dir> [--base /oddities]
Reads data/finds.json and data/img/. Writes <out>/index.html, <out>/<slug>/index.html, <out>/img/, <out>/finds.json.
No dependencies beyond the standard library.
"""
from __future__ import annotations

import argparse
import html
import json
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = "https://github.com/romainsimon/euclid-oddities"
SITE = "https://spacesim.co"

FEATURE = {"arc": "Arc", "ring": "Ring", "straight_line": "Straight line", "pair": "Pair", "diffuse_patch": "Diffuse patch",
           "irregular": "Irregular", "other": "Other", "none": "None"}
NATURE = {"ordinary": "Ordinary", "artefact": "Artefact", "known_rare_class": "Known rare class", "cannot_explain": "Cannot explain"}

CSS = """
@font-face{font-family:"Chillax";src:url("/assets/fonts/chillax-variable.woff2") format("woff2");font-weight:200 700;font-display:swap}
:root{--field:oklch(0.105 0.004 180);--raised:oklch(0.145 0.006 110);--control:oklch(0.14 0.005 110 / .92);
--hover:oklch(0.92 0.012 84 / .07);--text:oklch(0.92 0.012 84);--muted:oklch(0.76 0.012 84);--dim:oklch(0.7 0.012 84);
--line:oklch(0.92 0.012 84 / .18);--line-strong:oklch(0.92 0.012 84 / .4);--accent:oklch(0.7 0.1 73);--accent-strong:oklch(0.81 0.11 76);
--focus:oklch(0.83 0.12 77);--display:"Chillax","Helvetica Neue",Helvetica,Arial,system-ui,sans-serif;
--body:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;color-scheme:dark}
*{box-sizing:border-box}[hidden]{display:none!important}html{background:var(--field)}
body{margin:0;overflow-x:clip;background:var(--field);color:var(--text);font:15px/1.55 var(--body);-webkit-font-smoothing:antialiased}
a{color:var(--accent-strong);text-underline-offset:3px}a:hover{color:var(--focus)}
:focus-visible{outline:2px solid var(--focus);outline-offset:2px;border-radius:4px}
.wrap{max-width:1240px;margin:0 auto;padding:0 24px}
header.top{border-bottom:1px solid var(--line)}
header.top .wrap{display:flex;align-items:center;justify-content:space-between;gap:16px;height:56px}
.brand{font:500 17px/1 var(--display);letter-spacing:-.02em;color:var(--text);text-decoration:none}
.brand span{color:var(--dim);font-weight:400}
nav.top a{color:var(--muted);text-decoration:none;font-size:13px;margin-left:18px}nav.top a:hover{color:var(--text)}
.hero{padding-top:56px;padding-bottom:28px}
.eyebrow{font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:var(--accent)}
h1{font:450 clamp(34px,5vw,58px)/.98 var(--display);letter-spacing:-.045em;margin:12px 0 16px;max-width:15ch}
.lede{color:var(--muted);max-width:62ch;font-size:16px;margin:0}
.stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:1px;background:var(--line);border:1px solid var(--line);border-radius:9px;overflow:hidden;margin:32px 0 8px}
.stat{background:var(--field);padding:16px 18px}.stat b{display:block;font:450 28px/1.1 var(--display);letter-spacing:-.03em}
.stat span{color:var(--dim);font-size:12.5px}
.notice{border:1px solid var(--line);border-left:3px solid var(--accent);border-radius:8px;padding:12px 16px;color:var(--muted);font-size:13.5px;margin:20px 0 0}
.filters{position:sticky;top:0;z-index:5;background:color-mix(in oklch,var(--field) 92%,transparent);backdrop-filter:blur(8px);
border-bottom:1px solid var(--line);padding:14px 0;margin-top:28px}
.filters .wrap{display:flex;flex-wrap:wrap;gap:10px 18px;align-items:center}
.group{display:flex;gap:6px;align-items:center;flex-wrap:wrap}
.group>label,.lbl{font-size:12px;color:var(--dim);margin-right:2px}
.chip{appearance:none;border:1px solid var(--line);background:var(--control);color:var(--muted);border-radius:999px;padding:5px 11px;font:13px var(--body);cursor:pointer}
.chip:hover{background:var(--hover);color:var(--text)}.chip[aria-pressed=true]{border-color:var(--accent);color:var(--text);background:oklch(0.7 0.1 73 / .14)}
select,input[type=range]{accent-color:var(--accent)}
select{background:var(--control);color:var(--text);border:1px solid var(--line);border-radius:6px;padding:5px 8px;font:13px var(--body)}
.count{margin-left:auto;color:var(--dim);font-size:13px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:18px;padding:24px 0 60px}
.card{display:block;text-decoration:none;color:inherit;background:var(--raised);border:1px solid var(--line);border-radius:11px;overflow:hidden;transition:border-color .15s,transform .15s}
.card:hover{border-color:var(--line-strong);transform:translateY(-2px)}
.card img{display:block;width:100%;height:auto;aspect-ratio:1;object-fit:cover;background:#000}
.card .body{padding:12px 14px 14px}.card h3{font:500 15px/1.25 var(--display);letter-spacing:-.01em;margin:0 0 6px;color:var(--text)}
.meta{display:flex;flex-wrap:wrap;gap:6px;font-size:12px;color:var(--dim)}
.tag{border:1px solid var(--line);border-radius:999px;padding:1px 8px}
.tag.hi{border-color:var(--accent);color:var(--accent-strong)}
.card p{color:var(--muted);font-size:13px;margin:8px 0 0;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
.empty{color:var(--dim);padding:40px 0}
section.method{border-top:1px solid var(--line);padding:40px 0 70px;display:grid;grid-template-columns:1fr 1fr;gap:40px}
section.method h2,.detail h2{font:450 24px/1.1 var(--display);letter-spacing:-.03em;margin:0 0 12px}
section.method p,section.method li{color:var(--muted)}
table{border-collapse:collapse;width:100%;font-size:14px}td,th{border-bottom:1px solid var(--line);padding:8px 10px 8px 0;text-align:left;vertical-align:top}
th{color:var(--dim);font-weight:500;font-size:12.5px}td.num{font-variant-numeric:tabular-nums}
footer{border-top:1px solid var(--line);color:var(--dim);font-size:12.5px;padding:24px 0 40px}
.detail{display:grid;grid-template-columns:minmax(0,1.15fr) minmax(0,1fr);gap:36px;padding:28px 0 60px}
.viewer{position:relative}.viewer img{width:100%;height:auto;max-width:100%;display:block;border-radius:11px;border:1px solid var(--line);background:#000}
.legend{display:grid;grid-template-columns:1fr 1fr;gap:4px 16px;color:var(--dim);font-size:12.5px;margin-top:10px}
.toggle{margin-top:12px;display:flex;gap:8px}
.crumbs{font-size:13px;color:var(--dim);padding-top:24px}.crumbs a{color:var(--muted)}
.detail h1{font-size:clamp(28px,3.6vw,44px);max-width:none;margin-top:8px}
.quote{font-size:16px;color:var(--text);margin:14px 0}
.explain{color:var(--muted);font-size:14px}
dl{display:grid;grid-template-columns:max-content 1fr;gap:8px 18px;margin:20px 0;font-size:14px}dt{color:var(--dim)}dd{margin:0}
.links{display:flex;flex-wrap:wrap;gap:8px;margin:18px 0}
.btn{display:inline-block;border:1px solid var(--line-strong);border-radius:6px;padding:7px 12px;color:var(--text);text-decoration:none;font-size:13.5px}
.btn:hover{background:var(--hover);color:var(--text)}
.pager{display:flex;justify-content:space-between;gap:12px;border-top:1px solid var(--line);padding:18px 0 50px;font-size:14px}
@media (max-width:860px){.stats{grid-template-columns:repeat(2,1fr)}section.method,.detail{grid-template-columns:1fr}.count{margin-left:0;width:100%}}
@media (max-width:480px){.wrap{padding-left:16px;padding-right:16px}nav.top{display:none}.brand span{display:none}.hero{padding-top:32px}.stat b{font-size:22px}}
@media (prefers-reduced-motion:reduce){.card{transition:none}.card:hover{transform:none}}
"""


def e(s):
    return html.escape(str(s if s is not None else ""))


def page(title, desc, body, base, canonical, image=None):
    og = f'<meta property="og:image" content="{SITE}{image}">' if image else ""
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title><meta name="description" content="{e(desc)}"><link rel="canonical" href="{SITE}{canonical}">
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:type" content="website">{og}
<meta name="twitter:card" content="summary_large_image"><style>{CSS}</style></head><body>
<header class="top"><div class="wrap"><a class="brand" href="{base}/">Euclid Oddities <span>by SpaceSim</span></a>
<nav class="top"><a href="{base}/#method">Method</a><a href="{REPO}">Data &amp; rules</a><a href="/">SpaceSim</a></nav></div></header>
{body}
<footer><div class="wrap">Images: ESA Euclid DR1 (ESA/Euclid/Euclid Consortium), rendered by this project. Catalogue checks: SIMBAD, NED, ECLIPSE.
Every entry is an unverified suggestion made by a language model. Code, pre-registration and raw results: <a href="{REPO}">github.com/romainsimon/euclid-oddities</a>.</div></footer>
</body></html>"""


def tags(f):
    hi = " hi" if f["confidence"] in ("medium", "high") else ""
    return (f'<span class="tag">{e(FEATURE.get(f["feature"], f["feature"]))}</span>'
            f'<span class="tag{hi}">{e(f["confidence"])} confidence</span><span class="tag">interest {f["interest"]}</span>')


def card(f, base):
    return (f'<a class="card" href="{base}/{f["slug"]}/" data-feature="{e(f["feature"])}" data-conf="{e(f["confidence"])}" '
            f'data-interest="{f["interest"]}" data-cat="{"yes" if f["catalogued"] else "no"}" data-date="{e(f["date_found"])}">'
            f'<img src="{base}/img/{f["slug"]}-thumb.jpg" width="360" height="360" loading="lazy" alt="Euclid visible-band cutout of {e(f["name"])}">'
            f'<div class="body"><h3>{e(f["name"])}</h3><div class="meta">{tags(f)}</div><p>{e(f["description"])}</p></div></a>')


def index(F, meta, base):
    feats = sorted({f["feature"] for f in F}, key=lambda k: list(FEATURE).index(k))
    dates = sorted({f["date_found"] for f in F}, reverse=True)
    chips = "".join(f'<button class="chip" type="button" aria-pressed="false" data-f="{k}">{e(FEATURE[k])}</button>' for k in feats)
    body = f"""<main><div class="wrap hero"><div class="eyebrow">Euclid DR1 · Claude Fable 5.2 · open-ended search</div>
<h1>What does an AI notice in the new Euclid sky?</h1>
<p class="lede">Instead of a detector trained for one kind of object, Claude looks at Euclid images and flags whatever seems odd. Fake objects are hidden among the real ones so we can measure what it catches and what it invents. Below is everything it flagged on fresh sky.</p>
<div class="stats"><div class="stat"><b>14 / 24</b><span>planted oddities found with the larger view (9 / 24 before)</span></div>
<div class="stat"><b>3 / 16</b><span>false features on untouched images</span></div>
<div class="stat"><b>117</b><span>fresh-sky catalogue outliers inspected</span></div>
<div class="stat"><b>{len(F)}</b><span>flagged objects listed here</span></div></div>
<p class="notice">These are model suggestions, not discoveries. None has been checked by an astronomer yet. Most are probably ordinary galaxies seen in an unusual way.</p></div>
<div class="filters" role="region" aria-label="Filters"><div class="wrap">
<div class="group" aria-label="Feature"><span class="lbl">Feature</span>{chips}</div>
<div class="group"><label for="conf">Confidence</label><select id="conf"><option value="">Any</option><option value="medium">Medium or high</option><option value="low">Low only</option></select></div>
<div class="group"><label for="cat">Catalogue</label><select id="cat"><option value="">Any</option><option value="no">No named entry</option><option value="yes">Already catalogued</option></select></div>
<div class="group"><label for="int">Interest ≥ <output id="intv">2.6</output></label><input id="int" type="range" min="2.6" max="5" step="0.1" value="2.6"></div>
<div class="group"><label for="date">Found</label><select id="date"><option value="">Any date</option>{"".join(f'<option>{d}</option>' for d in dates)}</select></div>
<div class="group"><label for="sort">Sort</label><select id="sort"><option value="interest">Interest</option><option value="date">Newest</option></select></div>
<span class="count" id="count" aria-live="polite"></span></div></div>
<div class="wrap"><div class="grid" id="grid">{"".join(card(f, base) for f in F)}</div><p class="empty" id="empty" hidden>Nothing matches these filters.</p></div>
<div class="wrap"><section class="method" id="method"><div><h2>How it works</h2>
<p>Euclid DR1 tiles are queried from ESA's archive. A classical outlier score on the Euclid catalogue picks the strangest-looking entries. Claude Fable 5.2 sees each one as a 2×2 grid (visible band, colour from the infrared bands, a hard stretch for faint light, and a 3× zoom) and is asked to scan every quadrant, score its interest, and point at the most interesting thing.</p>
<p>Before anything ran on real sky, the rules were written and published: which rendering to use, what counts as a lead, and when to stop. Then each flag is checked against SIMBAD, NED and the ECLIPSE lens catalogue.</p></div>
<div><h2>How far to trust it</h2><table><tr><th>Measured on planted fakes</th><th>Old view</th><th>Larger view</th></tr>
<tr><td>Planted oddities found (of 24)</td><td class="num">9</td><td class="num">14</td></tr>
<tr><td>False features on untouched images (of 16)</td><td class="num">2</td><td class="num">3</td></tr></table>
<p>Small samples: the two views differ by five objects. Earlier, on 2,500 images, a smaller model (Haiku) found 18% of planted oddities. Full results, including the failures, are in the <a href="{REPO}">repository</a>.</p></div></section></div></main>
<script>
const cards=[...document.querySelectorAll('.card')],grid=document.getElementById('grid'),on=new Set();
const q=id=>document.getElementById(id);
function apply(){{const c=q('conf').value,k=q('cat').value,m=+q('int').value,d=q('date').value;q('intv').textContent=m.toFixed(1);let n=0;
for(const el of cards){{const ok=(!on.size||on.has(el.dataset.feature))&&(!c||(c==='low'?el.dataset.conf==='low':el.dataset.conf!=='low'))&&(!k||el.dataset.cat===k)&&(+el.dataset.interest>=m-1e-9)&&(!d||el.dataset.date===d);el.hidden=!ok;n+=ok}}
q('count').textContent=n+' of '+cards.length+' shown';q('empty').hidden=n>0;
const s=q('sort').value;[...cards].sort((a,b)=>s==='date'?b.dataset.date.localeCompare(a.dataset.date)||b.dataset.interest-a.dataset.interest:b.dataset.interest-a.dataset.interest).forEach(el=>grid.appendChild(el));
const p=new URLSearchParams();if(on.size)p.set('feature',[...on].join(','));if(c)p.set('confidence',c);if(k)p.set('catalogued',k);if(m>2.6)p.set('interest',m);if(d)p.set('date',d);
history.replaceState(null,'',(p.toString()?'?'+p:location.pathname))}}
document.querySelectorAll('.chip').forEach(b=>b.addEventListener('click',()=>{{const f=b.dataset.f;on.has(f)?on.delete(f):on.add(f);b.setAttribute('aria-pressed',on.has(f));apply()}}));
['conf','cat','int','date','sort'].forEach(id=>q(id).addEventListener('input',apply));
const p=new URLSearchParams(location.search);(p.get('feature')||'').split(',').filter(Boolean).forEach(f=>{{on.add(f);const b=document.querySelector(`.chip[data-f="${{f}}"]`);b&&b.setAttribute('aria-pressed','true')}});
if(p.get('confidence'))q('conf').value=p.get('confidence');if(p.get('catalogued'))q('cat').value=p.get('catalogued');if(p.get('interest'))q('int').value=p.get('interest');if(p.get('date'))q('date').value=p.get('date');
apply();
</script>"""
    return page("Euclid Oddities: what an AI notices in Euclid DR1", meta["note"], body, base, f"{base}/",
                f"{base}/img/{F[0]['slug']}-thumb.jpg")


def links(f):
    ra, dec = f["ra"], f["dec"]
    return [("SIMBAD", f"https://simbad.cfa.harvard.edu/simbad/sim-coo?Coord={ra}+{dec}&Radius=10&Radius.unit=arcsec"),
            ("NED", f"https://ned.ipac.caltech.edu/conesearch?coordinates={ra}d%20{dec}d&radius=0.17&in_csys=Equatorial&in_equinox=J2000"),
            ("Legacy Survey viewer", f"https://www.legacysurvey.org/viewer?ra={ra}&dec={dec}&layer=ls-dr10&zoom=16"),
            ("ESASky", f"https://sky.esa.int/esasky/?target={ra}%20{dec}&fov=0.02")]


def detail(f, prev, nxt, base):
    cat = ", ".join(e(n) for n in f["catalogue_names"]) or "no named entry (survey detections only)"
    sim = ", ".join(e(n["name"]) for n in f["simbad"]) or "none within 10″"
    ned = ", ".join(e(n["name"]) for n in f["ned"]) or "none within 10″"
    body = f"""<main class="wrap"><div class="crumbs"><a href="{base}/">All finds</a> / {e(f["name"])}</div>
<div class="detail"><div class="viewer"><img id="im" src="{base}/img/{f["slug"]}-marked.jpg" width="1072" height="1072" alt="Euclid cutout of {e(f["name"])}: visible band, colour composite, hard stretch and 3x zoom, with the model's chosen point circled">
<div class="toggle"><button class="chip" type="button" aria-pressed="true" id="mk">Show the model's point</button></div>
<div class="legend"><span>Top left: visible band (VIS)</span><span>Top right: colour, red 1.8 µm · green 1.1 µm · blue visible</span>
<span>Bottom left: hard stretch for faint light</span><span>Bottom right: 3× zoom on the brightest galaxy</span><span>Field: 32″ × 32″, north up</span></div></div>
<div><div class="eyebrow">Found {e(f["date_found"])} · {e(f["model"])} · {e(f["status"])}</div><h1>{e(f["name"])}</h1>
<div class="meta">{tags(f)}<span class="tag">{e(NATURE.get(f["nature"], f["nature"]))}</span></div>
<p class="quote">“{e(f["description"])}”</p><p class="explain">Ordinary explanation the model offered: {e(f["ordinary_explanation"])}</p>
<dl><dt>Position (ICRS)</dt><dd>RA {f["ra"]:.5f}°, Dec {f["dec"]:+.5f}°</dd><dt>Weirdness</dt><dd>{f["weirdness"]} / 5</dd>
<dt>Why it was inspected</dt><dd>{e(f["selection"])}</dd><dt>Catalogued as</dt><dd>{cat}</dd>
<dt>SIMBAD</dt><dd>{sim}</dd><dt>NED</dt><dd>{ned}</dd><dt>ECLIPSE lenses within 10″</dt><dd>{f["eclipse_within_10as"]}</dd>
<dt>Run</dt><dd>{e(f["run"])}, {e(f["rendering"])}</dd></dl>
<div class="links">{"".join(f'<a class="btn" href="{u}" rel="noopener">{n}</a>' for n, u in links(f))}</div>
<p class="notice">Not verified by an astronomer. If you recognise this object or can rule it out, please <a href="{REPO}/issues/new?title={e(f["name"])}">open an issue</a>.</p></div></div>
<nav class="pager">{f'<a href="{base}/{prev["slug"]}/">← {e(prev["name"])}</a>' if prev else '<span></span>'}{f'<a href="{base}/{nxt["slug"]}/">{e(nxt["name"])} →</a>' if nxt else ''}</nav></main>
<script>const b=document.getElementById('mk'),im=document.getElementById('im');b.addEventListener('click',()=>{{const m=b.getAttribute('aria-pressed')!=='true';b.setAttribute('aria-pressed',m);im.src=im.src.replace(/(-marked)?\\.jpg$/,m?'-marked.jpg':'.jpg')}});</script>"""
    title = f"{f['name']}: {FEATURE.get(f['feature'], f['feature']).lower()} flagged by Claude in Euclid DR1"
    return page(title, f["description"], body, base, f"{base}/{f['slug']}/", f"{base}/img/{f['slug']}-thumb.jpg")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--base", default="/oddities")
    a = ap.parse_args()
    out, base = Path(a.out), a.base.rstrip("/")
    D = json.loads((HERE / "data" / "finds.json").read_text(encoding="utf-8"))
    F = sorted(D["finds"], key=lambda f: (-f["interest"], f["slug"]))
    out.mkdir(parents=True, exist_ok=True)
    if (out / "img").exists():
        shutil.rmtree(out / "img")
    shutil.copytree(HERE / "data" / "img", out / "img")
    shutil.copy(HERE / "data" / "finds.json", out / "finds.json")
    (out / "index.html").write_text(index(F, D["meta"], base), encoding="utf-8")
    for i, f in enumerate(F):
        d = out / f["slug"]
        d.mkdir(exist_ok=True)
        (d / "index.html").write_text(detail(f, F[i - 1] if i else None, F[i + 1] if i + 1 < len(F) else None, base), encoding="utf-8")
    print(f"{len(F)} finds -> {out} (base {base or '/'})")


if __name__ == "__main__":
    main()
