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
           "irregular": "Irregular", "other": "Other", "none": "None",
           "radio_dark": "Radio, no Euclid source", "wd_irfaint": "Faint moving star"}
ICON = {"arc": "black-hole", "ring": "black-hole", "pair": "binary-star", "irregular": "galaxy", "diffuse_patch": "nebula",
        "straight_line": "comet", "other": "catalog-object", "none": "catalog-object", "radio_dark": "galaxy", "wd_irfaint": "catalog-object"}
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
@view-transition{navigation:auto}
::view-transition-group(*){animation-duration:.55s;animation-timing-function:cubic-bezier(.16,1,.3,1)}
::view-transition-old(root),::view-transition-new(root){animation-duration:.3s}
::view-transition-image-pair(*){isolation:auto}
::view-transition-old(*),::view-transition-new(*){height:100%;object-fit:cover}
@media (prefers-reduced-motion:reduce){::view-transition-group(*),::view-transition-old(*),::view-transition-new(*){animation:none!important}}
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
nav.top{display:flex;gap:2px}.site-header__actions{display:flex;align-items:center;gap:6px;min-width:0}.bar .spacesim-account{height:40px;min-height:40px;border-radius:999px;background:var(--card2)}.bar .spacesim-account:hover{background:var(--card3)}nav.top a{font-size:.86rem;color:var(--silver);text-decoration:none;padding:8px 14px;border-radius:999px;transition:background .25s,color .2s}
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
.doi{display:inline-block;margin-top:22px;line-height:0}.doi img{height:20px;width:auto}.doi span{padding:7px 11px}.doi span:first-child{background:var(--card3);color:var(--silver)}.doi span:last-child{background:var(--accent-soft);color:var(--accent)}.doi:hover span:last-child{background:rgba(255,107,26,.24)}
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
.row.log{grid-template-columns:minmax(0,2fr) 64px 64px 64px minmax(0,2fr)}.row.log .small{color:var(--dim)}
@media (max-width:700px){.row.log{grid-template-columns:1fr 48px 48px 48px}.row.log>span:last-child{grid-column:1/-1}}
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
.facts{display:grid;border-radius:var(--r)}.fact:first-child{border-radius:var(--r) var(--r) 0 0}.fact:last-child{border-radius:0 0 var(--r) var(--r)}.fact:only-child{border-radius:var(--r)}
.fact{display:grid;grid-template-columns:150px 1fr;gap:14px;padding:6px 18px;font-size:.84rem;line-height:1.45;background:var(--card2)}.fact:nth-child(even){background:#202329}
.fact span:first-child{color:var(--dim)}code{font:500 .78rem var(--mono);color:var(--silver)}
.links{display:flex;flex-wrap:wrap;gap:8px;margin:20px 0 16px}
.btn{display:inline-flex;align-items:center;gap:8px;border:0;border-radius:999px;padding:10px 16px;background:var(--card2);color:var(--fg);text-decoration:none;font-size:.86rem;font-weight:500;cursor:pointer;transition:background .25s}
.btn:hover{background:var(--card3);color:var(--fg)}.btn.primary{background:var(--fg);color:var(--bg)}.btn.primary:hover{background:#fff;color:var(--bg)}
.btn[aria-pressed=true]{background:var(--accent-soft);color:var(--accent)}
.small{color:var(--dim);font-size:.82rem}.small a{color:var(--silver)}
.reviews{background:var(--card);border-radius:var(--r-xl);padding:30px 34px;margin:0 0 14px}.reviews h2{font:700 1.5rem/1.1 var(--display);letter-spacing:-.03em;margin:0 0 6px}.reviews>.small{margin:0 0 18px}.rv-img{display:block;width:100%;border-radius:var(--r)}.rv-zoom{max-width:720px;margin-top:12px}.review+.review{margin-top:18px}.rv-hd{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin-bottom:10px}.tag.v-closer{background:var(--accent-soft);color:var(--accent)}.tag.v-split{color:var(--accent-strong)}.tag.v-star,.tag.v-artefact{color:var(--dim)}
.model{display:inline-flex;align-items:center;gap:6px;position:relative;font-weight:500;color:var(--fg);white-space:nowrap}.mlogo{width:15px;height:15px;flex:none}.model[data-tip]{cursor:help}.fact .model[data-tip]::after{left:auto;right:0}.model[data-tip]:hover::after,.model[data-tip]:focus-visible::after{content:attr(data-tip);position:absolute;left:0;bottom:calc(100% + 8px);z-index:30;width:max-content;max-width:min(320px,80vw);white-space:normal;background:var(--card3);color:var(--silver);font:400 .78rem/1.45 var(--body);padding:10px 12px;border-radius:var(--r-sm);box-shadow:0 18px 40px -18px rgba(0,0,0,.9)}
.model{vertical-align:middle;line-height:1}.model .mlogo{display:block}.rv-sum{display:grid;border-radius:var(--r);overflow:hidden;margin:4px 0 18px}.rv-row{display:grid;grid-template-columns:210px 120px 64px 1fr;gap:14px;align-items:center;padding:9px 16px;background:var(--card2);text-decoration:none;color:var(--silver);font-size:.86rem}.rv-row:nth-child(even){background:#202329}.rv-row:hover{background:var(--card3);color:var(--fg)}.rv-conf{color:var(--dim);font-size:.78rem}.rv-row .tag{justify-self:start}.rv-line{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.tabs{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 12px}.tab{appearance:none;border:0;background:var(--card2);color:var(--silver);border-radius:999px;padding:7px 14px;cursor:pointer;font:inherit;font-size:.86rem}.tab .model{color:inherit}.tab:hover{background:var(--card3)}.tab[aria-selected=true]{background:var(--accent-soft);color:var(--accent)}.rv-title{display:flex;flex-wrap:wrap;gap:10px;align-items:center;font:500 .95rem/1 var(--body);margin:4px 0 12px}.teaser{display:flex;flex-wrap:wrap;gap:10px;align-items:center;text-decoration:none;background:var(--card2);border-radius:var(--r-sm);padding:10px 14px;margin:0 0 18px}.teaser:hover{background:var(--card3)}.stack{display:inline-flex;align-items:center;padding-left:6px}.stack-i{display:grid;place-items:center;width:26px;height:26px;border-radius:50%;background:var(--card3);margin-left:-6px;box-shadow:0 0 0 2px var(--card2);color:var(--fg)}.stack-i .mlogo{width:14px;height:14px}.teaser:hover .stack-i{box-shadow:0 0 0 2px var(--card3)}.sr{position:absolute;width:1px;height:1px;overflow:hidden;clip-path:inset(50%);white-space:nowrap}.teaser .small{margin-left:auto}@media (max-width:700px){.rv-row{grid-template-columns:1fr auto;}.rv-conf{display:none}.rv-line{grid-column:1/-1;white-space:normal}}
.verdict{font:500 .66rem/1 var(--mono);letter-spacing:.08em;text-transform:uppercase;background:var(--card3);color:var(--fg);border-radius:999px;padding:7px 11px}
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
<header class="top"><div class="bar"><a class="brand" href="{base}/">Euclid Oddities</a>
<div class="site-header__actions"><nav class="top"><a href="{base}/#log">Log</a><a href="{base}/#method">Method</a><a href="{REPO}">Data &amp; rules</a><a class="keep" href="/">SpaceSim</a></nav></div></div></header>
{body}
<footer><div class="wrap">Images: ESA Euclid DR1 (ESA/Euclid/Euclid Consortium), rendered by this project. Catalogue checks: SIMBAD, NED, ECLIPSE.
Every entry is unverified: image finds are suggestions made by a language model, radio and moving-star candidates come from measurements. Code, pre-registration and raw results on <a href="{REPO}">GitHub</a>, archived with DOI <a href="https://doi.org/10.5281/zenodo.24304792">10.5281/zenodo.24304792</a>.</div></footer>
</body></html>"""


def is_radio(f):
    return f.get("kind") == "radio"


def is_wd(f):
    return f.get("kind") == "wd"


def measured(f):
    """Entries that come from measurements, with no model score."""
    return is_radio(f) or is_wd(f)


def img_base(f, base):
    return f'{base}/img/{"radio/" if is_radio(f) else "wd/" if is_wd(f) else ""}{f["slug"]}'


def wd_finds():
    """Track M candidates (data/wd_faint.json) as gallery entries: faint moving point sources with a near-infrared deficit."""
    fp_ = HERE / "data" / "wd_faint.json"
    if not fp_.exists():
        return []
    D = json.loads(fp_.read_text(encoding="utf-8"))
    out = []
    for c in D["candidates"]:
        desc = (f'Faint point source (r = {c["r"]:.1f}) that moved {c["pm"] * c["base_yr"] / 1000:.2f}″ in {c["base_yr"]:.0f} years. White dwarf candidate, '
                + ("fainter than expected in the near infrared in two colours." if c["firm"] else "somewhat fainter than expected in the near infrared."))
        out.append(dict(c, kind="wd", feature="wd_irfaint", date_found="2026-11-25", run="Faint white dwarf candidates that moved (Track M)",
                        model="No model (measured)", model_id="", interest=0, weirdness=0, confidence="none", catalogued=False,
                        description=desc, status="unverified candidate"))
    return out


def radio_finds():
    """Track R candidates (data/radio_dark.json) as gallery entries. They carry measurements, not a model's opinion."""
    fp_ = HERE / "data" / "radio_dark.json"
    if not fp_.exists():
        return []
    D = json.loads(fp_.read_text(encoding="utf-8"))
    out = []
    for c in D["candidates"]:
        empty = c["cls"] == "empty"
        desc = (f'Compact radio source, {c["peak"]:.0f} mJy/beam at 1.4 GHz. '
                + ("Nothing at its position in the Euclid visible or 1.8 µm image." if empty
                   else "Only a barely visible smudge at its position in Euclid."))
        out.append(dict(c, kind="radio", feature="radio_dark", date_found="2026-11-19", run="Radio sources with no Euclid counterpart (Track R)",
                        model="No model (measured)", model_id="", interest=0, weirdness=0, confidence="none", catalogued=True,
                        description=desc, status="unverified candidate"))
    return out


def tags(f):
    if is_wd(f):
        return (f'<span class="tag hi">{f["pm"]:.0f} mas/yr</span><span class="tag">{"two colours" if f["firm"] else "mild deficit"}</span>'
                + ('<span class="tag">tuning region</span>' if f.get("dev") else ""))
    if is_radio(f):
        return (f'<span class="tag hi">{f["peak"]:.0f} mJy</span><span class="tag">{"empty in Euclid" if f["cls"] == "empty" else "faint host"}</span>'
                + ('<span class="tag">tuning region</span>' if f.get("dev") else ""))
    if "confidence" in f.get("not_asked", []):
        return f'<span class="tag">{e(FEATURE.get(f["feature"], f["feature"]))}</span><span class="tag">wide-field lead</span>'
    hi = " hi" if f["confidence"] in ("medium", "high") else ""
    return (f'<span class="tag">{e(FEATURE.get(f["feature"], f["feature"]))}</span>'
            f'<span class="tag{hi}">{e(f["confidence"])} conf.</span>')


def stars(v, big=False):
    pct = max(0.0, min(1.0, float(v) / 5)) * 100
    return (f'<span class="stars{" big" if big else ""}" role="img" aria-label="Fable interest {v} out of 5" title="Fable interest {v} / 5">'
            f'<span class="s-off">★★★★★</span><span class="s-on" style="width:{pct:.0f}%">★★★★★</span></span>')


def seg(key, label, opts):
    return (f'<div class="group seg" data-k="{key}" role="group" aria-label="{e(label)}"><span class="lbl">{e(label)}</span>'
            + "".join(f'<button class="chip" type="button" data-v="{e(v)}" aria-pressed="false">{e(t)}</button>' for v, t in opts) + "</div>")


RARITY = [(3.0, "legendary", "Legendary"), (2.4, "rare", "Rare"), (2.0, "uncommon", "Uncommon"), (0, "common", "Common")]


def rarity(f):
    return next((k, t) for lim, k, t in RARITY if f["weirdness"] >= lim)


SPARKS = [(16, 20, 0), (80, 12, .9), (88, 52, 1.7), (24, 46, 2.4), (64, 34, 3.1)]


def vt(slug):
    """CSS identifier for view-transition-name (no '+')."""
    return slug.replace("+", "p").replace(".", "_")


RUNS = {"Fable pass 1 (A-fable)": "outliers", "Two-stage test (A-twostage), development field": "twostage",
        "Wide-field pass (A-wide)": "wide"}


def run_key(f):
    if is_radio(f):
        return "radio"
    if is_wd(f):
        return "wd"
    r = f.get("run", "")
    return RUNS.get(r, "wide" if r.startswith("Wide-field pass") else "other")


def promise(f):
    """Ranking for "Most promising": votes for a closer look first, then a penalty when most reviewers call it
    ordinary or a star, then the finder's interest score."""
    R = load_reviews(f["slug"])
    closer = sum(r.get("verdict") == "worth a closer look" for r in R)
    against = sum(r.get("verdict") in ("likely ordinary", "likely star or foreground", "likely artefact") for r in R)
    penalty = 2 if R and against > len(R) / 2 else 0
    if is_wd(f):      # no model score: firm two-colour deficits first, then by significance
        return round(closer * 2 - penalty + (0.6 if f["firm"] else 0.4) + min(-f["sig_jh"], 8) / 40, 3)
    if is_radio(f):   # no model score: emptier and brighter first, on the same 0-1 scale as interest / 5
        return round(closer * 2 - penalty + (0.6 if f["cls"] == "empty" else 0.4) + min(f["peak"], 70) / 200, 3)
    return round(closer * 2 - penalty + f["interest"] / 5, 3)


def card(f, base):
    rk, rt = rarity(f)
    ck, cl = consensus(load_reviews(f["slug"]))
    rv = f'<span class="tag v-{ck}" title="Majority verdict of independent AI reviewers">{e(cl)}</span>' if cl else ""
    sp = "".join(f'<i style="left:{x}%;top:{y}%;animation-delay:{d}s"></i>' for x, y, d in SPARKS)
    fx = ('<span class="fx" aria-hidden="true"><span class="foil"></span>'
          + (f'<span class="sparks">{sp}</span>' if rk == "legendary" else "")
          + '<span class="glare"></span></span>')
    return (f'<a class="card r-{rk}" style="view-transition-name:c-{vt(f["slug"])}" href="{base}/{f["slug"]}/" data-feature="{e(f["feature"])}" data-conf="{e(f["confidence"])}" data-rarity="{rk}" '
            f'data-interest="{f["interest"]}" data-cat="{"yes" if f["catalogued"] else "no"}" data-date="{e(f["date_found"])}" data-model="{e(f["model"])}" data-run="{e(run_key(f))}" data-score="{promise(f)}" data-rev="{ck or "none"}">{fx}'
            f'<img style="view-transition-name:i-{vt(f["slug"])}" src="{img_base(f, base)}-thumb.jpg" width="360" height="360" loading="lazy" alt="Euclid {"1.8 micron" if is_radio(f) else "visible-band"} cutout of {e(f["name"])}">'
            f'<div class="body"><div class="hd"><h3 style="view-transition-name:t-{vt(f["slug"])}">{icon(f["feature"])}{e(f["name"])}</h3>{"" if measured(f) else stars(f["interest"])}</div><div class="meta">{tags(f)}{rv}</div><p>{e(f["description"])}</p></div></a>')


def runs_html():
    fp_ = HERE / "data" / "runs.json"
    if not fp_.exists():
        return ""
    R = json.loads(fp_.read_text(encoding="utf-8")).get("runs", [])
    rows = "".join(
        f'<div class="row log"><span><b>{e(r.get("label", r.get("id", "")))}</b><br><span class="small">{e(r.get("date", ""))} · {e(r.get("model", ""))} · effort {e(r.get("effort", ""))}</span></span>'
        f'<span class="num">{r.get("fields", 0)}</span><span class="num">{r.get("leads", 0)}</span><span class="num">{r.get("published", 0)}</span>'
        f'<span class="small">{round((r.get("weekly_end", 0) - r.get("weekly_start", 0)) * 100)} pts · {e(r.get("status", ""))}</span></div>'
        for r in reversed(R))
    return (f'<section class="panel" id="log" style="margin-bottom:40px"><h2>Search <em>log</em></h2><p>Every pass, newest first, including the ones that '
            f'stopped or failed. Quota is the share of a weekly Claude subscription window used by the pass.</p><div class="rows">'
            f'<div class="row head log"><span>Pass</span><span>Fields</span><span>Leads</span><span>Listed</span><span>Quota · status</span></div>{rows}</div></section>')


def index(F, meta, base):
    n_model, n_radio, n_wd = sum(not measured(f) for f in F), sum(is_radio(f) for f in F), sum(is_wd(f) for f in F)
    feats = sorted({f["feature"] for f in F}, key=lambda k: list(FEATURE).index(k))
    dates = sorted({f["date_found"] for f in F}, reverse=True)
    models = sorted({f["model"] for f in F})
    chips = "".join(f'<button class="chip" type="button" aria-pressed="false" data-f="{k}">{icon(k, 16)}{e(FEATURE[k])}</button>' for k in feats)
    body = f"""<main class="wrap"><section class="hero">
<h1>Oddities in <em>Euclid DR1</em></h1>
<p class="lede">Three searches of fresh data from ESA's Euclid space telescope, run with Claude Fable 5.2. One looks at images for things that seem odd: tidal streams, possible gravitational lenses, oddly shaped galaxies ({n_model} finds, with planted fakes to measure how far to trust the model). One measures where bright radio sources have nothing in Euclid ({n_radio} candidates). One measures which faint stars moved in eight years and picks white dwarf candidates that are too faint in the near infrared ({n_wd} candidates). No model takes part in the selection of the last two. Almost none has been checked by an astronomer.</p>
<a class="doi" href="https://doi.org/10.5281/zenodo.24304792" rel="noopener"><img src="{base}/img/doi-badge.svg" alt="DOI 10.5281/zenodo.24304792" height="20"></a></section>
<div class="filters" role="region" aria-label="Filters">
<div class="group" aria-label="Feature"><span class="lbl">Feature</span>{chips}</div>
{seg("run", "Search", [("", "Any"), ("outliers", "Catalogue outliers"), ("wide", "Wide fields"), ("twostage", "Test fields")] + ([("radio", "Radio, no Euclid source")] if n_radio else []) + ([("wd", "Faint stars that moved")] if n_wd else []))}
{seg("rev", "Second opinion", [("", "Any"), ("closer", "Closer look"), ("split", "Split"), ("ordinary", "Ordinary"), ("star", "Star")])}
{seg("conf", "Confidence", [("", "Any"), ("medium", "Medium+"), ("low", "Low")])}
{seg("cat", "Catalogue", [("", "Any"), ("no", "Not catalogued"), ("yes", "Catalogued")])}
{seg("int", "Interest", [("", "Any"), ("3", "≥ 3.0"), ("3.5", "≥ 3.5")])}
{seg("date", "Found", [("", "Any")] + [(d, d) for d in dates])}
{seg("model", "Model", [("", "Any")] + [(m, m.replace("Claude ", "")) for m in models])}
{seg("sort", "Sort", [("promising", "Most promising"), ("interest", "Fable interest"), ("date", "Newest")])}
<span class="count" id="count" aria-live="polite"></span></div>
<div class="grid" id="grid">{"".join(card(f, base) for f in F)}</div><p class="empty" id="empty" hidden>Nothing matches these filters.</p>
<section class="method" id="method"><div class="panel"><span class="eyebrow"><b>01</b>Method</span><h2>How it <em>works</em></h2>
<p>Euclid DR1 tiles come from ESA's archive. A classical outlier score on the Euclid catalogue picks the strangest-looking entries. Claude Fable 5.2 sees each one as a 2×2 grid (visible band, colour from the infrared bands, a hard stretch for faint light, and a 3× zoom), is asked to scan every quadrant, and points at the most interesting thing.</p>
<p>The rules were written and published before anything ran on real sky. Each flag is then checked against SIMBAD, NED and the ECLIPSE lens catalogue. None has been checked by an astronomer yet: most are probably ordinary galaxies seen in an unusual way.</p></div>
<div class="panel"><span class="eyebrow"><b>02</b>Trust</span><h2>How far to <em>trust</em> it</h2>
<div class="rows"><div class="row head"><span>Measured on planted fakes</span><span>Old view</span><span>Larger view</span></div>
<div class="row"><span>Planted oddities found (of 24)</span><span class="num">9</span><span class="num acc">14</span></div>
<div class="row"><span>False features on untouched images (of 16)</span><span class="num">2</span><span class="num">3</span></div>
<div class="row"><span>Two-stage search on 107″ fields: found at stage 1 / after close look (of 24)</span><span class="num"></span><span class="num">14 / 9</span></div>
<div class="row"><span>Same, close look aimed at the stage-1 point (of 24)</span><span class="num"></span><span class="num">14 / 7</span></div>
<div class="row"><span>Fresh-sky outliers inspected</span><span class="num"></span><span class="num">117</span></div>
<div class="row"><span>Flagged and listed here</span><span class="num"></span><span class="num">{n_model}</span></div></div>
<p>These numbers are about the image search. The radio list and the list of faint moving stars are built from measurements only: <a href="{base}/radio-dark/">radio</a>, <a href="{base}/moving-faint/">moving stars</a>.</p>
<p>Small samples: the two views differ by five objects. Full results, failures included, are on <a href="{REPO}">GitHub</a>.</p></div></section>{runs_html()}</main>
<script>
const cards=[...document.querySelectorAll('.card')],grid=document.getElementById('grid'),on=new Set();
const st={{run:'',rev:'',conf:'',cat:'',int:'',date:'',model:'',sort:'promising'}};
function sync(){{document.querySelectorAll('.seg').forEach(g=>g.querySelectorAll('.chip').forEach(b=>b.setAttribute('aria-pressed',st[g.dataset.k]===b.dataset.v)))}}
function apply(){{let n=0;const m=+st.int||0;
for(const el of cards){{const ok=(!st.run||el.dataset.run===st.run)&&(!st.rev||el.dataset.rev===st.rev)&&(!on.size||on.has(el.dataset.feature))&&(!st.conf||(st.conf==='low'?el.dataset.conf==='low':(el.dataset.conf!=='low'&&el.dataset.conf!=='none')))&&(!st.cat||el.dataset.cat===st.cat)&&(+el.dataset.interest>=m-1e-9)&&(!st.date||el.dataset.date===st.date)&&(!st.model||el.dataset.model===st.model);el.hidden=!ok;n+=ok}}
document.getElementById('count').textContent=n+' of '+cards.length+' shown';document.getElementById('empty').hidden=n>0;
const RV={{closer:0,split:1,ordinary:2,artefact:3,star:3,other:2,none:1}};[...cards].sort((a,b)=>st.sort==='promising'?(b.dataset.score-a.dataset.score)||b.dataset.interest-a.dataset.interest:st.sort==='date'?b.dataset.date.localeCompare(a.dataset.date)||b.dataset.interest-a.dataset.interest:b.dataset.interest-a.dataset.interest).forEach(el=>grid.appendChild(el));
const p=new URLSearchParams();if(on.size)p.set('feature',[...on].join(','));for(const k in st)if(st[k]&&!(k==='sort'&&st[k]==='promising'))p.set(k,st[k]);
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
    return page("Oddities in Euclid DR1: odd galaxies, lens candidates, radio sources with no counterpart | Euclid Oddities", f"{len(F)} unverified finds in ESA Euclid DR1 images: possible gravitational lenses, tidal streams and odd galaxies flagged by Claude Fable 5.2, and radio sources with nothing at their position in Euclid.", body, base, base,
                f"{img_base(F[0], base)}-thumb.jpg")


def links(f):
    ra, dec = f["ra"], f["dec"]
    return [("SIMBAD", f"https://simbad.cfa.harvard.edu/simbad/sim-coo?Coord={ra}+{dec}&Radius=10&Radius.unit=arcsec"),
            ("NED", f"https://ned.ipac.caltech.edu/conesearch?coordinates={ra}d%20{dec}d&radius=0.17&in_csys=Equatorial&in_equinox=J2000"),
            ("Legacy Survey", f"https://www.legacysurvey.org/viewer?ra={ra}&dec={dec}&layer=ls-dr10&zoom=16"),
            ("ESASky", f"https://sky.esa.int/esasky/?target={ra}%20{dec}&fov=0.02")]


def load_reviews(slug):
    d = HERE / "data" / "reviews"
    R = []
    for fp in sorted(d.glob("*.json")) if d.exists() else []:
        try:
            r = json.loads(fp.read_text(encoding="utf-8"))
        except Exception:
            continue
        if r.get("slug") == slug:
            R.append(r)
    order = {"claude-opus-5-5": 1, "claude-fable-5-2": 2, "gpt-6-astra": 3}
    # Measurements without an AI model first, then AI reviewers in a fixed order.
    return sorted(R, key=lambda r: (0 if "no AI" in r.get("reviewer_model", "") else order.get(r.get("reviewer_model", ""), 9)))


VERDICT_SHORT = {"worth a closer look": "Closer look", "likely ordinary": "Likely ordinary", "likely artefact": "Likely artefact",
                 "likely star or foreground": "Likely a star", "plausible, low grade": "Expert: plausible, low grade",
                 "likely chance alignment": "Expert: likely chance alignment"}


def consensus(R):
    """(key, label) of the majority verdict, e.g. ('closer', 'Closer look · 2 of 3')."""
    if not R:
        return "", ""
    from collections import Counter
    c = Counter(r.get("verdict", "") for r in R)
    top = c.most_common()
    if len(top) > 1 and top[0][1] == top[1][1]:
        return "split", f"Reviewers split · {len(R)} reviews"
    v, k = top[0]
    key = {"worth a closer look": "closer", "likely ordinary": "ordinary", "likely artefact": "artefact",
           "likely star or foreground": "star"}.get(v, "other")
    return key, f"{VERDICT_SHORT.get(v, v)} · {k} of {len(R)}"


BASE_URL = "/euclid-oddities"


# Model display names and logos (Simple Icons, CC0). Logos identify the model that produced each entry.
_CLAUDE_D = "m4.7144 15.9555 4.7174-2.6471.079-.2307-.079-.1275h-.2307l-.7893-.0486-2.6956-.0729-2.3375-.0971-2.2646-.1214-.5707-.1215-.5343-.7042.0546-.3522.4797-.3218.686.0608 1.5179.1032 2.2767.1578 1.6514.0972 2.4468.255h.3886l.0546-.1579-.1336-.0971-.1032-.0972L6.973 9.8356l-2.55-1.6879-1.3356-.9714-.7225-.4918-.3643-.4614-.1578-1.0078.6557-.7225.8803.0607.2246.0607.8925.686 1.9064 1.4754 2.4893 1.8336.3643.3035.1457-.1032.0182-.0728-.164-.2733-1.3539-2.4467-1.445-2.4893-.6435-1.032-.17-.6194c-.0607-.255-.1032-.4674-.1032-.7285L6.287.1335 6.6997 0l.9957.1336.419.3642.6192 1.4147 1.0018 2.2282 1.5543 3.0296.4553.8985.2429.8318.091.255h.1579v-.1457l.1275-1.706.2368-2.0947.2307-2.6957.0789-.7589.3764-.9107.7468-.4918.5828.2793.4797.686-.0668.4433-.2853 1.8517-.5586 2.9021-.3643 1.9429h.2125l.2429-.2429.9835-1.3053 1.6514-2.0643.7286-.8196.85-.9046.5464-.4311h1.0321l.759 1.1293-.34 1.1657-1.0625 1.3478-.8804 1.1414-1.2628 1.7-.7893 1.36.0729.1093.1882-.0183 2.8535-.607 1.5421-.2794 1.8396-.3157.8318.3886.091.3946-.3278.8075-1.967.4857-2.3072.4614-3.4364.8136-.0425.0304.0486.0607 1.5482.1457.6618.0364h1.621l3.0175.2247.7892.522.4736.6376-.079.4857-1.2142.6193-1.6393-.3886-3.825-.9107-1.3113-.3279h-.1822v.1093l1.0929 1.0686 2.0035 1.8092 2.5075 2.3314.1275.5768-.3218.4554-.34-.0486-2.2039-1.6575-.85-.7468-1.9246-1.621h-.1275v.17l.4432.6496 2.3436 3.5214.1214 1.0807-.17.3521-.6071.2125-.6679-.1214-1.3721-1.9246L14.38 17.959l-1.1414-1.9428-.1397.079-.674 7.2552-.3156.3703-.7286.2793-.6071-.4614-.3218-.7468.3218-1.4753.3886-1.9246.3157-1.53.2853-1.9004.17-.6314-.0121-.0425-.1397.0182-1.4328 1.9672-2.1796 2.9446-1.7243 1.8456-.4128.164-.7164-.3704.0667-.6618.4008-.5889 2.386-3.0357 1.4389-1.882.929-1.0868-.0062-.1579h-.0546l-6.3385 4.1164-1.1293.1457-.4857-.4554.0608-.7467.2307-.2429 1.9064-1.3114Z"
_OPENAI_D = "M22.2819 9.8211a5.9847 5.9847 0 0 0-.5157-4.9108 6.0462 6.0462 0 0 0-6.5098-2.9A6.0651 6.0651 0 0 0 4.9807 4.1818a5.9847 5.9847 0 0 0-3.9977 2.9 6.0462 6.0462 0 0 0 .7427 7.0966 5.98 5.98 0 0 0 .511 4.9107 6.051 6.051 0 0 0 6.5146 2.9001A5.9847 5.9847 0 0 0 13.2599 24a6.0557 6.0557 0 0 0 5.7718-4.2058 5.9894 5.9894 0 0 0 3.9977-2.9001 6.0557 6.0557 0 0 0-.7475-7.0729zm-9.022 12.6081a4.4755 4.4755 0 0 1-2.8764-1.0408l.1419-.0804 4.7783-2.7582a.7948.7948 0 0 0 .3927-.6813v-6.7369l2.02 1.1686a.071.071 0 0 1 .038.052v5.5826a4.504 4.504 0 0 1-4.4945 4.4944zm-9.6607-4.1254a4.4708 4.4708 0 0 1-.5346-3.0137l.142.0852 4.783 2.7582a.7712.7712 0 0 0 .7806 0l5.8428-3.3685v2.3324a.0804.0804 0 0 1-.0332.0615L9.74 19.9502a4.4992 4.4992 0 0 1-6.1408-1.6464zM2.3408 7.8956a4.485 4.485 0 0 1 2.3655-1.9728V11.6a.7664.7664 0 0 0 .3879.6765l5.8144 3.3543-2.0201 1.1685a.0757.0757 0 0 1-.071 0l-4.8303-2.7865A4.504 4.504 0 0 1 2.3408 7.872zm16.5963 3.8558L13.1038 8.364 15.1192 7.2a.0757.0757 0 0 1 .071 0l4.8303 2.7913a4.4944 4.4944 0 0 1-.6765 8.1042v-5.6772a.79.79 0 0 0-.407-.667zm2.0107-3.0231l-.142-.0852-4.7735-2.7818a.7759.7759 0 0 0-.7854 0L9.409 9.2297V6.8974a.0662.0662 0 0 1 .0284-.0615l4.8303-2.7866a4.4992 4.4992 0 0 1 6.6802 4.66zM8.3065 12.863l-2.02-1.1638a.0804.0804 0 0 1-.038-.0567V6.0742a4.4992 4.4992 0 0 1 7.3757-3.4537l-.142.0805L8.704 5.459a.7948.7948 0 0 0-.3927.6813zm1.0976-2.3654l2.602-1.4998 2.6069 1.4998v2.9994l-2.5974 1.4997-2.6067-1.4997Z"
MODELS = {
    "claude-opus-5-5": ("Claude Opus 5.5", "claude"), "claude-fable-5-2": ("Claude Fable 5.2", "claude"),
    "claude-sonnet-5-5": ("Claude Sonnet 5.5", "claude"), "claude-haiku-5-5": ("Claude Haiku 5.5", "claude"),
    "gpt-6-astra": ("GPT-6 Astra", "openai"),
    "galaxy-light subtraction (photutils isophotes, no AI model)": ("Galaxy-light subtraction", None),
}


def model_badge(model_id, tip=""):
    name, logo = MODELS.get(model_id, (None, None))
    if name is None:
        name, logo = (model_id[:1].upper() + model_id[1:] if model_id else "Unknown"), None
    if logo == "claude":
        svg = f'<svg class="mlogo" viewBox="0 0 24 24" aria-hidden="true"><path fill="#d97757" d="{_CLAUDE_D}"/></svg>'
    elif logo == "openai":
        svg = f'<svg class="mlogo" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="{_OPENAI_D}"/></svg>'
    else:
        svg = '<svg class="mlogo" viewBox="0 0 24 24" aria-hidden="true"><path fill="none" stroke="currentColor" stroke-width="1.8" d="M4 20V4m0 16h16M8 16l3-5 3 3 5-8"/></svg>'
    t = f' data-tip="{e(tip)}" tabindex="0"' if tip else ""
    return f'<span class="model"{t}>{svg}{e(name)}</span>'


def reviews_html(slug):
    R = load_reviews(slug)
    if not R:
        return ""
    # Order: closer look first, then the rest; AI reviewers before measurements kept as given.
    summary, tabs, panels = [], [], []
    for i, r in enumerate(R):
        rid = f"rv-{i}"
        badge = model_badge(r.get("reviewer_model", ""))
        v = r.get("verdict", "")
        vk = {"worth a closer look": "closer", "likely ordinary": "ordinary", "likely artefact": "artefact",
              "likely star or foreground": "star"}.get(v, "other")
        summary.append(f'<a class="rv-row" href="#{rid}" data-tab="{rid}"><span class="rv-who">{badge}</span><span class="tag v-{vk}">{e(VERDICT_SHORT.get(v, v))}</span>'
                       f'<span class="rv-conf">{e(r.get("confidence", ""))}</span><span class="rv-line">{e(r.get("most_likely", ""))}</span></a>')
        tabs.append(f'<button class="tab" type="button" role="tab" id="t-{rid}" aria-controls="{rid}" aria-selected="{"true" if i == 0 else "false"}">{badge}</button>')
        rows = [("What it sees", r.get("what_i_see")), ("Most likely", r.get("most_likely")), ("Against that", r.get("against_it")),
                ("Would settle it", r.get("decisive_test")), ("Catalogues", r.get("catalogue_notes")), ("Note", r.get("note"))]
        img = (f'<div class="zoomwrap rv-zoom"><img class="rv-img" src="{BASE_URL}/img/{e(r["image"])}" alt="Residual images after galaxy-light subtraction" loading="lazy"><div class="lens" aria-hidden="true"></div></div>' if r.get("image") else "")
        panels.append(f"""<article class="review" role="tabpanel" id="{rid}" aria-labelledby="t-{rid}"{"" if i == 0 else " hidden"}>
<h3 class="rv-title">{model_badge(r.get("reviewer_model", ""), r.get("note", ""))}<span class="tag v-{vk}">{e(VERDICT_SHORT.get(v, v))}</span><span class="small">{e(r.get("date", ""))} · {e(r.get("confidence", ""))} confidence</span></h3>
<div class="facts">{"".join(f'<div class="fact"><span>{k}</span><span>{e(x)}</span></div>' for k, x in rows if x)}</div>{img}</article>""")
    script = """<script>(()=>{const T=[...document.querySelectorAll('.reviews .tab')];function show(id){for(const t of T){const on=t.getAttribute('aria-controls')===id;t.setAttribute('aria-selected',on);document.getElementById(t.getAttribute('aria-controls')).hidden=!on}}
T.forEach(t=>t.addEventListener('click',()=>{show(t.getAttribute('aria-controls'));history.replaceState(null,'','#'+t.getAttribute('aria-controls'))}));
document.querySelectorAll('.rv-row').forEach(a=>a.addEventListener('click',ev=>{ev.preventDefault();show(a.dataset.tab);document.getElementById('t-'+a.dataset.tab).scrollIntoView({block:'nearest',behavior:'smooth'})}));
if(location.hash.startsWith('#rv-')&&document.getElementById(location.hash.slice(1)))show(location.hash.slice(1));})()</script>"""
    return (f'<section class="reviews" id="reviews"><h2>Second opinions</h2><p class="small">Independent reviewers (AI models from two families, plus measurements without AI) looked at the image without the original model\'s description. '
            f'Claude reviewers also queried public catalogues themselves. These are not expert opinions, except an entry marked as a reply from a researcher.</p>'
            f'<div class="rv-sum">{"".join(summary)}</div><div class="tabs" role="tablist" aria-label="Reviews">{"".join(tabs)}</div>{"".join(panels)}{script}</section>')


def review_teaser(slug):
    R = load_reviews(slug)
    if not R:
        return ""
    ck, cl = consensus(R)
    def chip(r):
        b = model_badge(r.get("reviewer_model", ""))
        name = MODELS.get(r.get("reviewer_model", ""), (r.get("reviewer_model", ""), None))[0]
        svg = b[b.index("<svg"):b.index("</svg>") + 6]
        return f'<span class="stack-i" title="{e(name)}">{svg}<span class="sr">{e(name)}</span></span>'
    logos = "".join(chip(r) for r in R)
    return f'<a class="teaser" href="#reviews"><span class="tag v-{ck}">{e(cl)}</span><span class="stack">{logos}</span><span class="small">Read the second opinions ↓</span></a>'


def radio_detail(f, prev, nxt, base):
    def num(v, nd=1):
        return "not measured" if v is None else f"{v:.{nd}f}"
    lit = f.get("lit") or {}
    facts = [("Position (ICRS)", f'RA {f["ra"]:.5f}°, Dec {f["dec"]:+.5f}° (radio position, corrected field by field)'),
             ("Radio flux", f'{f["peak"]:.1f} mJy/beam at 1367.5 MHz (RACS-mid), confirmed by RACS-high'),
             ("Radio spectral index", f'{num(f["alpha"], 2)} between 943.5 and 1367.5 MHz · {num(f.get("alpha_mid_high"), 2)} between 1367.5 and 1655.5 MHz (different dates)'),
             ("Euclid, visible", f'{num(f["vis_snr"])} σ in a 1.5″ aperture · 5σ limit {num(f["vis_lim"])} mag'),
             ("Euclid, 1.8 µm", f'{num(f["h_snr"])} σ in a 1.5″ aperture · 5σ limit {num(f["h_lim"])} mag'),
             ("Class", "Empty: no peak above 5σ within 1.5″ in either band" if f["cls"] == "empty" else "Faint host: a peak above 5σ within 1.5″ in at least one band"),
             ("WISE within 5″", "a CatWISE2020 source (may be a neighbour)" if f["wise"] else "none in CatWISE2020"),
             ("Radio surveys", e("; ".join(lit["radio_names"])) if lit.get("radio_names") else (e(f["known_as"]) if f.get("known_as") else "not looked up yet"))]
    sd = f.get("sed")
    if sd:
        lowf = (f'GLEAM {sd["gleam_200"]:.0f} mJy at 200 MHz, in-band index {num(sd["gleam_alpha"], 2)} (72-231 MHz, 2′ beam); index {num(sd["alpha_200_1367"], 2)} from 200 to 1367 MHz'
                if sd.get("gleam_200") else "not in the GLEAM catalogue")
        if sd.get("tgss_150"):
            lowf += f' · TGSS {sd["tgss_150"]:.0f} mJy at 150 MHz'
        facts.append(("Low-frequency radio", lowf))
        if sd.get("w1_snr") is not None:
            facts.append(("unWISE, measured", f'W1 {sd["w1_snr"]:.1f} σ, W2 {num(sd.get("w2_snr"))} σ in a 5.5″ aperture at the position · W1 5σ limit {num(sd.get("w1_lim"))} mag (Vega, no aperture correction)'))
    if lit:
        facts += [("Papers in SIMBAD", e("; ".join(lit["papers"])) if lit.get("papers") else "none attached to an object within 15″"),
                  ("Pulsar within 30″", e(", ".join(lit["pulsar"])) if lit.get("pulsar") else "none in the ATNF catalogue")]
        if lit.get("vlass") is not None:
            facts.append(("VLASS (3 GHz, 2.5″)", e("; ".join(lit["vlass"])) if lit["vlass"] else "no component within 5″"))
    if f.get("dev"):
        facts.append(("Blind?", "No: this source lies in the region where the rules were tuned"))
    facts.append(("Found", f'{e(f["date_found"])} · selection by catalogue and pixel measurements, no model call · image checked for data faults by Claude Fable 5.2'))
    body = f"""<main class="wrap"><div class="crumbs"><a href="{base}/">All finds</a> / {e(f["name"])}</div>
<div class="detail"><div class="viewer" style="view-transition-name:c-{vt(f["slug"])}"><div class="zoomwrap" id="zw"><img id="im" style="view-transition-name:i-{vt(f["slug"])}" src="{img_base(f, base)}-marked.jpg" width="1072" height="528" alt="Euclid cutouts at the radio position of {e(f["name"])}: visible band on the left, 1.8 micron on the right"><div class="lens" id="lens" aria-hidden="true"></div></div>
<div class="legend"><span>Left · visible band (VIS)</span><span>Right · 1.8 µm (H)</span><span>Each 32″ × 32″, north up</span><span>Circle · 1.5″ around the radio position</span></div></div>
<div class="info"><h1 style="view-transition-name:t-{vt(f["slug"])}">{icon(f["feature"], 34)}{e(f["name"])}</h1>
<div class="meta">{tags(f)}</div>
<p class="quote">{e(f["description"])}</p>
<p class="explain">What it could be: a distant radio galaxy too faint for Euclid, a galaxy hidden by dust, or a pulsar in our own Galaxy. Telling them apart needs a spectrum or a pulsation search. This is a known class of object (infrared-faint radio sources). <a href="{base}/radio-dark/">How the list was made</a>.</p>{review_teaser(f["slug"])}
<div class="facts">{"".join(f'<div class="fact"><span>{k}</span><span>{v}</span></div>' for k, v in facts)}</div>
<div class="links">{"".join(f'<a class="btn" href="{u}" rel="noopener">{n} ↗</a>' for n, u in links(f))}</div>
<p class="small">Unverified candidate. Recognise it, or can rule it out? <a href="{REPO}/issues/new?title={e(f["name"])}">Tell us on GitHub</a>.</p></div></div>
{reviews_html(f["slug"])}
<nav class="pager">{f'<a class="btn" href="{base}/{prev["slug"]}/">← {e(prev["name"])}</a>' if prev else '<span></span>'}{f'<a class="btn" href="{base}/{nxt["slug"]}/">{e(nxt["name"])} →</a>' if nxt else ''}</nav></main>
<script>const Z=3;
if(matchMedia('(hover:hover)').matches)document.querySelectorAll('.zoomwrap').forEach(zw=>{{const lens=zw.querySelector('.lens'),img=zw.querySelector('img');
zw.addEventListener('pointermove',ev=>{{const r=img.getBoundingClientRect(),x=ev.clientX-r.left,y=ev.clientY-r.top;
if(x<0||y<0||x>r.width||y>r.height){{zw.classList.remove('on');return}}zw.classList.add('on');lens.style.left=x+'px';lens.style.top=y+'px';
lens.style.backgroundImage=`url("${{img.currentSrc||img.src}}")`;lens.style.backgroundSize=`${{r.width*Z}}px ${{r.height*Z}}px`;
lens.style.backgroundPosition=`${{100-x*Z}}px ${{100-y*Z}}px`}});zw.addEventListener('pointerleave',()=>zw.classList.remove('on'))}});</script>"""
    return page(f"{f['name']}: radio source with no Euclid counterpart", f["description"], body, base, f"{base}/{f['slug']}", f"{img_base(f, base)}-thumb.jpg")


def wd_detail(f, prev, nxt, base):
    has = f.get("nsc_pmra") is not None
    nums = f'{f["nsc_pmra"]:+.0f}, {f["nsc_pmdec"]:+.0f} mas/yr (± {f["nsc_e"]:.0f}) in the NOIRLab Source Catalog DR2' if has else ""
    nsc = {"compatible": "compatible: " + nums, "disagrees": "differs by more than 3σ: " + nums}.get(f["nsc"], "not obtained (no object or query failed)")
    facts = [("Position (ICRS)", f'RA {f["ra"]:.5f}°, Dec {f["dec"]:+.5f}° (Euclid, 2024 to 2025)'),
             ("Motion", f'{f["pm"]:.0f} mas/yr (RA {f["pmx"]:+.0f}, Dec {f["pmy"]:+.0f}; ± {f["e_pm"]:.1f}) over {f["base_yr"]:.1f} years, Euclid against Legacy Surveys DR10'),
             ("Same motion in another data set?", nsc),
             ("Brightness", f'r = {f["r"]:.2f}, Euclid visible = {f["vis"]:.2f} (AB) · not in Gaia'),
             ("Optical colours", f'g − r = {f["gr"]:.2f}, r − z = {f["rz"]:.2f}'),
             ("Reduced proper motion", f'H_r = {f["Hr"]:.1f} (white dwarf box of the rules: above {17.0 + 3.5 * max(f["rz"], -0.5):.1f} at this colour)'),
             ("Near infrared, catalogue", f'J − H = {f["jh"]:.2f} against {f["bb_jh"]:.2f} for a blackbody of the same g − r ({f["sig_jh"]:.1f} σ) · Y − J {f["sig_yj"]:+.1f} σ'),
             ("Near infrared, pixels", f'J − H {abs(f["pix_d_jh"]):.2f} mag below the blackbody in a 0.8″ aperture' + (" (H not detected: lower limit)" if f["h_limit"] else "")),
             ("Signal", f'J {f["j_snr"]:.0f} σ, H {f["h_snr"]:.0f} σ in the Euclid catalogue')]
    if f.get("j_high"):
        facts.append(("Caution", "J is high against both Y and H: this looks more like a fault in J than a deficit in H"))
    if f.get("dev"):
        facts.append(("Blind?", "No: this source lies in the region where the rules were tuned"))
    facts.append(("Found", f'{e(f["date_found"])} · selection by catalogue and pixel measurements, no model call · image checked for data faults by Claude Fable 5.2'))
    body = f"""<main class="wrap"><div class="crumbs"><a href="{base}/">All finds</a> / {e(f["name"])}</div>
<div class="detail"><div class="viewer" style="view-transition-name:c-{vt(f["slug"])}"><div class="zoomwrap" id="zw"><img id="im" style="view-transition-name:i-{vt(f["slug"])}" src="{img_base(f, base)}-marked.jpg" width="1072" height="265" alt="Euclid cutouts of {e(f["name"])} in four bands: visible, Y, J and H"><div class="lens" id="lens" aria-hidden="true"></div></div>
<div class="legend"><span>Left to right · visible, Y (1.1 µm), J (1.4 µm), H (1.8 µm)</span><span>Each 10″ × 10″, north up</span><span>Circle · 1″ around the source</span></div></div>
<div class="info"><h1 style="view-transition-name:t-{vt(f["slug"])}">{icon(f["feature"], 34)}{e(f["name"])}</h1>
<div class="meta">{tags(f)}</div>
<p class="quote">{e(f["description"])}</p>
<p class="explain">What it could be: a cool white dwarf whose atmosphere absorbs near-infrared light (a known, rare kind), an ordinary cool white dwarf with a noisy measurement, or a faint star of the Galactic halo. Telling them apart needs a spectrum, at this brightness on an 8 m telescope. <a href="{base}/moving-faint/">How the list was made</a>.</p>{review_teaser(f["slug"])}
<div class="facts">{"".join(f'<div class="fact"><span>{k}</span><span>{v}</span></div>' for k, v in facts)}</div>
<div class="links">{"".join(f'<a class="btn" href="{u}" rel="noopener">{n} ↗</a>' for n, u in links(f))}</div>
<p class="small">Unverified candidate. Recognise it, or can rule it out? <a href="{REPO}/issues/new?title={e(f["name"])}">Tell us on GitHub</a>.</p></div></div>
{reviews_html(f["slug"])}
<nav class="pager">{f'<a class="btn" href="{base}/{prev["slug"]}/">← {e(prev["name"])}</a>' if prev else '<span></span>'}{f'<a class="btn" href="{base}/{nxt["slug"]}/">{e(nxt["name"])} →</a>' if nxt else ''}</nav></main>"""
    return page(f"{f['name']}: faint white dwarf candidate with a near-infrared deficit", f["description"], body, base, f"{base}/{f['slug']}", f"{img_base(f, base)}-thumb.jpg")


def wd_page(base):
    """Track M: faint white dwarf candidates that moved. Data: data/wd_faint.json, images data/img/wd/."""
    fp_ = HERE / "data" / "wd_faint.json"
    if not fp_.exists():
        return None
    D = json.loads(fp_.read_text(encoding="utf-8"))
    m, C = D["meta"], D["candidates"]
    steps = "".join(f'<div class="row" style="grid-template-columns:1fr 110px"><span>{e(k)}</span><span class="num">{v:,}</span></div>' for k, v in m["steps"])
    top = sorted([c for c in C if c["firm"]], key=lambda c: c["sig_jh"])[:12]

    def wcard(c):
        return (f'<a class="card r-common" href="{base}/{c["slug"]}/"><img src="{base}/img/wd/{c["slug"]}-marked.jpg" width="1072" height="265" loading="lazy" '
                f'style="aspect-ratio:1072/265;height:auto" alt="Euclid cutouts of {e(c["name"])} in four bands">'
                f'<div class="body"><div class="hd"><h3>{e(c["name"])}</h3></div><div class="meta"><span class="tag hi">{c["pm"]:.0f} mas/yr</span>'
                f'<span class="tag">r {c["r"]:.1f}</span><span class="tag">J − H {c["sig_jh"]:.1f} σ</span></div></div></a>')

    body = f"""<main class="wrap"><div class="crumbs"><a href="{base}/">All finds</a> / Faint stars that moved</div>
<section class="hero"><h1>Faint stars that <em>moved</em></h1>
<p class="lede">Comparing Euclid DR1 positions with images taken about eight years earlier gives the motion of stars too faint for the Gaia satellite. {m["wd"]:,} of them move like white dwarfs, the dense remains of dead stars. {m["kept"]} of those are fainter in the near infrared than their optical colour predicts. White dwarfs of that kind are known but rare, and almost all the known ones are brighter. Each entry is an unverified candidate with no spectrum.</p></section>
<section class="method"><div class="panel"><span class="eyebrow"><b>01</b>Method</span><h2>How the list was <em>made</em></h2>
<p>No language model takes part in the selection. For each Euclid tile, the positions of point sources are compared with the Legacy Surveys DR10 catalogue (2013 to 2019), after tying both to the galaxies of the tile, which do not move. A source is kept when it is absent from Gaia and moved by more than 30 mas per year at more than 5 times the error. White dwarf candidates are picked by reduced proper motion: faint for their colour and fast. Their Euclid near-infrared colours are then compared with a blackbody.</p>
<p>The rules were tuned on one 10° × 10° region and published before the rest of the sky was read. Stars already measured by Gaia come out with the right motion to 0.9 mas per year. Claude Fable 5.2 then looked at the images of the near-infrared candidates, only to remove data faults: {m["removed"]} were removed. {m["dev"]} of the {m["kept"]} lie in the tuning region and are not blind.</p>
<p class="small">{e(m["date"])} · selection: catalogue and pixel measurements, no model call · image check: {e(m["model"])}, {e(m["harness"])}</p></div>
<div class="panel"><span class="eyebrow"><b>02</b>Counts</span><h2>What was <em>kept</em></h2>
<div class="rows">{steps}</div>
<p>About {m["area"]:,} square degrees. The same cuts applied to galaxies, which cannot move, predict at most {m["false_box"]} false white dwarf candidates of {m["wd"]:,}. The near-infrared rule with signs reversed selects {m["excess"]} sources, so part of the {m["kept"]} is scatter; {m["firm"]} are firm in two colours.</p>
<p>How interesting: moderate. These are known kinds of objects at the expected density. The list reaches fainter than published ones and carries Euclid near-infrared photometry.</p>
<div class="links"><a class="btn" href="{base}/?run=wd">All {m["kept"]} in the gallery →</a><a class="btn" href="{REPO}/tree/main/track-m-moving-faint" rel="noopener">Full tables, rules and code ↗</a></div></div></section>
<h2 style="margin:8px 0 0">The {len(top)} strongest deficits</h2><p class="small">Left to right: Euclid visible, Y, J, H. 10″ across, north up. A source with a near-infrared deficit fades from J to H more than its neighbours.</p>
<div class="grid" style="grid-template-columns:repeat(auto-fill,minmax(420px,1fr))">{"".join(wcard(c) for c in top)}</div>
<p class="small">Unverified candidates. Recognise one, or can rule it out? <a href="{REPO}/issues/new?title=Track%20M">Tell us on GitHub</a>.</p></main>"""
    return page("Faint white dwarf candidates that moved | Euclid Oddities",
                f"{m['wd']:,} faint white dwarf candidates from Euclid DR1 proper motions, {m['kept']} with a near-infrared deficit. Unverified candidates.", body, base, f"{base}/moving-faint",
                f"{base}/img/wd/{top[0]['slug']}-thumb.jpg" if top else None)


def detail(f, prev, nxt, base):
    if is_wd(f):
        return wd_detail(f, prev, nxt, base)
    if is_radio(f):
        return radio_detail(f, prev, nxt, base)
    cat = ", ".join(e(n) for n in f["catalogue_names"]) or "No named entry (survey detections only)"
    sim = ", ".join(e(n["name"]) for n in f["simbad"]) or "None within 10″"
    ned = ", ".join(e(n["name"]) for n in f["ned"]) or "None within 10″"
    na = f.get("not_asked", [])
    facts = [("Position (ICRS)", f'RA {f["ra"]:.5f}°, Dec {f["dec"]:+.5f}°')]
    if "weirdness" not in na:
        facts.append(("Weirdness", f'{f["weirdness"]} / 5'))
    if "nature" not in na:
        facts.append(("Model's reading", e(NATURE.get(f["nature"], f["nature"]))))
    if "passes_checks" in f:
        facts.append(("Fixed checks", "all passed" if f["passes_checks"] else "failed: " + e(f.get("failed_checks", ""))))
    facts += [("Why inspected", e(f["selection"])),
             ("Catalogued as", cat), ("SIMBAD", sim), ("NED", ned), ("ECLIPSE lenses ≤ 10″", f["eclipse_within_10as"]),
             ("Found", f'{e(f["date_found"])} by ' + model_badge(f.get("model_id", ""), f'Effort: {f.get("effort", "not recorded")} · {f.get("thinking_tokens", 0)} thinking tokens · {f.get("harness", "")} · {f["run"]}, {f["rendering"]}'))]
    body = f"""<main class="wrap"><div class="crumbs"><a href="{base}/">All finds</a> / {e(f["name"])}</div>
<div class="detail"><div class="viewer" style="view-transition-name:c-{vt(f["slug"])}"><div class="zoomwrap" id="zw"><img id="im" style="view-transition-name:i-{vt(f["slug"])}" src="{base}/img/{f["slug"]}-marked.jpg" width="1072" height="1072" alt="Euclid cutout of {e(f["name"])}: visible band, colour composite, hard stretch and 3x zoom, with the model's chosen point circled"><div class="lens" id="lens" aria-hidden="true"></div></div>
<div class="under"><button class="btn" type="button" aria-pressed="true" id="mk">Model's point shown</button></div>
<div class="legend"><span>Top left · visible band (VIS)</span><span>Top right · colour: 1.8 µm, 1.1 µm, visible</span>
<span>Bottom left · hard stretch for faint light</span><span>Bottom right · 3× zoom on the brightest galaxy</span><span>Field 32″ × 32″, north up</span></div></div>
<div class="info"><h1 style="view-transition-name:t-{vt(f["slug"])}">{icon(f["feature"], 34)}{e(f["name"])}</h1>
<div class="meta">{stars(f["interest"], True)}<span class="ival">Fable interest {f["interest"]} / 5</span>{tags(f)}</div>
<p class="quote">“{e(f["description"])}”{' <span class="small">(short label from a one-look scan of a 107″ field)</span>' if f.get("not_asked") else ""}</p>{"" if "ordinary_explanation" in f.get("not_asked", []) else '<p class="explain">Ordinary explanation offered by the model: ' + e(f["ordinary_explanation"]) + '</p>'}{review_teaser(f["slug"])}
<div class="facts">{"".join(f'<div class="fact"><span>{k}</span><span>{v}</span></div>' for k, v in facts)}</div>
<div class="links">{"".join(f'<a class="btn" href="{u}" rel="noopener">{n} ↗</a>' for n, u in links(f))}</div>
<p class="small">Unverified model suggestion. Recognise it, or can rule it out? <a href="{REPO}/issues/new?title={e(f["name"])}">Tell us on GitHub</a>.</p></div></div>
{reviews_html(f["slug"])}
<nav class="pager">{f'<a class="btn" href="{base}/{prev["slug"]}/">← {e(prev["name"])}</a>' if prev else '<span></span>'}{f'<a class="btn" href="{base}/{nxt["slug"]}/">{e(nxt["name"])} →</a>' if nxt else ''}</nav></main>
<script>const Z=3;
if(matchMedia('(hover:hover)').matches)document.querySelectorAll('.zoomwrap').forEach(zw=>{{const lens=zw.querySelector('.lens'),img=zw.querySelector('img');
zw.addEventListener('pointermove',ev=>{{const r=img.getBoundingClientRect(),x=ev.clientX-r.left,y=ev.clientY-r.top;
if(x<0||y<0||x>r.width||y>r.height){{zw.classList.remove('on');return}}zw.classList.add('on');lens.style.left=x+'px';lens.style.top=y+'px';
lens.style.backgroundImage=`url("${{img.currentSrc||img.src}}")`;lens.style.backgroundSize=`${{r.width*Z}}px ${{r.height*Z}}px`;
lens.style.backgroundPosition=`${{100-x*Z}}px ${{100-y*Z}}px`}});zw.addEventListener('pointerleave',()=>zw.classList.remove('on'))}});
const b=document.getElementById('mk'),im=document.getElementById('im');b.addEventListener('click',()=>{{const m=b.getAttribute('aria-pressed')!=='true';b.setAttribute('aria-pressed',m);b.textContent=m?"Model's point shown":"Show the model's point";im.src=im.src.replace(/(-marked)?\\.jpg$/,m?'-marked.jpg':'.jpg')}});</script>"""
    title = f"{f['name']}: {FEATURE.get(f['feature'], f['feature']).lower()} flagged by Claude in Euclid DR1"
    return page(title, f["description"], body, base, f"{base}/{f['slug']}", f"{base}/img/{f['slug']}-thumb.jpg")


def radio_link(base):
    if not (HERE / "data" / "radio_dark.json").exists():
        return ""
    return f'<p class="lede" style="margin-top:14px"><a class="btn" href="{base}/radio-dark/">New: radio sources Euclid cannot see →</a></p>'


def radio_page(base):
    """Track R: radio sources with nothing at their position in Euclid. Data: data/radio_dark.json, images data/img/radio/."""
    fp_ = HERE / "data" / "radio_dark.json"
    if not fp_.exists():
        return None
    D = json.loads(fp_.read_text(encoding="utf-8"))
    m, C = D["meta"], D["candidates"]

    def num(v, nd=1):
        return "" if v is None else f"{v:.{nd}f}"

    def rcard(c):
        cls = "Empty in both bands" if c["cls"] == "empty" else "Faint host"
        return (f'<a class="card r-common" href="{base}/{c["slug"]}/"><img src="{base}/img/radio/{c["slug"]}-marked.jpg" width="1072" height="528" loading="lazy" '
                f'style="aspect-ratio:1072/528;height:auto" alt="Euclid visible (left) and 1.8 micron (right) cutouts at the radio position of {e(c["name"])}">'
                f'<div class="body"><div class="hd"><h3>{e(c["name"])}</h3></div><div class="meta"><span class="tag hi">{c["peak"]:.0f} mJy</span>'
                f'<span class="tag">{cls}</span><span class="tag">index {num(c["alpha"])}</span></div></div></a>')

    steps = "".join(f'<div class="row" style="grid-template-columns:1fr 90px"><span>{e(k)}</span><span class="num">{v}</span></div>' for k, v in m["steps"])
    top = C[:12]
    body = f"""<main class="wrap"><div class="crumbs"><a href="{base}/">All finds</a> / Radio sources with no Euclid counterpart</div>
<section class="hero"><h1>Radio sources Euclid <em>cannot see</em></h1>
<p class="lede">{m["kept"]} compact radio sources from the RACS-mid survey have nothing, or almost nothing, at their position in the Euclid DR1 visible and 1.8 µm images. This is a known class of object (infrared-faint radio sources, where distant radio galaxies are looked for). The list is new for this sky as far as we checked, each entry is an unverified candidate, and a pulsar would look the same.</p></section>
<section class="method"><div class="panel"><span class="eyebrow"><b>01</b>Method</span><h2>How the list was <em>made</em></h2>
<p>No language model takes part in the selection. Radio positions were corrected field by field against bright Euclid galaxies, then the flux was summed in a 1.5″ aperture on the Euclid visible and 1.8 µm mosaics, with the noise measured around each position. A source is kept when both bands show less than 3 times the noise, the data are deep enough, and a second radio survey (RACS-high) sees the same compact source.</p>
<p>The rules were tuned on one 10° × 10° region and published before the rest of the sky was measured. Claude Fable 5.2 then looked at every image, only to remove data faults: {m["removed"]} were removed. {m["dev"]} of the {m["kept"]} lie in the tuning region and are not blind.</p>
<p class="small">{e(m["date"])} · selection: catalogue and pixel measurements, no model call · image check: {e(m["model"])}, {e(m["harness"])}</p></div>
<div class="panel"><span class="eyebrow"><b>02</b>Counts</span><h2>What was <em>kept</em></h2>
<div class="rows">{steps}</div>
<p>Of the {m["kept"]}, {m["empty"]} are empty in both bands and {m["faint"]} show a barely visible host. Median radio spectral index: {m["alpha_med"]:.1f} (steep). {e(m["lit"])}</p>
<div class="links"><a class="btn" href="{base}/?run=radio">All {m["kept"]} in the gallery →</a><a class="btn" href="{REPO}/tree/main/track-r-radio-dark" rel="noopener">Full table, rules and code ↗</a></div></div></section>
<h2 style="margin:8px 0 0">The {len(top)} brightest</h2><p class="small">Left: Euclid visible band. Right: Euclid 1.8 µm. 32″ across, north up. The circle (1.5″ radius) marks the corrected radio position.</p>
<div class="grid" style="grid-template-columns:repeat(auto-fill,minmax(420px,1fr))">{"".join(rcard(c) for c in top)}</div>
<p class="small">Unverified candidates. Recognise one, or can rule it out? <a href="{REPO}/issues/new?title=Track%20R">Tell us on GitHub</a>.</p></main>"""
    return page("Radio sources with no Euclid counterpart | Euclid Oddities",
                f"{m['kept']} compact radio sources with nothing at their position in Euclid DR1 images. Unverified candidates.", body, base, f"{base}/radio-dark",
                f"{base}/img/radio/{top[0]['slug']}.jpg" if top else None)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--base", default="/euclid-oddities")
    a = ap.parse_args()
    out, base = Path(a.out), a.base.rstrip("/")
    global BASE_URL
    BASE_URL = base
    D = json.loads((HERE / "data" / "finds.json").read_text(encoding="utf-8"))
    F = sorted(D["finds"] + radio_finds() + wd_finds(), key=lambda f: (-promise(f), -f["interest"], f["slug"]))
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
    rp = radio_page(base)
    if rp:
        (out / "radio-dark").mkdir(exist_ok=True)
        (out / "radio-dark" / "index.html").write_text(rp, encoding="utf-8")
    wp = wd_page(base)
    if wp:
        (out / "moving-faint").mkdir(exist_ok=True)
        (out / "moving-faint" / "index.html").write_text(wp, encoding="utf-8")
    print(f"{len(F)} finds -> {out} (base {base or '/'}){' + radio-dark page' if rp else ''}")


if __name__ == "__main__":
    main()
