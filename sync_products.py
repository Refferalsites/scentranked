#!/usr/bin/env python3
"""Sync product data from each product's yoovic.com page (the single source of truth).
Updates data/products.json in place. Never overwrites good data with bad data:
- fetch/parse failures keep the previous values and mark sync.status = "failed"
- suspicious changes (non-USD, out of range, >60% price jump) keep previous values and mark "conflict"
Writes data/sync_report.json and appends price changes to data/price_history.json.
Stdlib only (Python 3.11+)."""
import json, re, html, os, sys, time, datetime, urllib.request, concurrent.futures as cf

BASE = os.path.dirname(os.path.abspath(__file__))
PF = os.path.join(BASE, "data", "products.json")
UA = "Mozilla/5.0 (compatible; ScentRankedPriceSync/1.0; +https://scentranked.pages.dev/about/)"
NOW = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)

def fetch(url):
    last = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html"})
            with urllib.request.urlopen(req, timeout=45) as r:
                if r.status != 200: raise RuntimeError(f"HTTP {r.status}")
                return r.read().decode("utf-8", "ignore"), r.geturl()
        except Exception as e:
            last = e; time.sleep(2 + attempt * 3)
    raise RuntimeError(str(last))

def money(s):
    m = re.fullmatch(r"\s*\$\s?([0-9]{1,5}(?:,[0-9]{3})*(?:\.[0-9]{2})?)\s*", s or "")
    return float(m.group(1).replace(",", "")) if m else None

def parse(h):
    d = {}
    t = re.search(r"<title>(.*?)</title>", h, re.S)
    d["title"] = html.unescape(re.sub(r"\s+", " ", t.group(1))).strip() if t else None
    pt = re.search(r'<h5 class="product-title[^"]*">(.*?)</h5>', h, re.S)
    if pt: d["title"] = html.unescape(re.sub(r"<[^>]+>|\s+", " ", pt.group(1))).strip()
    p = re.search(r'<span class="price-now[^"]*">\s*([^<]+?)\s*</span>', h)
    d["price_raw"] = p.group(1).strip() if p else None
    old = [x.strip() for x in re.findall(r'class="sidebar-price-old"[^>]*>\s*([^<]*)<', h) if x.strip()]
    d["compare_raw"] = old[0] if old else None
    cut = h.find("top-usp__logo"); seg = h[:cut] if cut > 0 else h
    imgs = list(dict.fromkeys(re.findall(r'<img src="(https://yoovic\.com/storage/vendor-media/[^"]+)"', seg)))
    d["gallery"] = imgs[:6]
    d["free_shipping_shown"] = "100% Free Shipping" in h
    d["expedited_shown"] = "Expedited shipping available" in h
    d["add_to_cart_shown"] = 'id="add-to-cart-form"' in h and "Buy Now" in h
    d["out_of_stock_shown"] = bool(re.search(r">\s*(Out of Stock|Sold Out|Currently unavailable)\s*<", h, re.I))
    d["currency_usd"] = "$ - USD" in h or (d["price_raw"] or "").startswith("$")
    return d

def sync_one(p):
    prev = p.get("sync", {})
    rec = {"checked_at": NOW.isoformat(), "status": "ok", "issues": []}
    try:
        h, final = fetch(p["url"])
        d = parse(h)
    except Exception as e:
        rec.update(status="failed", issues=[f"fetch failed: {e}"])
        return p, rec, None
    price = money(d["price_raw"])
    if price is None: rec["issues"].append(f"price not found/parseable: {d['price_raw']!r}")
    elif not d["currency_usd"]: rec["issues"].append("currency not USD")
    elif not (1 <= price <= 5000): rec["issues"].append(f"price out of range: {price}")
    old_price = money(p.get("price"))
    if price and old_price and abs(price - old_price) / old_price > 0.6 and not prev.get("confirm_jump"):
        rec["issues"].append(f"price jump {old_price} -> {price} (>60%); needs manual confirmation")
    if rec["issues"]:
        rec["status"] = "conflict" if price is not None else "failed"
        return p, rec, None
    change = None
    new = dict(p)
    newp = f"${price:,.2f}"
    if newp != p.get("price"): change = {"key": p["key"], "name": p["name"][:80], "from": p.get("price"), "to": newp, "at": NOW.isoformat()}
    new["price"] = newp
    cmp = money(d["compare_raw"])
    new["compare_at_price"] = f"${cmp:,.2f}" if cmp and cmp > price else ""
    if d["title"]: new["retailer_title"] = d["title"]
    if d["gallery"]:
        new["image"] = d["gallery"][0]; new["gallery"] = d["gallery"]
    new["retailer"] = {k: d[k] for k in ("free_shipping_shown", "expedited_shown", "add_to_cart_shown", "out_of_stock_shown")}
    new["availability"] = "out_of_stock" if d["out_of_stock_shown"] else ("add_to_cart_shown" if d["add_to_cart_shown"] else "unknown")
    new["last_checked"] = NOW.isoformat()
    return new, rec, change

def main():
    data = json.load(open(PF))
    prods = data["products"]
    only = set(sys.argv[1:])
    targets = [p for p in prods if not only or str(p["key"]) in only]
    with cf.ThreadPoolExecutor(6) as ex: res = list(ex.map(sync_one, targets))
    bykey = {p["key"]: p for p in prods}; changes = []; report = []
    for new, rec, ch in res:
        new["sync"] = rec; bykey[new["key"]] = new
        report.append({"key": new["key"], "name": new["name"][:70], **rec})
        if ch: changes.append(ch)
    data["products"] = [bykey[p["key"]] for p in prods]
    data["synced_at"] = NOW.isoformat()
    json.dump(data, open(PF, "w"), indent=1, ensure_ascii=False); open(PF, "a").write("\n")
    hist_f = os.path.join(BASE, "data", "price_history.json")
    hist = json.load(open(hist_f)) if os.path.exists(hist_f) else []
    if changes: json.dump((hist + changes)[-2000:], open(hist_f, "w"), indent=1, ensure_ascii=False)
    summary = {"ran_at": NOW.isoformat(), "checked": len(report), "ok": sum(r["status"] == "ok" for r in report),
               "failed": sum(r["status"] == "failed" for r in report), "conflict": sum(r["status"] == "conflict" for r in report), "price_changes": changes,
               "problems": [r for r in report if r["status"] != "ok"]}
    json.dump(summary, open(os.path.join(BASE, "data", "sync_report.json"), "w"), indent=1, ensure_ascii=False)
    print(json.dumps({k: summary[k] for k in ("checked", "ok", "failed", "conflict")}), f"price changes: {len(changes)}")
    for c in changes: print("  CHANGE", c["name"], c["from"], "->", c["to"])
    for r in summary["problems"]: print("  ISSUE", r["status"], r["name"], r["issues"])

if __name__ == "__main__": main()
