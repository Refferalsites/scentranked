#!/usr/bin/env python3
"""ScentRanked static site generator. Run: python3 build.py  -> writes ./public"""
import json, re, html, os, shutil, datetime, email.utils
from urllib.parse import urlencode

# ===== CENTRAL CONFIG =====
SITE_NAME = "ScentRanked"
SITE_URL = "https://scentranked.netlify.app"
AFFILIATE_PARAMS = {}   # e.g. {"ref": "YOUR_ID"} - appended to every yoovic.com buy link
CONTACT_EMAIL = "hello@scentranked.example"
# ==========================

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, "data", "products.json")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public")
TODAY = datetime.date.today().isoformat()
_raw = json.load(open(SRC))
P = {p["key"]: p for p in (_raw["products"] if isinstance(_raw, dict) else [dict(x, key=k) for k, x in enumerate(_raw)])}
SETTINGS = json.load(open(os.path.join(BASE, "data", "settings.json")))
SEOS = SETTINGS.get("seo", {})
if SETTINGS.get("site_name"): SITE_NAME = SETTINGS["site_name"]
if SETTINGS.get("contact_email"): CONTACT_EMAIL = SETTINGS["contact_email"]
if SETTINGS.get("affiliate_params"):
    from urllib.parse import parse_qsl
    AFFILIATE_PARAMS = dict(parse_qsl(SETTINGS["affiliate_params"].lstrip("?")))
esc = html.escape

def buy_url(u):
    if not AFFILIATE_PARAMS: return u
    return u + ("&" if "?" in u else "?") + urlencode(AFFILIATE_PARAMS)

# idx -> editorial data. "notes": publicly known notes (only where well established); otherwise None and the
# page quotes the retailer listing. Copy is our own editorial opinion - no ratings, no fake reviews.
F = {
 14: dict(slug="bleu-de-chanel-edt", short="Bleu de Chanel EDT", brand="Chanel", family="Fresh woody aromatic",
   notes="Grapefruit, lemon, mint, pink pepper, ginger, nutmeg, jasmine, incense, cedar, sandalwood, vetiver",
   best="The one bottle for office, weekends and dinner", season="All year", occasion="Everyday / office",
   take="If you only own one designer cologne, this is the safest pick on the list. Bright citrus up top, a clean incense-and-woods drydown, and nothing loud or polarizing about it. It reads polished in a meeting and relaxed on a Saturday.",
   pros=["Extremely versatile","Smells expensive without trying hard","Easy blind buy for most people"],
   cons=["Very popular, so not unique","EDT is moderate in projection, not a beast"]),
 47: dict(slug="versace-eros-edt", short="Versace Eros EDT", brand="Versace", family="Aromatic fougère, sweet",
   notes="Mint, green apple, lemon, tonka bean, ambroxan, geranium, vanilla, vetiver, oakmoss, cedar",
   best="Loud, sweet, youthful compliment magnet", season="Fall, winter, spring evenings", occasion="Nights out / clubs",
   take="Eros is famous for one reason: people notice it. Cold mint and green apple lead into a sweet vanilla-tonka base that projects well. It is not subtle, so go easy in the office, but for a night out under $100 it is hard to beat.",
   pros=["Strong projection for the price","Big compliment reputation","Great value"],
   cons=["Easy to overspray","Sweetness can feel heavy in hot weather"]),
 48: dict(slug="versace-eros-flame", short="Versace Eros Flame", brand="Versace", family="Spicy citrus woody",
   notes="Lemon, mandarin, chinotto, black pepper, rosemary, geranium, rose, tonka bean, vanilla, sandalwood, patchouli",
   best="A warmer, more grown-up Eros", season="Fall, winter", occasion="Date night",
   take="Flame swaps Eros's mint-candy opening for zesty citrus and black pepper, then settles into a warm vanilla-woods base. It's a friendlier, more mature take on the line and one of the cheapest bottles here.",
   pros=["Warm and inviting","Cheapest designer bottle on this list","Works for 20s-40s"],
   cons=["Not a hot-weather scent","Less distinctive than original Eros"]),
 0: dict(slug="paco-rabanne-1-million-edt", short="1 Million EDT (Tester)", brand="Paco Rabanne", family="Spicy leather amber",
   notes="Blood mandarin, grapefruit, mint, cinnamon, rose, leather, amber, woody notes",
   best="Classic sweet-spicy party scent", season="Fall, winter", occasion="Nights out",
   take="The gold-bar bottle is a 2000s icon for a reason: cinnamon, sweet amber and soft leather that read warm and flirty. This listing is a tester (plain packaging) at 3.4 oz, which is typically the cheapest way to get the full-size juice.",
   pros=["Iconic, crowd-pleasing","Tester = more juice per dollar","Strong sillage"],
   cons=["Tester packaging (no retail box)","Can be cloying in heat"]),
 38: dict(slug="paco-rabanne-1-million-parfum", short="1 Million Parfum (6.8 oz)", brand="Paco Rabanne", family="Warm, rich",
   notes=None, best="Huge bottle for heavy users", season="Fall, winter", occasion="Date night",
   take="The Parfum concentration of 1 Million in a big 6.8 oz bottle. If you already know you love the 1 Million DNA and wear it often, the size makes it a sensible stock-up.",
   pros=["Very large 6.8 oz size","Parfum concentration"], cons=["Big commitment if you haven't sampled it"]),
 26: dict(slug="jean-paul-gaultier-le-male-edt", short="Le Male EDT (4.2 oz)", brand="Jean Paul Gaultier", family="Aromatic fougère, vanilla",
   notes="Mint, lavender, cardamom, bergamot, artemisia, cinnamon, orange blossom, cumin, vanilla, tonka bean, sandalwood, amber, cedar",
   best="Barbershop-meets-vanilla legend", season="Fall, winter", occasion="Evenings / casual",
   take="Le Male has been a best-seller since the 90s: clean lavender and mint up front, a creamy vanilla-tonka finish. It's sweet, comforting and instantly recognizable. The 4.2 oz bottle makes it great value per ml.",
   pros=["Timeless, recognisable","Generous 4.2 oz size","Cozy, approachable"],
   cons=["Some find it dated","Sweet vanilla base isn't for summer days"]),
 32: dict(slug="jean-paul-gaultier-le-male-le-parfum", short="Le Male Le Parfum", brand="Jean Paul Gaultier", family="Warm spicy vanilla",
   notes="Cardamom, lavender, iris, vanilla, woody notes",
   best="Elegant, dressed-up date scent", season="Fall, winter", occasion="Date night / formal",
   take="Le Parfum is Le Male in a tux: less mint, more cardamom, powdery iris and rich vanilla. It's smooth, dense and noticeably classier than the EDT. One of the strongest date-night picks on the site.",
   pros=["Smooth, sophisticated","Long-lasting EDP intense","Huge compliment reputation"],
   cons=["Too rich for hot days"]),
 31: dict(slug="jean-paul-gaultier-le-beau-le-parfum", short="Le Beau Eau de Parfum Intense", brand="Jean Paul Gaultier", family="Tropical woody amber",
   notes="Pineapple, iris, cypress, ginger, coconut, tonka bean, sandalwood, amber",
   best="Tropical-sweet and very wearable", season="Spring, summer evenings, fall", occasion="Date night / vacation",
   take="Le Beau's intense version leans into creamy coconut, tonka and woods with a fresh, slightly green opening. It feels like a vacation in a bottle, but with enough depth for evenings.",
   pros=["Fun, distinctive coconut-tonka vibe","Under $100"], cons=["2.5 oz bottle","Sweetness won't suit everyone"]),
 2: dict(slug="armani-acqua-di-gio-profondo", short="Acqua di Giò Profondo EDP", brand="Armani", family="Fresh aquatic aromatic",
   notes=None, best="Modern deep-blue aquatic", season="Spring, summer", occasion="Daytime / office / summer",
   take="Profondo is the deeper, more modern take on the classic Acqua di Giò: marine freshness with aromatic herbs and a mineral, woody base. A top-tier hot-weather office scent.",
   pros=["Clean and inoffensive","Great in heat","EDP lasts longer than classic ADG"], cons=["Very safe, not daring"]),
 8: dict(slug="bvlgari-aqva-pour-homme-marine", short="Bvlgari Aqva Pour Homme Marine", brand="Bvlgari", family="Fresh aquatic",
   notes=None, best="Bright, salty beach freshness", season="Summer", occasion="Daytime / beach / gym",
   take="Aqva Marine is pure summer: citrusy mandarin and petitgrain over a breezy marine accord. Light and easy, made for the heat.",
   pros=["Very refreshing","Inoffensive anywhere"], cons=["Lighter longevity","Not an evening scent"]),
 40: dict(slug="prada-luna-rossa-ocean-le-parfum", short="Luna Rossa Ocean Le Parfum", brand="Prada", family="Fresh aquatic aromatic",
   notes=None, best="Clean, sporty-luxe freshness", season="Spring, summer", occasion="Daytime / office",
   take="A polished fresh scent from Prada's sailing-inspired Luna Rossa line, in a refillable bottle. Clean and modern, a smart under-$100 alternative to pricier blue fragrances.",
   pros=["Refillable bottle","Under $100","Office-safe"], cons=["1.6 oz is a small bottle"]),
 36: dict(slug="montblanc-legend-blue-edp", short="Montblanc Legend Blue EDP", brand="Montblanc", family="Woody aromatic, fresh",
   notes=None, best="Mint-fresh blue scent with a modern ambroxan base", season="Spring, summer", occasion="Everyday / office",
   take="Legend Blue opens with spearmint and settles into a smooth woody-ambroxan base. Fresh, clean and very easy to wear daily.",
   pros=["Fresh and mass-appealing","Good daily driver"], cons=["Familiar 'blue' DNA"]),
 6: dict(slug="azzaro-wanted-edt", short="Azzaro Wanted EDT", brand="Azzaro", family="Woody spicy citrus",
   notes="Lemon, ginger, mint, lavender, cardamom, juniper, apple, geranium, tonka bean, vetiver, cedar, amberwood",
   best="Zesty, spicy all-rounder", season="Spring, fall", occasion="Everyday / casual",
   take="Wanted mixes lemon and ginger with cardamom and a warm woody base, so it's fresh enough for day but has some spice and warmth. A versatile, upbeat everyday scent.",
   pros=["Versatile","Fresh-meets-warm balance"], cons=["Less hype than the Most Wanted flankers"]),
 4: dict(slug="azzaro-the-most-wanted-parfum", short="Azzaro The Most Wanted Parfum", brand="Azzaro", family="Spicy amber woody",
   notes=None, best="Dark, sweet, magnetic evening scent", season="Fall, winter", occasion="Date night / nights out",
   take="The Most Wanted Parfum is the boldest member of the Wanted family, spicy, warm and sweet with serious presence. At the listed sale price it's one of the best values on the site. Check the size on the product page before buying.",
   pros=["Big presence","Currently on sale at Yoovic"], cons=["Too heavy for hot weather"]),
 9: dict(slug="carolina-herrera-212-men", short="Carolina Herrera 212 Men EDT", brand="Carolina Herrera", family="Fresh green woody",
   notes=None, best="Clean, peppery-green classic", season="Spring, summer", occasion="Office / everyday",
   take="212 Men is a crisp, slightly peppery green scent on a sandalwood base. Clean and understated, a smart budget office pick.",
   pros=["Office-friendly","Affordable"], cons=["Modest projection"]),
 45: dict(slug="valentino-uomo-born-in-roma-the-gold", short="Valentino Uomo Born in Roma The Gold", brand="Valentino", family="Warm spicy woody",
   notes=None, best="Golden, warm, premium evening scent", season="Fall, winter", occasion="Date night / events",
   take="A warmer, richer flanker of Born in Roma Uomo. Spicy-woody with a luxurious feel, for evenings when you want to stand out without going sweet-candy.",
   pros=["Premium feel","Distinctive studded bottle"], cons=["Pricier than most designer picks here"]),
 13: dict(slug="chanel-allure-homme-sport-extreme", short="Allure Homme Sport Eau Extrême", brand="Chanel", family="Fresh spicy woody",
   notes=None, best="Energetic, fresh-meets-spicy Chanel", season="Spring, summer", occasion="Active / daytime",
   take="Chanel's sportier line, with a cool, fresh opening and a smooth, slightly spicy woody base. Classy fresh option for men who want Chanel quality but something different from Bleu.",
   pros=["Chanel quality","Fresh but with depth"], cons=["Premium price"]),
 19: dict(slug="creed-silver-mountain-water", short="Creed Silver Mountain Water", brand="Creed", family="Citrus fruity woody (niche)",
   notes=None, best="Luxury crisp, clean freshness", season="Spring, summer", occasion="Daytime / special occasions",
   take="The niche splurge for fresh lovers. Cool, crisp citrus and fruit over clean woods and musk, inspired by alpine streams. It's an investment, but it's the kind of 'quietly expensive' freshness designer blues aim for.",
   pros=["Distinctive, refined freshness","Prestige house"], cons=["Expensive"]),
 18: dict(slug="creed-royal-oud", short="Creed Royal Oud", brand="Creed", family="Woody spicy smoky (niche)",
   notes=None, best="Refined oud for formal nights", season="Fall, winter", occasion="Formal / evening",
   take="A polished, wearable woody oud from Creed. Spicy, smoky and dignified, a great entry to oud for US guys who find traditional ouds too intense.",
   pros=["Wearable oud","Luxury statement"], cons=["Very expensive"]),
 39: dict(slug="parfums-de-marly-greenley", short="Parfums de Marly Greenley", brand="Parfums de Marly", family="Fresh green citrus woody (niche)",
   notes=None, best="Green-apple-crisp niche freshness", season="Spring, summer", occasion="Daytime / office",
   take="Greenley is a bright, green, citrusy niche scent with a soft woody base. Fresh and elegant, great for men who want a luxury daytime signature that doesn't smell like the usual blue designers.",
   pros=["Distinctive green freshness","Niche quality"], cons=["Expensive"]),
 1: dict(slug="afnan-9-pm", short="Afnan 9 PM EDP", brand="Afnan", family="Sweet warm (Middle Eastern)",
   notes=None, best="Budget sweet evening scent", season="Fall, winter", occasion="Nights out",
   take="One of the most talked-about budget Middle Eastern fragrances in the US. Sweet, warm and loud for the price. Often compared to big-name sweet designer evening scents.",
   pros=["Extremely affordable","Strong performance for the price"], cons=["Very sweet","Less refined than designers"]),
 30: dict(slug="lattafa-qaed-al-fursan", short="Lattafa Qaed Al Fursan EDP", brand="Lattafa", family="Fruity fresh amber woody",
   notes=None, best="$20 fruity-fresh crowd-pleaser", season="Spring, summer, fall", occasion="Casual / everyday",
   take="A popular Lattafa release with a juicy fruit opening and an amber-woody base. At about $20 it's an easy, low-risk way to try something fun.",
   pros=["Cheapest on the list","Fun, fruity profile"], cons=["Less refined than luxury fruity scents"]),
}
ROUNDUPS = [
 dict(slug="best-compliment-getting-colognes", title="Best Compliment-Getting Colognes for Men",
   h="The colognes people actually ask about.", ids=[47,14,32,0,4,48,45,31],
   intro="'Compliment-getter' usually means three things: decent projection, a pleasant, likeable sweetness or freshness, and a scent that feels familiar enough to read as attractive. These picks have reputations that hold up."),
 dict(slug="best-date-night-colognes", title="Best Date Night Colognes for Men",
   h="Warm, close, memorable.", ids=[32,48,4,31,45,38,18,1],
   intro="Date-night scents should be warmer and a little closer to the skin: vanilla, amber, spice, woods. Spray less than you would outdoors; you want someone to lean in, not walk away."),
 dict(slug="best-summer-colognes", title="Best Summer Colognes for Men",
   h="Fresh scents that survive the heat.", ids=[2,8,40,36,19,39,13,9],
   intro="Heavy sweet scents turn cloying in heat. For summer, think citrus, marine and green notes with a clean woody base. These are the freshest options in the lineup."),
 dict(slug="best-colognes-under-100", title="Best Colognes for Men Under $100",
   h="Designer quality without the designer markup.", ids=[48,47,0,26,31,40,9,4,1,30],
   intro="Every pick here is under $100 at Yoovic at the time we checked (prices change, so confirm on the product page). Sorted roughly by how much fragrance you get for the money."),
]
SOCIAL = {n: (SETTINGS.get("social", {}).get(n.lower()) or "#") for n in ["Instagram", "TikTok", "Pinterest", "X"]}   # edit in /admin > Settings
ANNOUNCE = SETTINGS.get("announcement") or "Free shipping on every order at Yoovic · Expedited US shipping available"
YEAR = datetime.date.today().year
BLOG_CATS = ["Cologne Guides", "Buying Tips", "Seasonal Picks"]
POSTS = []

def price(i): return P[i]["price"]
def pnum(i): return float(re.sub(r"[^\d.]","",P[i]["price"]))
def slugify(s): return re.sub(r"[^a-z0-9]+","-",s.lower()).strip("-")
CSS = open(os.path.join(BASE,"style.css")).read()
BRANDS = sorted({f["brand"] for f in F.values()})
TOP = [i for i in F if P.get(i, {}).get("featured")] or [14,47,32,2,48,0,26,36]
OCC = {"best-compliment-getting-colognes":"Compliment-getters","best-date-night-colognes":"Date night","best-summer-colognes":"Summer","best-colognes-under-100":"Under $100"}

def occasions(i):
    o=[OCC[r["slug"]] for r in ROUNDUPS if i in r["ids"]]
    if re.search(r"office|everyday|daytime",F[i]["occasion"],re.I): o.append("Office & everyday")
    if pnum(i)<100 and "Under $100" not in o: o.append("Under $100")
    return o
def concentration(i):
    n=P[i]["name"].lower()
    for k,v in [("eau de parfum intense","Eau de Parfum Intense"),("le parfum","Parfum"),("eau de parfum","Eau de Parfum"),("edp","Eau de Parfum"),("eau de toilette","Eau de Toilette"),("parfum","Parfum"),("cologne","Cologne")]:
        if k in n: return v
    return None
def size(i):
    m=re.search(r"(\d+(?:\.\d+)?)\s*(?:fl\.?\s*)?oz",P[i]["name"],re.I) or re.search(r"(\d+)\s*ml",P[i]["name"],re.I)
    if not m: return None
    return m.group(0).replace("fl oz","fl oz")
def badges(i):
    b=[]
    if P[i].get("compare_at_price"): b.append(("sale","Sale"))
    if i in TOP[:6]: b.append(("ed","Editor's Pick"))
    if F[i]["family"].endswith("(niche)"): b.append(("niche","Niche Luxury"))
    elif pnum(i)<100: b.append(("value","Under $100"))
    return b

LOGO_MARK = '''<svg class="mark" viewBox="0 0 40 48" aria-hidden="true"><defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#f3d58f"/><stop offset=".55" stop-color="#c9973f"/><stop offset="1" stop-color="#8a6424"/></linearGradient></defs><rect x="15" y="2" width="10" height="7" rx="1.5" fill="url(#g)"/><rect x="17.5" y="9" width="5" height="4" fill="url(#g)"/><path d="M8 18a6 6 0 0 1 6-6h12a6 6 0 0 1 6 6v22a6 6 0 0 1-6 6H14a6 6 0 0 1-6-6z" fill="none" stroke="url(#g)" stroke-width="2.4"/><text x="20" y="36" text-anchor="middle" font-family="Georgia,serif" font-size="14" font-weight="700" fill="url(#g)">SR</text></svg>'''
def logo(): return f'<a class="logo" href="/" aria-label="{SITE_NAME} home">{LOGO_MARK}<span class="wm">Scent<em>Ranked</em></span></a>'
SOC_ICONS={"Instagram":'<path d="M7 2h10a5 5 0 0 1 5 5v10a5 5 0 0 1-5 5H7a5 5 0 0 1-5-5V7a5 5 0 0 1 5-5zm5 5a5 5 0 1 0 0 10 5 5 0 0 0 0-10zm6-1.5a1.2 1.2 0 1 0 0 2.4 1.2 1.2 0 0 0 0-2.4z"/>',
 "TikTok":'<path d="M16 2c.4 2.6 2 4.3 4.6 4.6v3.3c-1.7 0-3.2-.5-4.6-1.4v6.7A6.2 6.2 0 1 1 9.8 9v3.4a2.9 2.9 0 1 0 2.9 2.9V2z"/>',
 "Pinterest":'<path d="M12 2a10 10 0 0 0-3.6 19.3c-.1-.8-.2-2 0-2.9l1.2-5s-.3-.6-.3-1.5c0-1.4.8-2.5 1.8-2.5.9 0 1.3.6 1.3 1.4 0 .9-.6 2.2-.9 3.4-.2 1 .5 1.9 1.6 1.9 1.9 0 3.3-2 3.3-4.9 0-2.5-1.8-4.3-4.4-4.3-3 0-4.8 2.3-4.8 4.6 0 .9.3 1.9.8 2.4l.1.4-.3 1.2c0 .2-.2.3-.4.2-1.4-.6-2.2-2.6-2.2-4.2 0-3.4 2.5-6.6 7.2-6.6 3.8 0 6.7 2.7 6.7 6.3 0 3.7-2.4 6.8-5.6 6.8-1.1 0-2.2-.6-2.5-1.3l-.7 2.6c-.2 1-.9 2.2-1.4 2.9A10 10 0 1 0 12 2z"/>',
 "X":'<path d="M17.8 3h3.1l-6.8 7.7L22 21h-6.2l-4.9-6.4L5.3 21H2.2l7.3-8.3L2 3h6.4l4.4 5.8zm-1.1 16.2h1.7L7.4 4.7H5.6z"/>'}

def buy(i, label=None, cls="btn"):
    return f'<a class="{cls}" href="{esc(buy_url(P[i]["url"]))}" rel="sponsored nofollow noopener" target="_blank">Purchase Now</a>'

def card(i, rank=None, eager=False):
    f=F[i]; p=P[i]
    bd="".join(f'<span class="badge {c}">{t}</span>' for c,t in badges(i))
    cmp=f' <s>{p["compare_at_price"]}</s>' if p.get("compare_at_price") else ""
    data=f'data-brand="{esc(f["brand"])}" data-price="{pnum(i):.2f}" data-occ="{esc("|".join(occasions(i)))}" data-name="{esc((f["short"]+" "+f["brand"]+" "+f["family"]).lower())}"'
    return f"""<article class="pcard" {data}>{f'<span class="rank">#{rank}</span>' if rank else ''}<div class="badges">{bd}</div>
<a href="/reviews/{f['slug']}/" class="pimg"><img src="{p['image']}" alt="{esc(f['short'])} by {esc(f['brand'])}" width="400" height="400" {'fetchpriority="high"' if eager else 'loading="lazy"'} decoding="async"></a>
<div class="pbody"><a class="pbrand" href="/brands/{slugify(f['brand'])}/">{esc(f['brand'])}</a><h3><a href="/reviews/{f['slug']}/">{esc(f['short'])}</a></h3>
<p class="pfam">{esc(f['family'])}</p><p class="pprice"><span class="price">{price(i)}</span>{cmp}</p>{buy(i)}</div></article>"""

def crumbs(items):
    return {"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":k+1,"name":n,"item":SITE_URL+u} for k,(n,u) in enumerate(items)]}
def crumb_html(items): return '<nav class="crumbs" aria-label="Breadcrumb">'+" <span>/</span> ".join(f'<a href="{u}">{esc(n)}</a>' if u else f'<span aria-current="page">{esc(n)}</span>' for n,u in items)+'</nav>'

def header():
    occ="".join(f'<li><a href="/{r["slug"]}/">{esc(r["title"].replace(" for Men","").replace("Best ",""))}</a></li>' for r in ROUNDUPS)
    br="".join(f'<li><a href="/brands/{slugify(b)}/">{esc(b)}</a></li>' for b in BRANDS)
    bc="".join(f'<li><a href="/blog/category/{slugify(c)}/">{esc(c)}</a></li>' for c in BLOG_CATS)
    return f"""<a class="skip" href="#main">Skip to content</a><div class="announce">{esc(ANNOUNCE)} · <a href="/affiliate-disclosure/">How we earn</a></div>
<header class="hdr"><div class="wrap hrow">
<details class="mnav"><summary aria-label="Open menu"><span></span><span></span><span></span></summary><div class="mpanel">
<form action="/shop/" role="search"><input name="q" type="search" placeholder="Search colognes" aria-label="Search colognes"></form>
<a href="/shop/">Shop All</a><p>Best Lists</p><ul>{occ}</ul><p>Brands</p><ul class="cols">{br}</ul><p>Blog</p><ul>{bc}<li><a href="/blog/">All articles</a></li></ul><a href="/reviews/">All Reviews</a></div></details>
{logo()}
<nav class="dnav" aria-label="Main"><ul>
<li class="dd"><a href="/shop/">Shop by Occasion</a><ul class="drop">{occ}<li><a href="/shop/">Shop all colognes</a></li></ul></li>
<li class="dd"><a href="/brands/">Brands</a><ul class="drop cols">{br}</ul></li>
<li class="dd"><a href="/best-compliment-getting-colognes/">Best Lists</a><ul class="drop">{occ}</ul></li>
<li class="dd"><a href="/blog/">Blog</a><ul class="drop">{bc}<li><a href="/blog/">All articles</a></li></ul></li></ul></nav>
<form class="hsearch" action="/shop/" role="search"><input name="q" type="search" placeholder="Search colognes…" aria-label="Search colognes"><button aria-label="Search"><svg viewBox="0 0 24 24" width="18" height="18"><circle cx="11" cy="11" r="7" fill="none" stroke="currentColor" stroke-width="2"/><path d="m20 20-4-4" stroke="currentColor" stroke-width="2"/></svg></button></form>
<a class="hblog btn" href="/blog/">Read the Blog</a><a class="hshop" href="/shop/">Shop</a></div></header>"""

def footer():
    soc="".join(f'<a href="{u}" aria-label="{n}"><svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">{SOC_ICONS[n]}</svg></a>' for n,u in SOCIAL.items())
    lists="".join(f'<li><a href="/{r["slug"]}/">{esc(r["title"].replace(" for Men",""))}</a></li>' for r in ROUNDUPS)
    br="".join(f'<li><a href="/brands/{slugify(b)}/">{esc(b)}</a></li>' for b in BRANDS[:8])
    bl="".join(f'<li><a href="/blog/category/{slugify(c)}/">{esc(c)}</a></li>' for c in BLOG_CATS)+"".join(f'<li class="fpost"><a href="/blog/{x["slug"]}/">{esc(x["title"])}</a></li>' for x in POSTS[:3])+'<li><a href="/blog/">All articles →</a></li>'
    return f"""<footer class="ftr"><div class="wrap">
<div class="news"><div><h2>The ScentRanked Edit</h2><p>New guides and picks, about twice a month. No spam.</p></div>
<form name="newsletter" method="POST" data-netlify="true" netlify-honeypot="company" action="/thanks/"><input type="hidden" name="form-name" value="newsletter"><p class="hp"><label>Company <input name="company"></label></p>
<label class="sr" for="nl-email">Email address</label><input id="nl-email" type="email" name="email" required placeholder="you@example.com" autocomplete="email"><button class="btn">Subscribe</button></form></div>
<div class="fgrid"><div>{logo()}<p>Plain-English guides to the best designer colognes for men, for US shoppers.</p><div class="soc">{soc}</div></div>
<div><h3>Best Lists</h3><ul>{lists}<li><a href="/shop/">Shop all</a></li></ul></div>
<div><h3>Blog</h3><ul>{bl}</ul></div><div><h3>Top Brands</h3><ul>{br}<li><a href="/brands/">All brands</a></li></ul></div>
<div><h3>Company</h3><ul><li><a href="/about/">About</a></li><li><a href="/blog/">Blog</a></li><li><a href="/reviews/">Reviews</a></li><li><a href="/affiliate-disclosure/">Affiliate Disclosure</a></li><li><a href="/privacy/">Privacy Policy</a></li><li><a href="/rss.xml">RSS</a></li></ul></div></div>
<p class="fdisc"><strong>Affiliate disclosure:</strong> {SITE_NAME} is reader-supported. "Purchase Now" links go to Yoovic, and we may earn a commission at no extra cost to you. Prices were checked on {TODAY} and may change. Brand names are trademarks of their owners; {SITE_NAME} is not affiliated with or endorsed by them.</p>
<p class="legal">© {YEAR} {SITE_NAME} · <a href="/privacy/">Privacy</a> · <a href="/affiliate-disclosure/">Disclosure</a> · <a href="/sitemap.xml">Sitemap</a></p></div></footer>"""

FONTS='<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link rel="preconnect" href="https://yoovic.com"><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600;700&family=Inter:wght@400;500;600;700&display=swap">'
def _head_extra():
    h = ""
    v = SEOS.get("google_site_verification", "").strip()
    if v:
        m = re.search(r'content="([^"]+)"', v); v = m.group(1) if m else v
        h += f'<meta name="google-site-verification" content="{esc(v)}">'
    v = SEOS.get("bing_site_verification", "").strip()
    if v: h += f'<meta name="msvalidate.01" content="{esc(v)}">'
    gtm = SEOS.get("gtm_id", "").strip(); ga = SEOS.get("ga4_id", "").strip()
    if gtm and re.fullmatch(r"GTM-[A-Z0-9]+", gtm):
        h += "<script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],j=d.createElement(s);j.async=true;j.src='https://www.googletagmanager.com/gtm.js?id='+i;f.parentNode.insertBefore(j,f)})(window,document,'script','dataLayer','" + gtm + "');</script>"
    elif ga and re.fullmatch(r"G-[A-Z0-9]+", ga):
        h += f'<script async src="https://www.googletagmanager.com/gtag/js?id={ga}"></script><script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag("js",new Date());gtag("config","{ga}");</script>'
    return h
HEAD_EXTRA = _head_extra()
URL_HASH = {}

def merchant_feed():
    items = []
    for i in F:
        p = P[i]
        if not p.get("in_merchant_feed", True): continue
        f = F[i]
        sale = p.get("compare_at_price")
        pr = f"{pnum(i):.2f} USD"
        price_xml = f"<g:price>{float(re.sub(r'[^0-9.]','',sale)):.2f} USD</g:price><g:sale_price>{pr}</g:sale_price>" if sale else f"<g:price>{pr}</g:price>"
        extra = "".join(f"<g:additional_image_link>{esc(g)}</g:additional_image_link>" for g in (p.get("gallery") or [])[1:10])
        items.append(f"""<item><g:id>yoovic-{esc(p['url'].rstrip('/').split('/')[-1])}</g:id><title>{esc(p['name'][:150])}</title><description>{esc((p.get('description') or f['take'])[:4900])}</description>
<link>{esc(buy_url(p['url']))}</link><g:image_link>{esc(p['image'])}</g:image_link>{extra}{price_xml}<g:availability>in_stock</g:availability><g:condition>new</g:condition>
<g:brand>{esc(f['brand'])}</g:brand><g:identifier_exists>no</g:identifier_exists><g:google_product_category>{esc(str(SEOS.get('google_product_category') or '479'))}</g:google_product_category><g:product_type>Fragrance &gt; Men's Cologne</g:product_type>
<g:gender>{'male' if p.get('gender')=='men' else 'unisex'}</g:gender><g:age_group>adult</g:age_group><g:shipping><g:country>US</g:country><g:price>0.00 USD</g:price></g:shipping></item>""")
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0" xmlns:g="http://base.google.com/ns/1.0"><channel><title>{SITE_NAME} product feed</title><link>{SITE_URL}/</link><description>{SITE_NAME} men\'s cologne picks</description>\n' + "\n".join(items) + "\n</channel></rss>\n"

def page(path, title, desc, body, schema=None, ogimg=None, js=False, full=False):
    url = SITE_URL + "/" + path.replace("index.html","")
    sch = "".join(f'<script type="application/ld+json">{json.dumps(s)}</script>' for s in (schema or []))
    doc = f"""<!doctype html><html lang="en-US"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title><meta name="description" content="{esc(desc)}"><link rel="canonical" href="{url}"><meta name="theme-color" content="#0d0c0a">
<link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="apple-touch-icon" href="/favicon.svg">
<meta property="og:type" content="website"><meta property="og:site_name" content="{SITE_NAME}"><meta property="og:locale" content="en_US"><meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{url}">{f'<meta property="og:image" content="{ogimg}">' if ogimg else ''}
<meta name="twitter:card" content="summary_large_image">{HEAD_EXTRA}{FONTS}<link rel="stylesheet" href="/style.css"><link rel="alternate" type="application/rss+xml" title="{SITE_NAME} Blog" href="/rss.xml">{sch}</head><body>
{header()}<main id="main" class="{'' if full else 'wrap'}">{body}</main>{footer()}{'<script src="/shop.js" defer></script>' if js else ''}<script src="/site.js" defer></script></body></html>"""
    f = os.path.join(OUT, path); os.makedirs(os.path.dirname(f), exist_ok=True); open(f,"w").write(doc)
    import hashlib; URL_HASH[url] = hashlib.sha1(re.sub(r"\d{4}-\d{2}-\d{2}", "", doc).encode()).hexdigest()[:16]
    return url

SHOP_JS = r"""(function(){var g=document.getElementById('pgrid');if(!g)return;var cards=[].slice.call(g.children),f=document.getElementById('filters'),q=new URLSearchParams(location.search);
var s=f.querySelector('[name=q]');if(q.get('q'))s.value=q.get('q');if(q.get('occ')){var c=f.querySelector('[name=occ][value="'+q.get('occ')+'"]');if(c)c.checked=true}if(q.get('brand'))f.brand.value=q.get('brand');
function run(){var t=s.value.trim().toLowerCase(),b=f.brand.value,mx=parseFloat(f.max.value),o=[].slice.call(f.querySelectorAll('[name=occ]:checked')).map(function(x){return x.value}),n=0;
cards.forEach(function(c){var ok=(!t||c.dataset.name.indexOf(t)>-1)&&(!b||c.dataset.brand===b)&&(+c.dataset.price<=mx)&&o.every(function(x){return c.dataset.occ.split('|').indexOf(x)>-1});c.hidden=!ok;if(ok)n++});
var so=f.sort.value;cards.slice().sort(function(a,b){return so==='lo'?a.dataset.price-b.dataset.price:so==='hi'?b.dataset.price-a.dataset.price:a.dataset.i-b.dataset.i}).forEach(function(c){g.appendChild(c)});
document.getElementById('maxv').textContent='$'+mx;document.getElementById('count').textContent=n+(n===1?' cologne':' colognes');document.getElementById('empty').hidden=n>0}
f.addEventListener('input',run);f.addEventListener('submit',function(e){e.preventDefault();run()});f.addEventListener('reset',function(){setTimeout(run,0)});cards.forEach(function(c,k){c.dataset.i=k});run()})();"""
SITE_JS = r"""document.querySelectorAll('.thumbs button').forEach(function(b){b.addEventListener('click',function(){var m=document.getElementById('gmain');m.src=b.dataset.src;document.querySelectorAll('.thumbs button').forEach(function(x){x.setAttribute('aria-pressed',x===b)})})});"""

def build():
    global POSTS
    POSTS = load_posts()
    if os.path.exists(OUT): shutil.rmtree(OUT)
    os.makedirs(OUT); open(os.path.join(OUT,"style.css"),"w").write(CSS)
    shutil.copytree(os.path.join(BASE, "admin"), os.path.join(OUT, "admin"))
    json.dump({"products":[{"slug":F[i]["slug"],"name":F[i]["short"],"key":i} for i in F],"categories":BLOG_CATS}, open(os.path.join(OUT,"admin","meta.json"),"w"))
    if SEOS.get("merchant_feed_enabled", True): open(os.path.join(OUT, "merchant-feed.xml"), "w").write(merchant_feed())
    open(os.path.join(OUT,"shop.js"),"w").write(SHOP_JS); open(os.path.join(OUT,"site.js"),"w").write(SITE_JS)
    open(os.path.join(OUT,"favicon.svg"),"w").write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><rect width="48" height="48" rx="10" fill="#0d0c0a"/>'+LOGO_MARK.replace('<svg class="mark" viewBox="0 0 40 48" aria-hidden="true">','<g transform="translate(5 1) scale(.95)">').replace('</svg>','</g>')+'</svg>')
    open(os.path.join(OUT,"logo.svg"),"w").write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 48">'+LOGO_MARK.replace('<svg class="mark" viewBox="0 0 40 48" aria-hidden="true">','<g>').replace('</svg>','</g>')+'<text x="50" y="33" font-family="Georgia,serif" font-size="26" fill="#f4efe6">Scent<tspan fill="#d4a85a" font-style="italic">Ranked</tspan></text></svg>')
    urls=[]
    # ---- product detail pages
    for i,f in F.items():
        p=P[i]; d=p["description"] or ""; gal=p.get("gallery") or [p["image"]]
        rel=list(dict.fromkeys([j for r in ROUNDUPS if i in r["ids"] for j in r["ids"] if j!=i]+[j for j in F if F[j]["brand"]==f["brand"] and j!=i]))[:4]
        inr="".join(f'<a class="chip" href="/{r["slug"]}/">{esc(r["title"])}</a>' for r in ROUNDUPS if i in r["ids"])
        det=[("Brand",f'<a href="/brands/{slugify(f["brand"])}/">{esc(f["brand"])}</a>'),("Concentration",concentration(i)),("Size",size(i)),("Scent family",esc(f["family"])),("Best season",esc(f["season"])),("Best for",esc(f["occasion"])),("For","Men" if p["gender"]=="men" else "Unisex")]
        dt="".join(f"<tr><th>{k}</th><td>{v}</td></tr>" for k,v in det if v)
        thumbs="".join(f'<button type="button" data-src="{g}" aria-label="View image {k+1}" aria-pressed="{str(k==0).lower()}"><img src="{g}" alt="" width="72" height="72" loading="lazy"></button>' for k,g in enumerate(gal)) if len(gal)>1 else ""
        notes=f'<div class="notes"><h3>Key notes</h3><p>{"".join(f"<span>{esc(n.strip())}</span>" for n in f["notes"].split(","))}</p><p class="small">Widely published notes for this fragrance.</p></div>' if f["notes"] else ""
        bd="".join(f'<span class="badge {c}">{t}</span>' for c,t in badges(i))
        body=f"""{crumb_html([("Home","/"),("Shop","/shop/"),(f['brand'],f"/brands/{slugify(f['brand'])}/"),(f['short'],None)])}
<section class="pdp"><div class="gallery"><div class="gmain"><img id="gmain" src="{gal[0]}" alt="{esc(f['short'])} by {esc(f['brand'])}" width="600" height="600" fetchpriority="high"></div><div class="thumbs">{thumbs}</div></div>
<div class="pinfo"><div class="badges static">{bd}</div><a class="pbrand" href="/brands/{slugify(f['brand'])}/">{esc(f['brand'])}</a><h1>{esc(f['short'])}</h1><p class="pfam">{esc(f['family'])}</p>
<p class="pprice big"><span class="price">{price(i)}</span>{f' <s>{p["compare_at_price"]}</s>' if p.get("compare_at_price") else ''}</p>
<p class="lead">{esc(f['best'])}.</p>{buy(i,cls="btn lg")}
<ul class="perks"><li>Ships from Yoovic: free shipping, expedited US options</li><li>Price checked {TODAY}. Confirm on Yoovic</li></ul>
<table class="dtable">{dt}</table><div class="chips">{inr}</div></div></section>
<section class="pdesc"><div class="prose"><h2>Our take</h2><p>{esc(f['take'])}</p>
<div class="pc"><div><h3>What we like</h3><ul>{''.join(f'<li>{esc(x)}</li>' for x in f['pros'])}</ul></div><div><h3>Keep in mind</h3><ul>{''.join(f'<li>{esc(x)}</li>' for x in f['cons'])}</ul></div></div>
{notes}<h2>From the retailer's description</h2><p class="small">{esc(d[:600])}{'…' if len(d)>600 else ''}</p><p class="small">Listing: {esc(p['name'])}</p>
<h2>How to wear it</h2><p>Best for <strong>{esc(f['occasion'].lower())}</strong>, ideally in <strong>{esc(f['season'].lower())}</strong>. Start with 2–3 sprays on the chest and neck and adjust. Performance varies with skin and climate, so sample first if you can. See our guide on <a href="/blog/edt-vs-edp-vs-parfum/">EDT vs EDP vs Parfum</a>.</p>
<div class="cta">{buy(i,cls="btn lg")}</div></div></section>
{f'<section class="sec"><h2 class="h2">You may also like</h2><div class="pgrid">{"".join(card(j) for j in rel)}</div></section>' if rel else ''}
<div class="mbuy"><span class="price">{price(i)}</span>{buy(i)}</div>"""
        offer={"@type":"Offer","price":f"{pnum(i):.2f}","priceCurrency":"USD","url":p["url"],"seller":{"@type":"Organization","name":"Yoovic"}}
        sch=[{"@context":"https://schema.org","@type":"Product","name":p["name"],"brand":{"@type":"Brand","name":f["brand"]},"image":gal,"description":f["take"],"category":"Men's Cologne","offers":offer},
             crumbs([("Home","/"),("Shop","/shop/"),(f["brand"],f"/brands/{slugify(f['brand'])}/"),(f["short"],f"/reviews/{f['slug']}/")])]
        urls.append(page(f"reviews/{f['slug']}/index.html", f"{f['short']}: Notes, Price & Review ({YEAR}) | {SITE_NAME}",
             f"{f['short']} by {f['brand']}: {f['best'].lower()}. Scent notes, best season and occasion, and current price ({price(i)}) with free shipping at Yoovic.", body, sch, p["image"]))
    # ---- roundups
    for r in ROUNDUPS:
        items="".join(f"""<section class="pick" id="{F[i]['slug']}"><div class="pickimg"><span class="rank">#{k+1}</span><img src="{P[i]['image']}" alt="{esc(F[i]['short'])}" width="320" height="320" loading="lazy"></div>
<div><a class="pbrand" href="/brands/{slugify(F[i]['brand'])}/">{esc(F[i]['brand'])}</a><h2>{esc(F[i]['short'])}</h2><p class="pfam">{esc(F[i]['family'])} · {esc(F[i]['season'])}</p><p class="lead">{esc(F[i]['best'])}</p><p>{esc(F[i]['take'])}</p>
<div class="prow"><span class="price">{price(i)}</span>{buy(i)}<a class="link" href="/reviews/{F[i]['slug']}/">Full details →</a></div></div></section>""" for k,i in enumerate(r["ids"]))
        quick="".join(f'<li><a href="#{F[i]["slug"]}">{esc(F[i]["short"])}</a> <span class="qp">{price(i)}</span> {buy(i,cls="btn sm")}</li>' for i in r["ids"])
        other="".join(f'<a class="chip" href="/{o["slug"]}/">{esc(o["title"])}</a>' for o in ROUNDUPS if o is not r)
        body=f"""<section class="lhero"><div class="wrap">{crumb_html([("Home","/"),("Best Lists",None),(r['title'],None)])}<p class="kicker">Updated {datetime.date.today().strftime('%B %Y')}</p><h1>{esc(r['title'])}</h1><p class="lede">{esc(r['h'])} {esc(r['intro'])}</p></div></section>
<div class="wrap"><p class="small">Rankings are editorial opinion based on each fragrance's publicly known profile and reputation, not paid placement.</p>
<div class="quick"><h2>Quick list</h2><ol>{quick}</ol></div>{items}<div class="chips more"><strong>More lists:</strong> {other}<a class="chip" href="/shop/">Shop all</a></div></div>"""
        sch=[{"@context":"https://schema.org","@type":"ItemList","name":r["title"],"itemListElement":[{"@type":"ListItem","position":k+1,"url":f"{SITE_URL}/reviews/{F[i]['slug']}/","name":F[i]["short"]} for k,i in enumerate(r["ids"])]},
             crumbs([("Home","/"),(r["title"],f"/{r['slug']}/")])]
        urls.append(page(f"{r['slug']}/index.html", f"{r['title']} ({YEAR}) | {SITE_NAME}", f"{r['h']} Our ranked {r['title'].lower()} for US shoppers, with notes, best uses and prices.", body, sch, P[r['ids'][0]]['image'], full=True))
    # ---- shop
    allc="".join(card(i) for i in TOP+[i for i in sorted(F,key=pnum) if i not in TOP])
    bopt="".join(f'<option>{esc(b)}</option>' for b in BRANDS)
    occs=list(OCC.values())+["Office & everyday"]
    chips="".join(f'<label class="fchip"><input type="checkbox" name="occ" value="{esc(o)}"><span>{esc(o)}</span></label>' for o in occs)
    mx=int(max(pnum(i) for i in F))+1
    body=f"""{crumb_html([("Home","/"),("Shop",None)])}<h1>Shop Men's Colognes</h1><p class="lede">{len(F)} designer and niche colognes we recommend. Filter by brand, price and occasion.</p>
<div class="shop"><form id="filters" class="filters" aria-label="Filter colognes"><input name="q" type="search" placeholder="Search…" aria-label="Search">
<label>Brand<select name="brand"><option value="">All brands</option>{bopt}</select></label>
<label>Max price <output id="maxv">${mx}</output><input type="range" name="max" min="20" max="{mx}" step="5" value="{mx}"></label>
<fieldset><legend>Occasion</legend>{chips}</fieldset><label>Sort<select name="sort"><option value="">Featured</option><option value="lo">Price: low to high</option><option value="hi">Price: high to low</option></select></label><button type="reset" class="btn ghost">Reset filters</button></form>
<div><p class="count" id="count" aria-live="polite"></p><div class="pgrid" id="pgrid">{allc}</div><p id="empty" hidden>No colognes match those filters.</p></div></div>"""
    urls.append(page("shop/index.html",f"Shop the Best Men's Colognes ({YEAR}) | {SITE_NAME}","Shop our curated designer and niche men's colognes, from Chanel and Versace to Creed. Filter by brand, price and occasion.",body,[crumbs([("Home","/"),("Shop","/shop/")])],js=True))
    urls.append(page("reviews/index.html",f"All Men's Cologne Reviews | {SITE_NAME}","Every men's cologne we cover, with notes, best uses and prices.",crumb_html([("Home","/"),("Reviews",None)])+'<h1>All Cologne Reviews</h1><div class="pgrid">'+"".join(card(i) for i in sorted(F,key=pnum))+'</div>'))
    # ---- brands
    bl=""
    for b in BRANDS:
        ids=[i for i in F if F[i]["brand"]==b]; s=slugify(b); bl+=f'<a class="bcard" href="/brands/{s}/"><img src="{P[ids[0]]["image"]}" alt="" width="160" height="160" loading="lazy"><span>{esc(b)}</span><small>{len(ids)} pick{"s" if len(ids)>1 else ""}</small></a>'
        lo,hi=min(pnum(i) for i in ids),max(pnum(i) for i in ids)
        body=f"""{crumb_html([("Home","/"),("Brands","/brands/"),(b,None)])}<h1>{esc(b)} Colognes for Men</h1><p class="lede">Our recommended {esc(b)} fragrances, from ${lo:.0f}{f" to ${hi:.0f}" if hi>lo else ""}, with notes and current prices.</p><div class="pgrid">{"".join(card(i) for i in ids)}</div>
<p class="more"><a href="/brands/">All brands</a> · <a href="/shop/">Shop all colognes</a></p>"""
        urls.append(page(f"brands/{s}/index.html",f"Best {b} Colognes for Men ({YEAR}) | {SITE_NAME}",f"The best {b} colognes for men, with scent notes, best uses and current prices at Yoovic.",body,[crumbs([("Home","/"),("Brands","/brands/"),(b,f"/brands/{s}/")])],P[ids[0]]["image"]))
    urls.append(page("brands/index.html",f"Cologne Brands | {SITE_NAME}","Browse men's colognes by brand: Chanel, Versace, Jean Paul Gaultier, Armani, Creed, Paco Rabanne and more.",crumb_html([("Home","/"),("Brands",None)])+f'<h1>Shop by Brand</h1><div class="bgrid">{bl}</div>'))
    # ---- home
    promos=[("best-compliment-getting-colognes","Top Colognes of "+str(YEAR),"The compliment-getters",47),("best-colognes-under-100","Under $100 Picks","Designer scents, sensible prices",48),("best-date-night-colognes","Date Night","Warm, close, unforgettable",32),("best-summer-colognes","Summer Fresh","Scents that survive the heat",2)]
    pr="".join(f'<a class="promo" href="/{s}/"><img src="{P[i]["image"]}" alt="" width="300" height="300" loading="lazy"><div><small>{esc(sub)}</small><strong>{esc(t)}</strong><span>Shop the list →</span></div></a>' for s,t,sub,i in promos)
    brs="".join(f'<a href="/brands/{slugify(b)}/">{esc(b)}</a>' for b in BRANDS)
    def pimg(x): return f'<img src="{esc(x["img"])}" alt="" width="400" height="250" loading="lazy">' if x.get("img") else ""
    def pcards(lst): return "".join(f'<a class="post-card v" href="/blog/{x["slug"]}/">{pimg(x)}<div><p class="small">{esc(x.get("category",""))} · {x["dt"].strftime("%b %-d, %Y")}</p><h3>{esc(x["title"])}</h3><p>{esc(x.get("description",""))}</p></div></a>' for x in lst)
    secs=[("Latest Articles","/blog/",POSTS[:4])]+[(c,f"/blog/category/{slugify(c)}/",[x for x in POSTS if x.get("category")==c][:4]) for c in BLOG_CATS]
    blogsecs="".join(f'<section class="sec blogsec{" alt" if k%2 else ""}"><div class="shead"><h2 class="h2">{esc(t)}</h2><a href="{u}">View all →</a></div><div class="posts four">{pcards(l)}</div></section>' for k,(t,u,l) in enumerate(secs) if l)
    body=f"""<section class="hero"><div class="wrap hgrid"><div class="htxt"><p class="kicker">The {YEAR} Edit · Best Designer Colognes for Men</p><h1>Find the cologne that<br><em>gets you noticed.</em></h1>
<p class="lede">Curated picks from Chanel, Versace, Jean Paul Gaultier, Armani, Creed and more, ranked by occasion in plain English. Every pick ships from Yoovic.</p>
<div class="hbtn"><a class="btn lg" href="/shop/">Shop the Edit</a><a class="btn ghost lg" href="/best-compliment-getting-colognes/">Top Colognes of {YEAR}</a></div></div>
<div class="hart"><img src="{P[14]['image']}" alt="Bleu de Chanel" width="420" height="420" fetchpriority="high" class="h1i"><img src="{P[32]['image']}" alt="Le Male Le Parfum" width="300" height="300" class="h2i"><img src="{P[47]['image']}" alt="Versace Eros" width="260" height="260" class="h3i" loading="lazy"></div></div></section>
<div class="trust wrap"><span>Free shipping on every order at Yoovic</span><span>Expedited US shipping available</span><span>Independent, no-hype picks</span><span>No paid rankings</span></div>
<section class="wrap sec"><h2 class="h2">Shop by occasion</h2><div class="promos">{pr}</div></section>
<section class="wrap sec"><div class="shead"><h2 class="h2">Editor's top picks</h2><a href="/shop/">View all →</a></div><div class="pgrid">{''.join(card(i,k+1,eager=k<2) for k,i in enumerate(TOP))}</div></section>
<section class="banner"><div class="wrap"><div><p class="kicker">Under $100</p><h2>Designer quality, without the designer markup.</h2><p>Versace Eros Flame, Le Male, 1 Million and more, all under $100.</p><a class="btn lg" href="/best-colognes-under-100/">Shop Under $100</a></div><img src="{P[48]['image']}" alt="Versace Eros Flame" width="320" height="320" loading="lazy"></div></section>
<section class="wrap sec"><h2 class="h2">Shop by brand</h2><div class="brandrow">{brs}</div></section>
{blogsecs}
<section class="wrap sec prose"><h2 class="h2">How we pick</h2><p>We focus on fragrances with long, well-documented reputations in the US and sort them by what you'll actually use them for: office, summer, date night, or getting noticed. We don't publish star ratings, scores or invented reviews. You get our honest opinion, the published notes, and who each scent suits. "Purchase Now" links go to the product page at Yoovic, and we may earn a commission (<a href="/affiliate-disclosure/">details</a>).</p></section>"""
    sch=[{"@context":"https://schema.org","@type":"WebSite","name":SITE_NAME,"url":SITE_URL+"/","potentialAction":{"@type":"SearchAction","target":SITE_URL+"/shop/?q={search_term_string}","query-input":"required name=search_term_string"}},{"@context":"https://schema.org","@type":"Organization","name":SITE_NAME,"url":SITE_URL+"/","logo":SITE_URL+"/logo.svg"}]
    urls.insert(0,page("index.html",f"Best Designer Colognes for Men ({YEAR}): Top Picks | {SITE_NAME}","The best designer colognes for men in "+str(YEAR)+": compliment-getters, date night, summer and under-$100 picks from Chanel, Versace, JPG, Armani and Creed, with current prices.",body,sch,P[14]['image'],full=True))
    # ---- static pages
    S={"about":("About ScentRanked",f"<h1>About {SITE_NAME}</h1><p>{SITE_NAME} is a small editorial site that helps US shoppers pick a men's cologne without the hype. Our guides are organized around real situations (office, summer, date night, budget), and we stick to fragrances with long, well-documented reputations.</p><h2>How we write</h2><ul><li>Scent notes come from brand or retailer information, or widely published fragrance pyramids.</li><li>Our take is editorial opinion. We don't publish star ratings, scores or invented customer reviews.</li><li>Prices are checked on the retailer's site and dated, and they can change at any time.</li></ul><h2>Contact</h2><p>{CONTACT_EMAIL}</p>"),
       "affiliate-disclosure":("Affiliate Disclosure",f"<h1>Affiliate Disclosure</h1><p>{SITE_NAME} is reader-supported. \"Purchase Now\" links on this site point to <a href='https://yoovic.com' rel='sponsored nofollow'>Yoovic</a>, and we may earn a commission if you buy through them, at no extra cost to you.</p><p>Commissions never change our editorial opinion or the order of our rankings. We are not affiliated with, endorsed by, or sponsored by any of the fragrance brands mentioned. All trademarks belong to their owners.</p><p>Yoovic handles purchases, shipping, returns and customer service. Please review its terms before buying.</p><p>This disclosure follows the U.S. Federal Trade Commission's guidance on endorsements.</p>"),
       "privacy":("Privacy Policy",f"<h1>Privacy Policy</h1><p class='small'>Last updated {TODAY}</p><p>{SITE_NAME} does not require accounts.</p><h2>Newsletter</h2><p>If you subscribe, we store your email address (via our host's form service) only to send the newsletter. Unsubscribe or request deletion at any time by contacting {CONTACT_EMAIL}.</p><h2>Technical data</h2><p>Our hosting provider may log standard technical data (IP address, browser, pages visited) for security and performance.</p><h2>Cookies & third parties</h2><p>We don't set advertising cookies. Fonts load from Google Fonts and product images from yoovic.com. When you click a Purchase Now link you go to Yoovic, which has its own privacy policy and may use cookies to attribute the referral.</p><h2>Your rights</h2><p>US residents, including California residents under the CCPA/CPRA, may request access to or deletion of personal data we hold. Contact {CONTACT_EMAIL}.</p><h2>Children</h2><p>This site is not directed at children under 13.</p>"),
       "thanks":("Thanks for subscribing","<h1>You're on the list.</h1><p>Thanks for subscribing to The ScentRanked Edit.</p><p><a class='btn' href='/shop/'>Keep shopping</a></p>")}
    for s,(t,b) in S.items():
        u=page(f"{s}/index.html",f"{t} | {SITE_NAME}",f"{t} for {SITE_NAME}.",f'<section class="prose static">{b}</section>')
        if s!="thanks": urls.append(u)
    urls += build_blog()
    page("404.html",f"Page not found | {SITE_NAME}","Page not found",'<section class="prose static"><h1>Page not found</h1><p><a class="btn" href="/shop/">Shop colognes</a></p></section>')
    open(os.path.join(OUT,"sitemap.xml"),"w").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'+"".join(f"<url><loc>{u}</loc><lastmod>{TODAY}</lastmod></url>\n" for u in urls)+"</urlset>\n")
    ik = re.sub(r"[^a-zA-Z0-9-]", "", SEOS.get("indexnow_key", ""))
    if ik: open(os.path.join(OUT, f"{ik}.txt"), "w").write(ik)
    json.dump({"indexnow_key": ik, "urls": {u: URL_HASH[u] for u in urls if u in URL_HASH}}, open(os.path.join(OUT, "indexnow-urls.json"), "w"))
    open(os.path.join(OUT,"robots.txt"),"w").write(f"User-agent: *\nAllow: /\nDisallow: /thanks/\nDisallow: /admin/\n\nSitemap: {SITE_URL}/sitemap.xml\n")
    print(len(urls),"pages in sitemap")
# ===== BLOG =====
# content/blog/*.md with front matter. Skipped if status != published or date is in the future.
BLOG_DIR = os.path.join(BASE, "content", "blog")
SLUG2I = {f["slug"]: i for i, f in F.items()}

def parse_date(s):
    s = s.strip().replace(" ", "T", 1)
    d = datetime.datetime.fromisoformat(s)
    if d.tzinfo is None: d = d.replace(tzinfo=datetime.timezone.utc)
    return d

def front(text):
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.S)
    if m:
        try:
            import yaml
            meta = yaml.safe_load(m.group(1)) or {}
            meta = {k: (v.isoformat() if hasattr(v, "isoformat") else ("" if v is None else str(v) if not isinstance(v, str) else v)) for k, v in meta.items()}
            return meta, m.group(2)
        except Exception:
            pass
    return _front_simple(text)

def _front_simple(text):
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.S)
    if not m: raise ValueError("missing front matter")
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1); meta[k.strip()] = v.strip().strip('"').strip("'")
    return meta, m.group(2)

def inline(t):
    t = esc(t, quote=False)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<!\*)\*(?!\s)(.+?)\*", r"<em>\1</em>", t)
    t = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>', t)
    return t

def md(text):
    out, para, lst = [], [], None
    def flush():
        nonlocal para, lst
        if para: out.append("<p>" + inline(" ".join(para)) + "</p>"); para = []
        if lst: out.append(f"<{lst[0]}>" + "".join(f"<li>{inline(x)}</li>" for x in lst[1]) + f"</{lst[0]}>"); lst = None
    for line in text.splitlines():
        s = line.strip()
        m = re.fullmatch(r"\{\{\s*product:([a-z0-9-]+)\s*\}\}", s)
        if m:
            flush()
            if m.group(1) not in SLUG2I: raise ValueError(f"unknown product shortcode: {m.group(1)}")
            out.append('<div class="embed">' + card(SLUG2I[m.group(1)]) + "</div>"); continue
        if not s: flush(); continue
        h = re.match(r"^(#{2,4})\s+(.*)", s)
        if h: flush(); out.append(f"<h{len(h.group(1))}>{inline(h.group(2))}</h{len(h.group(1))}>"); continue
        li = re.match(r"^([-*]|\d+\.)\s+(.*)", s)
        if li:
            if para: flush()
            kind = "ol" if li.group(1)[0].isdigit() else "ul"
            if lst and lst[0] != kind: flush()
            if not lst: lst = (kind, [])
            lst[1].append(li.group(2)); continue
        if lst: flush()
        para.append(s)
    flush()
    return "\n".join(out)

def load_posts():
    now = datetime.datetime.now(datetime.timezone.utc); posts = []
    if not os.path.isdir(BLOG_DIR): return posts
    for fn in sorted(os.listdir(BLOG_DIR)):
        if not fn.endswith(".md"): continue
        meta, body = front(open(os.path.join(BLOG_DIR, fn), encoding="utf-8").read())
        slug = meta.get("slug") or fn[:-3]
        d = parse_date(meta["date"])
        if meta.get("status", "draft").lower() != "published": print(f"  skip (draft): {fn}"); continue
        if d > now: print(f"  skip (scheduled {d.isoformat()}): {fn}"); continue
        img = meta.get("image", "")
        if img.startswith("product:"): img = P[SLUG2I[img[8:]]]["image"]
        if meta.get("category") and meta["category"] not in BLOG_CATS: raise ValueError(f"{fn}: unknown category {meta['category']} (add it to BLOG_CATS)")
        posts.append(dict(meta, slug=slug, dt=d, body=body, img=img))
    return sorted(posts, key=lambda p: p["dt"], reverse=True)

def build_blog():
    posts = POSTS; urls = []
    def cats_nav(cur=None): return '<div class="chips">'+f'<a class="chip{" on" if cur is None else ""}" href="/blog/">All</a>'+"".join(f'<a class="chip{" on" if cur==c else ""}" href="/blog/category/{slugify(c)}/">{esc(c)}</a>' for c in BLOG_CATS)+'</div>'
    def plist(lst): return "".join(f"""<a class="post-card" href="/blog/{p['slug']}/">{f'<img src="{esc(p["img"])}" alt="" width="400" height="250" loading="lazy">' if p['img'] else ''}<div><p class="small">{esc(p.get('category',''))} · {p['dt'].strftime('%b %-d, %Y')}</p><h2>{esc(p['title'])}</h2><p>{esc(p.get('description',''))}</p></div></a>""" for p in lst) or "<p>No posts yet.</p>"
    for p in posts:
        img = p["img"]; cat = p.get("category")
        rel = [x for x in posts if x is not p and x.get("category")==cat][:3]
        body = f"""{crumb_html([("Home","/"),("Blog","/blog/")]+([(cat,f"/blog/category/{slugify(cat)}/")] if cat else [])+[(p['title'],None)])}
<article class="prose post">{f'<a class="kicker" href="/blog/category/{slugify(cat)}/">{esc(cat)}</a>' if cat else ''}<h1>{esc(p['title'])}</h1><p class="small">{p['dt'].strftime('%B %-d, %Y')} · {SITE_NAME} Editors</p>
{f'<img class="post-hero" src="{esc(img)}" alt="" width="760" height="380">' if img else ''}{md(p['body'])}</article>
{f'<section class="sec"><h2 class="h2">More {esc(cat)}</h2><div class="posts four">{plist(rel)}</div></section>' if rel else ''}"""
        sch = [{"@context":"https://schema.org","@type":"BlogPosting","headline":p["title"],"description":p.get("description",""),"datePublished":p["dt"].isoformat(),"articleSection":cat,
                "image":img or None,"author":{"@type":"Organization","name":SITE_NAME},"publisher":{"@type":"Organization","name":SITE_NAME,"logo":{"@type":"ImageObject","url":SITE_URL+"/logo.svg"}},"mainEntityOfPage":f"{SITE_URL}/blog/{p['slug']}/"},
               crumbs([("Home","/"),("Blog","/blog/"),(p["title"],f"/blog/{p['slug']}/")])]
        urls.append(page(f"blog/{p['slug']}/index.html", f"{p['title']} | {SITE_NAME}", p.get("description",""), body, sch, img or None))
    urls.append(page("blog/index.html", f"Men's Cologne Blog: Guides, Buying Tips & Seasonal Picks | {SITE_NAME}", "Practical, no-hype guides to choosing, buying, wearing and storing men's cologne.",
        f'{crumb_html([("Home","/"),("Blog",None)])}<h1>The ScentRanked Blog</h1><p class="lede">Practical, no-hype guides to buying and wearing cologne.</p>{cats_nav()}<div class="posts">{plist(posts)}</div>',[crumbs([("Home","/"),("Blog","/blog/")])]))
    for c in BLOG_CATS:
        lst=[x for x in posts if x.get("category")==c]; s=slugify(c)
        urls.append(page(f"blog/category/{s}/index.html", f"{c}: Men's Cologne Articles | {SITE_NAME}", f"{c} from the {SITE_NAME} blog: practical articles on men's cologne.",
            f'{crumb_html([("Home","/"),("Blog","/blog/"),(c,None)])}<h1>{esc(c)}</h1>{cats_nav(c)}<div class="posts">{plist(lst)}</div>',[crumbs([("Home","/"),("Blog","/blog/"),(c,f"/blog/category/{s}/")])]))
    def rcat(p): return f"<category>{esc(p['category'])}</category>" if p.get("category") else ""
    items = "".join(f"<item><title>{esc(p['title'])}</title><link>{SITE_URL}/blog/{p['slug']}/</link><guid>{SITE_URL}/blog/{p['slug']}/</guid><pubDate>{email.utils.format_datetime(p['dt'])}</pubDate>{rcat(p)}<description>{esc(p.get('description',''))}</description></item>" for p in posts)
    open(os.path.join(OUT, "rss.xml"), "w").write(f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel><title>{SITE_NAME} Blog</title><link>{SITE_URL}/blog/</link><description>Men\'s cologne guides</description>{items}</channel></rss>\n')
    print(f"  blog: {len(posts)} published")
    return urls

build()
