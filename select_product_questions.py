#!/usr/bin/env python3
"""Pick 5-10 distinct, answerable questions per product from autocomplete suggestions (one per intent pattern)."""
import json, re
raw = json.load(open("data/product_questions_raw.json"))
PATTERNS = [  # (pattern id, regex) - order = priority
 ("smell", r"\b(smell|smells|notes|scent like)\b"),
 ("gender", r"\b(for men or women|for women|unisex|for men)\b"),
 ("season", r"\b(summer|winter|fall|spring|seasons?)\b"),
 ("longevity", r"\b(last long|lasts?|longevity|long lasting|how long)\b"),
 ("concentration", r"\b(edt or edp|edp or edt|eau de toilette|eau de parfum|edp vs|edt vs|concentration|cologne or perfume|parfum or)\b"),
 ("price", r"\b(how much|price|cost|cheap|expensive|on sale|sale)\b"),
 ("worth", r"\b(worth it|worth buying|good|any good|best)\b"),
 ("occasion", r"\b(office|work|date|school|club|wedding|everyday|daily)\b"),
 ("release", r"\b(when did|come out|released?|launch|what year|discontinued)\b"),
 ("refill", r"\brefill"),
 ("authentic", r"\b(real|fake|original|authentic)\b"),
 ("size", r"\b(ml|oz|size|bottle)\b"),
]
BAD = r"\b(elixir|absolu|intense|energy|essence|lover|pride|in blue|lucky|priv[eé]|reddit|dupe|tester|travel|gift set|near me|ulta|sephora|macy|walmart|amazon|costco|tj maxx|marshalls|philippines|india|uae|pakistan|uk|canada|pronounce|meme|hated|red flag|womens?|her|vs|similar|like\b(?! smell))"
out = {"meta": {**raw["meta"], "method": "One question per intent pattern, filtered to the exact product (other flankers, retailers and countries excluded). Answers are rendered from verified data at build time."}, "products": {}}
for slug, d in raw["products"].items():
    name = d["query_name"]; picked = {}
    for s in d["suggestions"]:
        t = s["text"].lower()
        if name.split()[0] not in t: continue
        rest = t.replace(name, " ")
        bad = [w for w in re.findall(BAD, rest)]
        if bad: continue
        if not re.match(r"^(is|does|what|how|which|can|when|why|should|are|do)\b", t): continue
        for pid, rx in PATTERNS:
            if pid not in picked and re.search(rx, rest):
                picked[pid] = {"question": t[0].upper() + t[1:].rstrip("?") + "?", "pattern": pid, "source": f"Google Autocomplete (US), seed \"{s['seed']}\""}
                break
    out["products"][slug] = [picked[p] for p, _ in PATTERNS if p in picked][:10]
json.dump(out, open("data/product_questions.json", "w"), indent=1)
for k, v in out["products"].items(): print(len(v), k, [x["pattern"] for x in v])
