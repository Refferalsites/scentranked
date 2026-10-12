import { getStore } from "@netlify/blobs";
import { googleToken, has } from "./admin.mjs";
const SITE = () => process.env.URL || "https://scentranked.netlify.app";
const store = () => getStore("indexing");
async function fetchJson(u) { const r = await fetch(u, { headers: { "cache-control": "no-cache" } }); if (!r.ok) throw new Error(`${u} -> ${r.status}`); return r.json(); }
export async function getLog() { return (await store().get("log", { type: "json" })) || { indexnow: [], google: [] }; }
async function addLog(kind, entry) { const l = await getLog(); l[kind] = [entry, ...(l[kind] || [])].slice(0, 20); await store().setJSON("log", l); }
// Diff the build's URL->hash manifest against the last submitted snapshot.
export async function changedUrls(all = false) {
  const man = await fetchJson(`${SITE()}/indexnow-urls.json`);
  const prev = all ? {} : ((await store().get("snapshot", { type: "json" })) || {});
  const changed = Object.keys(man.urls).filter((u) => prev[u] !== man.urls[u]);
  return { man, changed };
}
export async function submitIndexNow(urls, key, trigger) {
  const host = new URL(SITE()).host;
  if (!key) { const e = { at: new Date().toISOString(), trigger, ok: false, detail: "No IndexNow key in settings" }; await addLog("indexnow", e); return e; }
  if (!urls.length) { const e = { at: new Date().toISOString(), trigger, ok: true, count: 0, detail: "No new or changed URLs" }; await addLog("indexnow", e); return e; }
  const r = await fetch("https://api.indexnow.org/indexnow", { method: "POST", headers: { "content-type": "application/json; charset=utf-8" },
    body: JSON.stringify({ host, key, keyLocation: `${SITE()}/${key}.txt`, urlList: urls.slice(0, 10000) }) });
  const e = { at: new Date().toISOString(), trigger, ok: r.status === 200 || r.status === 202, status: r.status, count: urls.length, detail: (await r.text()).slice(0, 200) || (r.status === 202 ? "Accepted (key validation pending)" : "OK"), sample: urls.slice(0, 5) };
  await addLog("indexnow", e); return e;
}
export async function submitGoogle(urls, trigger) {
  if (!has("GOOGLE_INDEXING_SA_JSON")) { const e = { at: new Date().toISOString(), trigger, ok: false, detail: "GOOGLE_INDEXING_SA_JSON not set (skipped)" }; await addLog("google", e); return e; }
  const posts = urls.filter((u) => /\/blog\/[^/]+\/$/.test(u)).slice(0, 100);   // stay well under the default 200/day quota
  if (!posts.length) { const e = { at: new Date().toISOString(), trigger, ok: true, count: 0, detail: "No new or changed blog posts" }; await addLog("google", e); return e; }
  const tok = await googleToken("GOOGLE_INDEXING_SA_JSON", "https://www.googleapis.com/auth/indexing");
  const res = [];
  for (const u of posts) {
    const r = await fetch("https://indexing.googleapis.com/v3/urlNotifications:publish", { method: "POST", headers: { authorization: `Bearer ${tok}`, "content-type": "application/json" }, body: JSON.stringify({ url: u, type: "URL_UPDATED" }) });
    res.push({ url: u, status: r.status }); if (r.status === 429) break;
  }
  const ok = res.filter((x) => x.status === 200).length;
  const e = { at: new Date().toISOString(), trigger, ok: ok === res.length, count: res.length, detail: `${ok}/${res.length} accepted`, sample: res.slice(0, 5) };
  await addLog("google", e); return e;
}
export async function runIndexing(trigger, all = false) {
  const { man, changed } = await changedUrls(all);
  const a = await submitIndexNow(changed, man.indexnow_key, trigger);
  let g; try { g = await submitGoogle(changed, trigger); } catch (err) { g = { ok: false, detail: String(err.message) }; await addLog("google", { at: new Date().toISOString(), trigger, ...g }); }
  if (a.ok) await store().setJSON("snapshot", man.urls);
  return { indexnow: a, google: g };
}
