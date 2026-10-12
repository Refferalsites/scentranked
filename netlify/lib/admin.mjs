import crypto from "node:crypto";
const env = (k) => process.env[k] || "";
export const COOKIE = "sr_admin";
const TTL = 8 * 3600;
export const REPO = env("GITHUB_REPO") || "Refferalsites/scentranked";
export const BRANCH = env("GITHUB_BRANCH") || "main";

export function json(data, status = 200, headers = {}) {
  return new Response(JSON.stringify(data), { status, headers: { "content-type": "application/json", "cache-control": "no-store", ...headers } });
}
function hmac(s) { return crypto.createHmac("sha256", env("SESSION_SECRET")).update(s).digest("base64url"); }
export function makeSession(user) {
  const payload = Buffer.from(JSON.stringify({ u: user, exp: Math.floor(Date.now() / 1000) + TTL, n: crypto.randomBytes(8).toString("hex") })).toString("base64url");
  return `${payload}.${hmac(payload)}`;
}
export function sessionCookie(v, maxAge = TTL) {
  return `${COOKIE}=${v}; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=${maxAge}`;
}
export function getSession(req) {
  if (!env("SESSION_SECRET")) return null;
  const c = (req.headers.get("cookie") || "").split(/;\s*/).find((x) => x.startsWith(COOKIE + "="));
  if (!c) return null;
  const [p, sig] = c.slice(COOKIE.length + 1).split(".");
  if (!p || !sig) return null;
  const a = Buffer.from(sig), b = Buffer.from(hmac(p));
  if (a.length !== b.length || !crypto.timingSafeEqual(a, b)) return null;
  try { const d = JSON.parse(Buffer.from(p, "base64url").toString()); return d.exp > Date.now() / 1000 ? d : null; } catch { return null; }
}
export function sameOrigin(req) {
  const o = req.headers.get("origin"); if (!o) return true;
  try { return new URL(o).host === new URL(req.url).host; } catch { return false; }
}
// ---- GitHub contents API
async function gh(path, opts = {}) {
  const r = await fetch(`https://api.github.com/repos/${REPO}/${path}`, { ...opts, headers: { authorization: `Bearer ${env("GITHUB_TOKEN")}`, accept: "application/vnd.github+json", "user-agent": "scentranked-admin", ...(opts.headers || {}) } });
  const t = await r.text(); let d; try { d = JSON.parse(t); } catch { d = t; }
  if (!r.ok) throw new Error(`GitHub ${r.status}: ${d && d.message ? d.message : t}`.slice(0, 300));
  return d;
}
export async function ghList(dir) { return gh(`contents/${dir}?ref=${BRANCH}`); }
export async function ghGet(path) {
  const d = await gh(`contents/${path}?ref=${BRANCH}`);
  return { sha: d.sha, text: Buffer.from(d.content, "base64").toString("utf8") };
}
export async function ghPut(path, text, message, sha) {
  return gh(`contents/${path}`, { method: "PUT", body: JSON.stringify({ message, branch: BRANCH, content: Buffer.from(text, "utf8").toString("base64"), ...(sha ? { sha } : {}) }) });
}
export async function ghDelete(path, message, sha) {
  return gh(`contents/${path}`, { method: "DELETE", body: JSON.stringify({ message, branch: BRANCH, sha }) });
}
// ---- Google service-account access token (JWT RS256)
export async function googleToken(envName, scope) {
  const sa = JSON.parse(env(envName));
  const now = Math.floor(Date.now() / 1000);
  const enc = (o) => Buffer.from(JSON.stringify(o)).toString("base64url");
  const unsigned = `${enc({ alg: "RS256", typ: "JWT" })}.${enc({ iss: sa.client_email, scope, aud: "https://oauth2.googleapis.com/token", iat: now, exp: now + 3600 })}`;
  const sig = crypto.sign("RSA-SHA256", Buffer.from(unsigned), sa.private_key).toString("base64url");
  const r = await fetch("https://oauth2.googleapis.com/token", { method: "POST", headers: { "content-type": "application/x-www-form-urlencoded" }, body: `grant_type=urn%3Aietf%3Aparams%3Aoauth%3Agrant-type%3Ajwt-bearer&assertion=${unsigned}.${sig}` });
  const d = await r.json(); if (!r.ok) throw new Error("Google auth failed: " + (d.error_description || d.error));
  return d.access_token;
}
export const has = (k) => Boolean(env(k));
