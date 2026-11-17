"""Static gallery for Euclid Oddities: one gallery page with filters and one page per find.

Usage: python build.py <out_dir> [--base /euclid-oddities]
Reads data/finds.json and data/img/. Writes <out>/index.html, <out>/<slug>/index.html, <out>/img/, <out>/finds.json.
Standard library only. Visual language: the SimEngine page on indiega.me (no borders or separators, large rounded
cards, pill controls, Space Grotesk / Inter / JetBrains Mono, orange accent).
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
ICON = {"arc": "black-hole", "ring": "black-hole", "pair": "binary-star", "irregular": "galaxy", "diffuse_patch": "nebula",
        "straight_line": "comet", "other": "catalog-object", "none": "catalog-object"}
ICON_DIR = "/assets/icons/object-types"


def icon(feature, size=20):
    return (f'<img class="ico" src="{ICON_DIR}/{ICON.get(feature, "catalog-object")}.webp" width="{size}" height="{size}" alt="" '
            f'aria-hidden="true" loading="lazy">')


NATURE = {"ordinary": "Ordinary", "artefact": "Artefact", "known_rare_class": "Known rare class", "cannot_explain": "Cannot explain"}

# Self-hosted (SpaceSim serves every font from /assets/fonts; no third-party font requests). SIL OFL fonts.
FONTS = ('<link rel="preload" href="/assets/fonts/space-grotesk-variable.woff2" as="font" type="font/woff2" crossorigin>'
         '<link rel="preload" href="/assets/fonts/inter-variable.woff2" as="font" type="font/woff2" crossorigin>')
FONT_FACES = """@font-face{font-family:"Space Grotesk";src:url("/assets/fonts/space-grotesk-variable.woff2") format("woff2");font-weight:300 700;font-display:swap}
@font-face{font-family:"Inter";src:url("/assets/fonts/inter-variable.woff2") format("woff2");font-weight:100 900;font-display:swap}
@font-face{font-family:"JetBrains Mono";src:url("/assets/fonts/jetbrains-mono-variable.woff2") format("woff2");font-weight:100 800;font-display:swap}
"""

CSS = """
:root{--bg:#0b0c0f;--card:#15171c;--card2:#1b1e24;--card3:#23262d;--fg:#eceef2;--silver:#c3c8d0;--dim:#868c97;
--accent:#ff6b1a;--accent-soft:rgba(255,107,26,.14);--ease:cubic-bezier(.16,1,.3,1);--r-xl:40px;--r-lg:28px;--r:20px;--r-sm:14px;
--display:"Space Grotesk",ui-sans-serif,system-ui,sans-serif;--body:"Inter",ui-sans-serif,system-ui,sans-serif;
--mono:"JetBrains Mono",ui-monospace,SFMono-Regular,monospace;color-scheme:dark}
*{box-sizing:border-box}[hidden]{display:none!important}html{background:var(--bg)}
body{margin:0;overflow-x:clip;background:var(--bg);color:var(--fg);font:15px/1.6 var(--body);-webkit-font-smoothing:antialiased;
background-image:radial-gradient(ellipse 60% 30% at 80% 0%,rgba(255,107,26,.07),transparent 70%);background-repeat:no-repeat}
a{color:var(--fg)}a:hover{color:var(--accent)}
:focus-visible{outline:2px solid var(--accent);outline-offset:3px;border-radius:10px}
button,select,input{font:inherit;color:inherit}
.wrap{max-width:1440px;margin:0 auto;padding:0 16px}@media (min-width:760px){.wrap{padding:0 32px}}
header.top{position:sticky;top:0;z-index:20;padding:12px 16px 0}@media (min-width:760px){header.top{padding:12px 32px 0}}
.bar{max-width:1376px;margin:0 auto;display:flex;align-items:center;justify-content:space-between;gap:12px;height:52px;padding:0 8px 0 20px;
border-radius:999px;background:rgba(21,23,28,.78);backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px)}
.brand{font:700 1.02rem/1 var(--display);letter-spacing:-.02em;text-decoration:none;color:var(--fg);display:flex;align-items:center;gap:10px}
.badge{font:500 .58rem/1 var(--mono);letter-spacing:.12em;text-transform:uppercase;padding:5px 8px;border-radius:999px;background:var(--accent-soft);color:var(--accent)}
nav.top{display:flex;gap:2px}nav.top a{font-size:.86rem;color:var(--silver);text-decoration:none;padding:8px 14px;border-radius:999px;transition:background .25s,color .2s}
nav.top a:hover{background:var(--card2);color:var(--fg)}
.intro{padding:44px 0 4px;display:flex;flex-wrap:wrap;align-items:flex-end;justify-content:space-between;gap:12px 32px}
.eyebrow{display:inline-block;font:500 .64rem/1 var(--mono);letter-spacing:.14em;text-transform:uppercase;color:var(--silver);background:var(--card2);padding:7px 11px;border-radius:999px}
.eyebrow b{color:var(--accent);font-weight:500;margin-right:6px}
h1{font:700 clamp(1.9rem,3.6vw,2.7rem)/1.05 var(--display);letter-spacing:-.035em;margin:14px 0 8px}
h1 em,h2 em{font-style:normal;color:var(--accent)}
.lede{color:var(--dim);max-width:62ch;margin:0;font-size:.95rem}
.intro .side{color:var(--dim);font-size:.86rem;max-width:34ch}.intro .side a{color:var(--silver)}
.hero{text-align:center;padding:64px 0 12px}
.hero h1{font:700 clamp(2rem,4.2vw,3.4rem)/1.04 var(--display);letter-spacing:-.04em;margin:0 auto 16px;max-width:20ch}
.hero .lede{font-size:1rem;color:var(--silver);max-width:76ch;margin:0 auto}
.filters{position:sticky;top:72px;z-index:10;margin:24px 0 0;background:rgba(21,23,28,.9);backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);
border-radius:var(--r-lg);padding:12px 14px;display:flex;flex-wrap:wrap;gap:10px 16px;align-items:center}
.group{display:flex;gap:6px;align-items:center;flex-wrap:wrap}
.lbl{font:500 .6rem/1 var(--mono);letter-spacing:.12em;text-transform:uppercase;color:var(--dim);margin:0 4px 0 2px}
.chip{appearance:none;border:0;background:var(--card2);color:var(--silver);border-radius:999px;padding:4px 12px;font-size:.84rem;cursor:pointer;transition:background .25s,color .2s}
.chip:hover{background:var(--card3);color:var(--fg)}.chip[aria-pressed=true]{background:var(--accent-soft);color:var(--accent)}
.count{margin-left:auto;font:500 .66rem/1 var(--mono);letter-spacing:.08em;text-transform:uppercase;color:var(--dim)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:14px;padding:16px 0 56px}
.card{display:flex;flex-direction:column;text-decoration:none;color:inherit;background:var(--card);border-radius:var(--r-lg);padding:10px;transition:transform .5s var(--ease),background .25s}
.card:hover{background:var(--card2);color:inherit}.card.r-common:hover{transform:translateY(-4px)}
.card{position:relative;isolation:isolate;--mx:50%;--my:50%;--rx:0deg;--ry:0deg;--hyp:0}
.card>img,.card>.body{position:relative;z-index:1}
.fx{position:absolute;inset:0;border-radius:inherit;overflow:hidden;pointer-events:none;z-index:0}
.fx .foil,.fx .glare,.fx .sparks{position:absolute;inset:0}
.r-common .fx{display:none}
.card.r-uncommon,.card.r-rare,.card.r-legendary{transform:perspective(900px) rotateX(var(--rx)) rotateY(var(--ry));transition:transform .9s cubic-bezier(.34,1.56,.64,1),background .25s,box-shadow .4s}
.card.on{transition:transform .12s linear,box-shadow .3s}

.card.r-rare{background:radial-gradient(ellipse 80% 45% at 100% 100%,rgba(255,107,26,.05),transparent 70%),var(--card)}
.card.r-legendary{background:radial-gradient(ellipse 90% 55% at 100% 100%,rgba(255,107,26,.09),transparent 70%),var(--card);box-shadow:0 30px 80px -40px rgba(255,107,26,.18)}
.fx .foil{display:none;background:repeating-linear-gradient(115deg,#ff6b1a 0%,#ffd36b 6%,#7dffcf 12%,#6fb7ff 18%,#c58bff 24%,#ff6b9e 30%,#ff6b1a 36%);background-size:300% 300%;background-position:var(--mx) var(--my);mix-blend-mode:color-dodge;opacity:calc(.015 + var(--hyp)*.05);animation:holo-idle 9s ease-in-out infinite alternate;transition:opacity .4s}
.r-rare .fx .foil,.r-legendary .fx .foil{display:block}
.r-legendary .fx .foil{opacity:calc(.03 + var(--hyp)*.08)}
.card.on .fx .foil{animation:none}
@keyframes holo-idle{from{background-position:0% 30%}to{background-position:100% 70%}}
.fx .glare{background:radial-gradient(circle at var(--mx) var(--my),rgba(255,255,255,.14) 0%,rgba(255,255,255,.03) 28%,transparent 55%);mix-blend-mode:overlay;opacity:0;transition:opacity .4s;z-index:3}
.card.on .fx .glare{opacity:1}
.fx .sparks i{position:absolute;width:10px;height:10px;margin:-5px;background:#fff;clip-path:polygon(50% 0,60% 40%,100% 50%,60% 60%,50% 100%,40% 60%,0 50%,40% 40%);opacity:0;animation:twinkle 3.8s ease-in-out infinite;z-index:2}
@keyframes twinkle{0%,70%,100%{opacity:0;transform:scale(.3) rotate(0)}80%{opacity:.45;transform:scale(.8) rotate(45deg)}}

.card>img{display:block;width:100%;height:auto;aspect-ratio:1;object-fit:cover;border-radius:var(--r);background:#000}
.card .body{padding:14px 10px 8px}.card h3{font:600 1rem/1.25 var(--display);letter-spacing:-.01em;margin:0 0 10px}
.meta{display:flex;flex-wrap:wrap;gap:6px;align-items:center}
.ico{display:inline-block;vertical-align:-.18em;margin-right:.45em;object-fit:contain;opacity:.92}.chip .ico{vertical-align:-3px;margin-right:6px}.hd h3 .ico{vertical-align:-4px;margin-right:8px}.info h1 .ico{vertical-align:-.12em;margin-right:12px}
.hd{display:flex;justify-content:space-between;align-items:flex-start;gap:10px}.hd h3{margin:0 0 10px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;min-width:0}
.stars{position:relative;display:inline-block;flex:none;font-size:.95rem;line-height:1;letter-spacing:1px;white-space:nowrap}
.stars .s-off{color:var(--card3)}.stars .s-on{position:absolute;inset:0 auto 0 0;overflow:hidden;color:var(--accent)}
.stars.big{font-size:1.25rem;margin-right:6px}.ival{font:500 .66rem/1 var(--mono);letter-spacing:.06em;text-transform:uppercase;color:var(--dim);margin-right:8px}
.tag{font:500 .62rem/1 var(--mono);letter-spacing:.06em;text-transform:uppercase;color:var(--silver);background:var(--card2);border-radius:999px;padding:6px 9px}
.card:hover .tag{background:var(--card3)}.tag.hi{background:var(--accent-soft);color:var(--accent)}
.card p{color:var(--dim);font-size:.85rem;margin:12px 0 0;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
.empty{color:var(--dim);text-align:center;padding:40px 0}
.method{display:grid;grid-template-columns:1fr 1fr;gap:14px;padding:0 0 40px}
.panel{background:var(--card);border-radius:var(--r-xl);padding:34px}
.panel h2{font:700 clamp(1.5rem,2.4vw,2rem)/1.08 var(--display);letter-spacing:-.035em;margin:14px 0 12px}
.panel p{color:var(--silver);font-size:.93rem}.panel p a{color:var(--fg)}
.rows{display:grid;gap:8px;margin:16px 0}
.row{display:grid;grid-template-columns:1fr 64px 64px;gap:12px;align-items:center;background:var(--card2);border-radius:var(--r-sm);padding:12px 16px;font-size:.88rem}
.row.head{background:none;padding:0 16px;font:500 .6rem/1 var(--mono);letter-spacing:.12em;text-transform:uppercase;color:var(--dim)}
.row .num{font:700 1.05rem/1 var(--display);text-align:right}.row .num.acc{color:var(--accent)}.row.head span:not(:first-child){text-align:right}
footer{color:var(--dim);font-size:.8rem;padding:4px 0 48px}footer a{color:var(--silver)}
.crumbs{font:500 .64rem/1 var(--mono);letter-spacing:.1em;text-transform:uppercase;color:var(--dim);padding:36px 0 16px}.crumbs a{color:var(--silver);text-decoration:none}
.detail{display:grid;grid-template-columns:minmax(0,1.1fr) minmax(0,1fr);gap:14px;padding-bottom:14px;align-items:start}
.viewer{background:var(--card);border-radius:var(--r-xl);padding:12px}
.viewer img{display:block;width:100%;height:auto;border-radius:30px;background:#000}
.zoomwrap{position:relative;cursor:none}@media (hover:none){.zoomwrap{cursor:auto}}
.lens{position:absolute;width:200px;height:200px;border-radius:50%;pointer-events:none;background-repeat:no-repeat;background-color:#000;box-shadow:0 0 0 2px rgba(236,238,242,.85),0 24px 60px -12px rgba(0,0,0,.9);transform:translate(-50%,-50%);opacity:0;transition:opacity .2s}
.zoomwrap.on .lens{opacity:1}
.under{display:flex;flex-wrap:wrap;gap:8px;align-items:center;padding:12px 6px 4px}
.legend{display:grid;grid-template-columns:1fr 1fr;gap:4px 16px;color:var(--dim);font-size:.76rem;padding:8px 10px 8px}
.info{background:var(--card);border-radius:var(--r-xl);padding:34px}
.info h1{font-size:clamp(1.7rem,3vw,2.4rem);margin:16px 0 14px}
.quote{font-size:1.04rem;color:var(--fg);margin:20px 0 8px}
.explain{color:var(--dim);font-size:.9rem;margin:0 0 20px}
.facts{display:grid;border-radius:var(--r);overflow:hidden}
.fact{display:grid;grid-template-columns:150px 1fr;gap:14px;padding:6px 18px;font-size:.84rem;line-height:1.45;background:var(--card2)}.fact:nth-child(even){background:#202329}
.fact span:first-child{color:var(--dim)}code{font:500 .78rem var(--mono);color:var(--silver)}
.links{display:flex;flex-wrap:wrap;gap:8px;margin:20px 0 16px}
.btn{display:inline-flex;align-items:center;gap:8px;border:0;border-radius:999px;padding:10px 16px;background:var(--card2);color:var(--fg);text-decoration:none;font-size:.86rem;font-weight:500;cursor:pointer;transition:background .25s}
.btn:hover{background:var(--card3);color:var(--fg)}.btn.primary{background:var(--fg);color:var(--bg)}.btn.primary:hover{background:#fff;color:var(--bg)}
.btn[aria-pressed=true]{background:var(--accent-soft);color:var(--accent)}
.small{color:var(--dim);font-size:.82rem}.small a{color:var(--silver)}
.pager{display:flex;justify-content:space-between;gap:12px;padding:10px 0 50px}
@media (max-width:900px){.method,.detail{grid-template-columns:1fr}.count{margin-left:0;width:100%}.filters{position:static}
nav.top a:not(.keep){display:none}.fact{grid-template-columns:1fr;gap:0;padding:4px 16px}.panel,.info{padding:24px}.legend{grid-template-columns:1fr}}
@media (prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}.card:hover,.card{transform:none!important}}
"""


def e(s):
    return html.escape(str(s if s is not None else ""))


def page(title, desc, body, base, canonical, image=None):
    og = f'<meta data-route-meta property="og:image" content="{SITE}{image}">' if image else ""
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#070908" />
<link rel="icon" type="image/png" sizes="32x32" href="/assets/favicons/galaxy-32.png" />
<link rel="apple-touch-icon" type="image/png" sizes="180x180" href="/assets/favicons/galaxy-180.png" />
<title>{e(title)}</title><meta name="description" content="{e(desc)}"><link data-route-meta rel="canonical" href="{SITE}{canonical}">
<meta data-route-meta property="og:title" content="{e(title)}"><meta data-route-meta property="og:description" content="{e(desc)}"><meta data-route-meta property="og:type" content="website"><meta data-route-meta property="og:url" content="{SITE}{canonical}">{og}
<meta data-route-meta name="twitter:card" content="summary_large_image">{FONTS}<style>{FONT_FACES}{CSS}</style></head><body>
<header class="top"><div class="bar"><a class="brand" href="{base}/">Euclid Oddities <span class="badge">Beta</span></a>
<nav class="top"><a href="{base}/#method">Method</a><a href="{REPO}">Data &amp; rules</a><a class="keep" href="/">SpaceSim</a></nav></div></header>
{body}
<footer><div class="wrap">Images: ESA Euclid DR1 (ESA/Euclid/Euclid Consortium), rendered by this project. Catalogue checks: SIMBAD, NED, ECLIPSE.
Every entry is an unverified suggestion made by a language model. Code, pre-registration and raw results on <a href="{REPO}">GitHub</a>.</div></footer>
</body></html>"""


def tags(f):
    hi = " hi" if f["confidence"] in ("medium", "high") else ""
    return (f'<span class="tag">{e(FEATURE.get(f["feature"], f["feature"]))}</span>'
            f'<span class="tag{hi}">{e(f["confidence"])} conf.</span>')


def stars(v, big=False):
    pct = max(0.0, min(1.0, float(v) / 5)) * 100
    return (f'<span class="stars{" big" if big else ""}" role="img" aria-label="Interest {v} out of 5" title="Interest {v} / 5">'
            f'<span class="s-off">★★★★★</span><span class="s-on" style="width:{pct:.0f}%">★★★★★</span></span>')


def seg(key, label, opts):
    return (f'<div class="group seg" data-k="{key}" role="group" aria-label="{e(label)}"><span class="lbl">{e(label)}</span>'
            + "".join(f'<button class="chip" type="button" data-v="{e(v)}" aria-pressed="false">{e(t)}</button>' for v, t in opts) + "</div>")


RARITY = [(3.0, "legendary", "Legendary"), (2.4, "rare", "Rare"), (2.0, "uncommon", "Uncommon"), (0, "common", "Common")]


def rarity(f):
    return next((k, t) for lim, k, t in RARITY if f["weirdness"] >= lim)


SPARKS = [(16, 20, 0), (80, 12, .9), (88, 52, 1.7), (24, 46, 2.4), (64, 34, 3.1)]


def card(f, base):
    rk, rt = rarity(f)
    sp = "".join(f'<i style="left:{x}%;top:{y}%;animation-delay:{d}s"></i>' for x, y, d in SPARKS)
    fx = ('<span class="fx" aria-hidden="true"><span class="foil"></span>'
          + (f'<span class="sparks">{sp}</span>' if rk == "legendary" else "")
          + '<span class="glare"></span></span>')
    return (f'<a class="card r-{rk}" href="{base}/{f["slug"]}/" data-feature="{e(f["feature"])}" data-conf="{e(f["confidence"])}" data-rarity="{rk}" '
            f'data-interest="{f["interest"]}" data-cat="{"yes" if f["catalogued"] else "no"}" data-date="{e(f["date_found"])}" data-model="{e(f["model"])}">{fx}'
            f'<img src="{base}/img/{f["slug"]}-thumb.jpg" width="360" height="360" loading="lazy" alt="Euclid visible-band cutout of {e(f["name"])}">'
            f'<div class="body"><div class="hd"><h3>{icon(f["feature"])}{e(f["name"])}</h3>{stars(f["interest"])}</div><div class="meta">{tags(f)}</div><p>{e(f["description"])}</p></div></a>')


def index(F, meta, base):
    feats = sorted({f["feature"] for f in F}, key=lambda k: list(FEATURE).index(k))
    dates = sorted({f["date_found"] for f in F}, reverse=True)
    models = sorted({f["model"] for f in F})
    chips = "".join(f'<button class="chip" type="button" aria-pressed="false" data-f="{k}">{icon(k, 16)}{e(FEATURE[k])}</button>' for k in feats)
    body = f"""<main class="wrap"><section class="hero">
<h1>Unusual galaxies and lens candidates in <em>Euclid DR1</em></h1>
<p class="lede">Claude Fable 5.2 searched fresh images from ESA's Euclid space telescope for anything that looked odd: tidal streams, possible gravitational lenses, oddly shaped galaxies. Fake objects were planted among the real ones to measure how far to trust it. None of these {len(F)} finds has been checked by an astronomer yet.</p></section>
<div class="filters" role="region" aria-label="Filters">
<div class="group" aria-label="Feature"><span class="lbl">Feature</span>{chips}</div>
{seg("conf", "Confidence", [("", "Any"), ("medium", "Medium+"), ("low", "Low")])}
{seg("cat", "Catalogue", [("", "Any"), ("no", "Not catalogued"), ("yes", "Catalogued")])}
{seg("int", "Interest", [("", "Any"), ("3", "≥ 3.0"), ("3.5", "≥ 3.5")])}
{seg("date", "Found", [("", "Any")] + [(d, d) for d in dates])}
{seg("model", "Model", [("", "Any")] + [(m, m.replace("Claude ", "")) for m in models])}
{seg("sort", "Sort", [("interest", "Interest"), ("date", "Newest")])}
<span class="count" id="count" aria-live="polite"></span></div>
<div class="grid" id="grid">{"".join(card(f, base) for f in F)}</div><p class="empty" id="empty" hidden>Nothing matches these filters.</p>
<section class="method" id="method"><div class="panel"><span class="eyebrow"><b>01</b>Method</span><h2>How it <em>works</em></h2>
<p>Euclid DR1 tiles come from ESA's archive. A classical outlier score on the Euclid catalogue picks the strangest-looking entries. Claude Fable 5.2 sees each one as a 2×2 grid (visible band, colour from the infrared bands, a hard stretch for faint light, and a 3× zoom), is asked to scan every quadrant, and points at the most interesting thing.</p>
<p>The rules were written and published before anything ran on real sky. Each flag is then checked against SIMBAD, NED and the ECLIPSE lens catalogue. None has been checked by an astronomer yet: most are probably ordinary galaxies seen in an unusual way.</p></div>
<div class="panel"><span class="eyebrow"><b>02</b>Trust</span><h2>How far to <em>trust</em> it</h2>
<div class="rows"><div class="row head"><span>Measured on planted fakes</span><span>Old view</span><span>Larger view</span></div>
<div class="row"><span>Planted oddities found (of 24)</span><span class="num">9</span><span class="num acc">14</span></div>
<div class="row"><span>False features on untouched images (of 16)</span><span class="num">2</span><span class="num">3</span></div>
<div class="row"><span>Fresh-sky outliers inspected</span><span class="num"></span><span class="num">117</span></div>
<div class="row"><span>Flagged and listed here</span><span class="num"></span><span class="num">{len(F)}</span></div></div>
<p>Small samples: the two views differ by five objects. Full results, failures included, are on <a href="{REPO}">GitHub</a>.</p></div></section></main>
<script>
const cards=[...document.querySelectorAll('.card')],grid=document.getElementById('grid'),on=new Set();
const st={{conf:'',cat:'',int:'',date:'',model:'',sort:'interest'}};
function sync(){{document.querySelectorAll('.seg').forEach(g=>g.querySelectorAll('.chip').forEach(b=>b.setAttribute('aria-pressed',st[g.dataset.k]===b.dataset.v)))}}
function apply(){{let n=0;const m=+st.int||0;
for(const el of cards){{const ok=(!on.size||on.has(el.dataset.feature))&&(!st.conf||(st.conf==='low'?el.dataset.conf==='low':el.dataset.conf!=='low'))&&(!st.cat||el.dataset.cat===st.cat)&&(+el.dataset.interest>=m-1e-9)&&(!st.date||el.dataset.date===st.date)&&(!st.model||el.dataset.model===st.model);el.hidden=!ok;n+=ok}}
document.getElementById('count').textContent=n+' of '+cards.length+' shown';document.getElementById('empty').hidden=n>0;
[...cards].sort((a,b)=>st.sort==='date'?b.dataset.date.localeCompare(a.dataset.date)||b.dataset.interest-a.dataset.interest:b.dataset.interest-a.dataset.interest).forEach(el=>grid.appendChild(el));
const p=new URLSearchParams();if(on.size)p.set('feature',[...on].join(','));for(const k in st)if(st[k]&&!(k==='sort'&&st[k]==='interest'))p.set(k,st[k]);
history.replaceState(null,'',(p.toString()?'?'+p:location.pathname));sync()}}
document.querySelectorAll('.chip[data-f]').forEach(b=>b.addEventListener('click',()=>{{const f=b.dataset.f;on.has(f)?on.delete(f):on.add(f);b.setAttribute('aria-pressed',on.has(f));apply()}}));
document.querySelectorAll('.seg').forEach(g=>g.querySelectorAll('.chip').forEach(b=>b.addEventListener('click',()=>{{st[g.dataset.k]=b.dataset.v;apply()}})));
const p=new URLSearchParams(location.search);(p.get('feature')||'').split(',').filter(Boolean).forEach(f=>{{on.add(f);const b=document.querySelector(`.chip[data-f="${{f}}"]`);b&&b.setAttribute('aria-pressed','true')}});
for(const k in st)if(p.get(k))st[k]=p.get(k);
apply();
if(matchMedia('(hover:hover)').matches&&!matchMedia('(prefers-reduced-motion:reduce)').matches)cards.filter(c=>c.dataset.rarity!=='common').forEach(c=>{{
const T={{uncommon:6,rare:9,legendary:12}}[c.dataset.rarity];
c.addEventListener('pointermove',ev=>{{const r=c.getBoundingClientRect(),x=(ev.clientX-r.left)/r.width,y=(ev.clientY-r.top)/r.height;
c.style.setProperty('--mx',x*100+'%');c.style.setProperty('--my',y*100+'%');c.style.setProperty('--rx',(-(y-.5)*T)+'deg');c.style.setProperty('--ry',((x-.5)*T*1.2)+'deg');
c.style.setProperty('--hyp',Math.min(1,Math.hypot(x-.5,y-.5)*2));c.classList.add('on')}});
c.addEventListener('pointerleave',()=>{{c.classList.remove('on');c.style.setProperty('--rx','0deg');c.style.setProperty('--ry','0deg')}})}});
</script>"""
    return page("Unusual galaxies and lens candidates in Euclid DR1 | Euclid Oddities", f"{len(F)} unusual objects in ESA Euclid DR1 images flagged by Claude Fable 5.2: possible gravitational lenses, tidal streams and odd galaxies, with catalogue checks. Unverified.", body, base, base,
                f"{base}/img/{F[0]['slug']}-thumb.jpg")


def links(f):
    ra, dec = f["ra"], f["dec"]
    return [("SIMBAD", f"https://simbad.cfa.harvard.edu/simbad/sim-coo?Coord={ra}+{dec}&Radius=10&Radius.unit=arcsec"),
            ("NED", f"https://ned.ipac.caltech.edu/conesearch?coordinates={ra}d%20{dec}d&radius=0.17&in_csys=Equatorial&in_equinox=J2000"),
            ("Legacy Survey", f"https://www.legacysurvey.org/viewer?ra={ra}&dec={dec}&layer=ls-dr10&zoom=16"),
            ("ESASky", f"https://sky.esa.int/esasky/?target={ra}%20{dec}&fov=0.02")]


def detail(f, prev, nxt, base):
    cat = ", ".join(e(n) for n in f["catalogue_names"]) or "No named entry (survey detections only)"
    sim = ", ".join(e(n["name"]) for n in f["simbad"]) or "None within 10″"
    ned = ", ".join(e(n["name"]) for n in f["ned"]) or "None within 10″"
    facts = [("Position (ICRS)", f'RA {f["ra"]:.5f}°, Dec {f["dec"]:+.5f}°'), ("Weirdness", f'{f["weirdness"]} / 5'),
             ("Model's reading", e(NATURE.get(f["nature"], f["nature"]))), ("Why inspected", e(f["selection"])),
             ("Catalogued as", cat), ("SIMBAD", sim), ("NED", ned), ("ECLIPSE lenses ≤ 10″", f["eclipse_within_10as"]),
             ("Found", f'{e(f["date_found"])} by {e(f["model"])} (<code>{e(f.get("model_id", ""))}</code>)'),
             ("Effort", f'{e(f.get("effort", "not recorded"))} · {f.get("thinking_tokens", 0)} thinking tokens'),
             ("Harness", e(f.get("harness", ""))), ("Run", f'{e(f["run"])}, {e(f["rendering"])}')]
    body = f"""<main class="wrap"><div class="crumbs"><a href="{base}/">All finds</a> / {e(f["name"])}</div>
<div class="detail"><div class="viewer"><div class="zoomwrap" id="zw"><img id="im" src="{base}/img/{f["slug"]}-marked.jpg" width="1072" height="1072" alt="Euclid cutout of {e(f["name"])}: visible band, colour composite, hard stretch and 3x zoom, with the model's chosen point circled"><div class="lens" id="lens" aria-hidden="true"></div></div>
<div class="under"><button class="btn" type="button" aria-pressed="true" id="mk">Model's point shown</button></div>
<div class="legend"><span>Top left · visible band (VIS)</span><span>Top right · colour: 1.8 µm, 1.1 µm, visible</span>
<span>Bottom left · hard stretch for faint light</span><span>Bottom right · 3× zoom on the brightest galaxy</span><span>Field 32″ × 32″, north up</span></div></div>
<div class="info"><h1>{icon(f["feature"], 34)}{e(f["name"])}</h1>
<div class="meta">{stars(f["interest"], True)}<span class="ival">{f["interest"]} / 5 interest</span>{tags(f)}</div>
<p class="quote">“{e(f["description"])}”</p><p class="explain">Ordinary explanation offered by the model: {e(f["ordinary_explanation"])}</p>
<div class="facts">{"".join(f'<div class="fact"><span>{k}</span><span>{v}</span></div>' for k, v in facts)}</div>
<div class="links">{"".join(f'<a class="btn" href="{u}" rel="noopener">{n} ↗</a>' for n, u in links(f))}</div>
<p class="small">Unverified model suggestion. Recognise it, or can rule it out? <a href="{REPO}/issues/new?title={e(f["name"])}">Tell us on GitHub</a>.</p></div></div>
<nav class="pager">{f'<a class="btn" href="{base}/{prev["slug"]}/">← {e(prev["name"])}</a>' if prev else '<span></span>'}{f'<a class="btn" href="{base}/{nxt["slug"]}/">{e(nxt["name"])} →</a>' if nxt else ''}</nav></main>
<script>const zw=document.getElementById('zw'),lens=document.getElementById('lens'),Z=3;
if(matchMedia('(hover:hover)').matches){{zw.addEventListener('pointermove',ev=>{{const r=im.getBoundingClientRect(),x=ev.clientX-r.left,y=ev.clientY-r.top;
if(x<0||y<0||x>r.width||y>r.height){{zw.classList.remove('on');return}}zw.classList.add('on');lens.style.left=x+'px';lens.style.top=y+'px';
lens.style.backgroundImage=`url("${{im.currentSrc||im.src}}")`;lens.style.backgroundSize=`${{r.width*Z}}px ${{r.height*Z}}px`;
lens.style.backgroundPosition=`${{100-x*Z}}px ${{100-y*Z}}px`}});zw.addEventListener('pointerleave',()=>zw.classList.remove('on'))}}
const b=document.getElementById('mk'),im=document.getElementById('im');b.addEventListener('click',()=>{{const m=b.getAttribute('aria-pressed')!=='true';b.setAttribute('aria-pressed',m);b.textContent=m?"Model's point shown":"Show the model's point";im.src=im.src.replace(/(-marked)?\\.jpg$/,m?'-marked.jpg':'.jpg')}});</script>"""
    title = f"{f['name']}: {FEATURE.get(f['feature'], f['feature']).lower()} flagged by Claude in Euclid DR1"
    return page(title, f["description"], body, base, f"{base}/{f['slug']}", f"{base}/img/{f['slug']}-thumb.jpg")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--base", default="/euclid-oddities")
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
