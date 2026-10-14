#!/usr/bin/env python3
"""Shingle/Jaccard similarity gate across site prose. Exit 1 if any pair exceeds threshold."""
import os, re, html, sys, json, collections
BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "public")
THRESH = float(os.environ.get("DUP_THRESH", "0.55"))
N = 5

def texts():
    for root, _, files in os.walk(OUT):
        for f in files:
            if not f.endswith(".html"): continue
            p = os.path.join(root, f)
            h = open(p, encoding="utf-8", errors="ignore").read()
            if 'name="robots" content="noindex' in h: continue
            h = re.sub(r"(?s)<(script|style|nav|header|footer).*?</\1>", " ", h)
            t = html.unescape(re.sub(r"<[^>]+>", " ", h))
            t = re.sub(r"\s+", " ", t).lower()
            # drop boilerplate
            for b in ("scentranked", "purchase now", "we may earn", "affiliate", "yoovic", "shop by", "best lists"):
                t = t.replace(b, " ")
            words = re.findall(r"[a-z]{3,}", t)
            if len(words) < 80: continue
            yield os.path.relpath(p, OUT), words

def shingles(words):
    return {tuple(words[i:i+N]) for i in range(len(words)-N+1)}

def main():
    items = [(p, shingles(w)) for p, w in texts()]
    pairs = []
    for i, (pa, sa) in enumerate(items):
        for pb, sb in items[i+1:]:
            if not sa or not sb: continue
            # skip index vs category thin pairs that share cards
            if ("reviews/" in pa and "reviews/" in pb) or ("brands/" in pa and "brands/" in pb):
                # still check review pages against each other
                pass
            j = len(sa & sb) / len(sa | sb)
            if j >= THRESH: pairs.append((j, pa, pb))
    pairs.sort(reverse=True)
    report = {"threshold": THRESH, "pages_scanned": len(items), "pairs_over_threshold": [{"score": round(j,3), "a": a, "b": b} for j, a, b in pairs[:50]]}
    os.makedirs(os.path.join(BASE, "data"), exist_ok=True)
    json.dump(report, open(os.path.join(BASE, "data", "duplicate_report.json"), "w"), indent=1)
    print(f"Scanned {len(items)} pages; {len(pairs)} pairs >= {THRESH}")
    for j, a, b in pairs[:15]: print(f"  {j:.3f}  {a}  ↔  {b}")
    if pairs:
        print("FAIL: near-duplicate content detected. See data/duplicate_report.json")
        return 1
    print("OK: no near-duplicates above threshold")
    return 0

if __name__ == "__main__":
    sys.exit(main())
