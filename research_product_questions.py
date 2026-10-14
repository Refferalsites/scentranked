#!/usr/bin/env python3
"""Collect product-specific search questions from Google Autocomplete (US) -> data/product_questions.json"""
import json, urllib.request, urllib.parse, concurrent.futures as cf, datetime, re, time
Q = {"bleu-de-chanel-edt":"bleu de chanel","versace-eros-edt":"versace eros","versace-eros-flame":"versace eros flame","paco-rabanne-1-million-edt":"1 million paco rabanne",
"paco-rabanne-1-million-parfum":"1 million parfum","jean-paul-gaultier-le-male-edt":"le male","jean-paul-gaultier-le-male-le-parfum":"le male le parfum",
"jean-paul-gaultier-le-beau-le-parfum":"le beau le parfum","armani-acqua-di-gio-profondo":"acqua di gio profondo","bvlgari-aqva-pour-homme-marine":"bvlgari aqva marine",
"prada-luna-rossa-ocean-le-parfum":"luna rossa ocean le parfum","montblanc-legend-blue-edp":"montblanc legend blue","azzaro-wanted-edt":"azzaro wanted",
"azzaro-the-most-wanted-parfum":"azzaro the most wanted parfum","carolina-herrera-212-men":"212 men","valentino-uomo-born-in-roma-the-gold":"born in roma the gold",
"chanel-allure-homme-sport-extreme":"allure homme sport eau extreme","creed-silver-mountain-water":"silver mountain water","creed-royal-oud":"creed royal oud",
"parfums-de-marly-greenley":"pdm greenley","afnan-9-pm":"afnan 9pm","lattafa-qaed-al-fursan":"qaed al fursan"}
MODS = ["is", "does", "what", "how", "which", "can", "when", "why", "should"]
def ac(q):
    u = "https://suggestqueries.google.com/complete/search?client=firefox&hl=en&gl=us&q=" + urllib.parse.quote(q)
    for i in range(3):
        try: return json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=15).read().decode("utf-8", "ignore"))[1]
        except Exception: time.sleep(2)
    return []
out = {"meta": {"fetched": datetime.date.today().isoformat(), "source": "Google Autocomplete suggestqueries.google.com (gl=us, hl=en)", "note": "Search suggestions, not customer questions. No volumes implied."}, "products": {}}
jobs = [(slug, f"{m} {name}") for slug, name in Q.items() for m in MODS] + [(slug, f"{name} ") for slug, name in Q.items()]
with cf.ThreadPoolExecutor(10) as ex: res = list(ex.map(lambda j: (j, ac(j[1])), jobs))
for (slug, q), sug in res:
    d = out["products"].setdefault(slug, {"query_name": Q[slug], "suggestions": []})
    for s in sug: d["suggestions"].append({"text": s, "seed": q})
for d in out["products"].values():
    seen = set(); d["suggestions"] = [x for x in d["suggestions"] if not (x["text"] in seen or seen.add(x["text"]))]
json.dump(out, open("data/product_questions_raw.json", "w"), indent=1)
print({k: len(v["suggestions"]) for k, v in out["products"].items()})
