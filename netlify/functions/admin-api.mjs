import { getLog, runIndexing, submitGoogle, changedUrls } from "../lib/indexing.mjs";
import { json, getSession, sameOrigin, ghList, ghGet, ghPut, ghDelete, googleToken, has, REPO } from "../lib/admin.mjs";
const SITE = process.env.URL || "https://scentranked.netlify.app";
const SECRETS = ["ADMIN_USERNAME", "ADMIN_PASSWORD_SHA256", "SESSION_SECRET", "GITHUB_TOKEN", "GSC_SERVICE_ACCOUNT_JSON", "MERCHANT_SERVICE_ACCOUNT_JSON", "GOOGLE_INDEXING_SA_JSON"];
const q = (s) => JSON.stringify(String(s ?? ""));   // JSON string == valid YAML scalar
const SLUG = /^[a-z0-9][a-z0-9-]{1,80}$/;
function frontmatter(p) {
  const lines = ["---", `title: ${q(p.title)}`, `date: ${q(p.date)}`, `description: ${q(p.description)}`, `image: ${q(p.image)}`, `category: ${q(p.category)}`, `status: ${p.status === "published" ? "published" : "draft"}`, "---", ""];
  return lines.join("\n") + String(p.body || "").replace(/\r\n/g, "\n").trim() + "\n";
}
function parseFront(t) {
  const m = t.match(/^---\s*\n([\s\S]*?)\n---\s*\n([\s\S]*)$/); if (!m) return { body: t };
  const meta = {};
  for (const line of m[1].split("\n")) { const i = line.indexOf(":"); if (i < 0) continue; let v = line.slice(i + 1).trim();
    if (v.startsWith('"')) { try { v = JSON.parse(v); } catch {} } else v = v.replace(/^'|'$/g, ""); meta[line.slice(0, i).trim()] = v; }
  return { ...meta, body: m[2] };
}
export default async (req) => {
  const s = getSession(req); if (!s) return json({ error: "Not logged in" }, 401);
  if (req.method !== "GET" && !sameOrigin(req)) return json({ error: "Bad origin" }, 403);
  const url = new URL(req.url); const a = url.searchParams.get("action");
  const body = req.method === "POST" ? await req.json().catch(() => ({})) : {};
  try {
    if (a === "me") return json({ user: s.u });
    if (a === "status") return json({ repo: REPO, site: SITE, sitemap: `${SITE}/sitemap.xml`, merchantFeed: `${SITE}/merchant-feed.xml`, secrets: Object.fromEntries(SECRETS.map((k) => [k, has(k)])) });
    if (a === "posts") { const l = await ghList("content/blog"); return json(l.filter((f) => f.name.endsWith(".md")).map((f) => f.name.replace(/\.md$/, ""))); }
    if (a === "post") { const slug = url.searchParams.get("slug"); if (!SLUG.test(slug || "")) return json({ error: "Bad slug" }, 400);
      const f = await ghGet(`content/blog/${slug}.md`); return json({ slug, sha: f.sha, ...parseFront(f.text) }); }
    if (a === "save-post") { const p = body; if (!SLUG.test(p.slug || "")) return json({ error: "Slug must be lowercase letters, numbers and hyphens" }, 400);
      if (!p.title || !p.date) return json({ error: "Title and date are required" }, 400);
      const r = await ghPut(`content/blog/${p.slug}.md`, frontmatter(p), `${p.sha ? "Update" : "Add"} post: ${p.title} (admin)`, p.sha || undefined); return json({ ok: true, sha: r.content.sha }); }
    if (a === "delete-post") { if (!SLUG.test(body.slug || "")) return json({ error: "Bad slug" }, 400);
      await ghDelete(`content/blog/${body.slug}.md`, `Delete post: ${body.slug} (admin)`, body.sha); return json({ ok: true }); }
    if (a === "products") { const f = await ghGet("data/products.json"); return json({ sha: f.sha, ...JSON.parse(f.text) }); }
    if (a === "save-products") { if (!Array.isArray(body.products)) return json({ error: "products must be an array" }, 400);
      for (const p of body.products) { if (!/^https:\/\/(www\.)?yoovic\.com\//.test(p.url || "")) return json({ error: `Product URL must be a yoovic.com URL: ${p.name}` }, 400); }
      const r = await ghPut("data/products.json", JSON.stringify({ products: body.products }, null, 1) + "\n", "Update products (admin)", body.sha); return json({ ok: true, sha: r.content.sha }); }
    if (a === "settings") { const f = await ghGet("data/settings.json"); return json({ sha: f.sha, settings: JSON.parse(f.text) }); }
    if (a === "save-settings") { if (typeof body.settings !== "object") return json({ error: "Bad settings" }, 400);
      const r = await ghPut("data/settings.json", JSON.stringify(body.settings, null, 1) + "\n", "Update site settings (admin)", body.sha); return json({ ok: true, sha: r.content.sha }); }
    if (a === "gsc-submit-sitemap") { if (!has("GSC_SERVICE_ACCOUNT_JSON")) return json({ error: "GSC_SERVICE_ACCOUNT_JSON is not set in Netlify environment variables" }, 400);
      const tok = await googleToken("GSC_SERVICE_ACCOUNT_JSON", "https://www.googleapis.com/auth/webmasters");
      const prop = process.env.GSC_PROPERTY || `${SITE}/`;
      const r = await fetch(`https://www.googleapis.com/webmasters/v3/sites/${encodeURIComponent(prop)}/sitemaps/${encodeURIComponent(SITE + "/sitemap.xml")}`, { method: "PUT", headers: { authorization: `Bearer ${tok}` } });
      return json({ ok: r.ok, status: r.status, detail: r.ok ? "Sitemap submitted" : (await r.text()).slice(0, 400) }, r.ok ? 200 : 502); }
    if (a === "merchant-status") { if (!has("MERCHANT_SERVICE_ACCOUNT_JSON")) return json({ error: "MERCHANT_SERVICE_ACCOUNT_JSON is not set in Netlify environment variables" }, 400);
      const id = String(body.merchantId || "").replace(/\D/g, ""); if (!id) return json({ error: "Set a Merchant Center ID in settings first" }, 400);
      const tok = await googleToken("MERCHANT_SERVICE_ACCOUNT_JSON", "https://www.googleapis.com/auth/content");
      const r = await fetch(`https://merchantapi.googleapis.com/accounts/v1/accounts/${id}`, { headers: { authorization: `Bearer ${tok}` } });
      return json({ ok: r.ok, status: r.status, detail: (await r.text()).slice(0, 600) }, r.ok ? 200 : 502); }
    if (a === "indexing-log") return json(await getLog());
    if (a === "indexnow-submit-all") return json(await runIndexing("manual (all URLs)", true));
    if (a === "google-index-now") { const { changed } = await changedUrls(Boolean(body.all)); return json(await submitGoogle(changed, "manual")); }
    return json({ error: "Unknown action" }, 400);
  } catch (e) { return json({ error: String(e.message || e) }, 500); }
};
