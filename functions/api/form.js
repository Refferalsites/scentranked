// Replaces Netlify Forms: stores contact/newsletter submissions in KV (binding STORE), honeypot kept.
import { kvGet, kvPut } from "../_lib/admin.js";
const FORMS = { contact: { hp: "bot-field", fields: ["name", "email", "message"], thanks: "/contact/thanks/" }, newsletter: { hp: "company", fields: ["email"], thanks: "/thanks/" } };
const back = (req, path) => new Response(null, { status: 303, headers: { location: new URL(path, req.url).toString() } });
export async function onRequestPost({ request: req, env }) {
  let fd; try { fd = await req.formData(); } catch { return new Response("Bad request", { status: 400 }); }
  const name = String(fd.get("form-name") || ""), cfg = FORMS[name];
  if (!cfg) return new Response("Unknown form", { status: 400 });
  if (String(fd.get(cfg.hp) || "")) return back(req, cfg.thanks);      // bot: pretend success, store nothing
  if (env.TURNSTILE_SECRET) {                                             // optional Cloudflare Turnstile
    const t = String(fd.get("cf-turnstile-response") || "");
    const v = await fetch("https://challenges.cloudflare.com/turnstile/v0/siteverify", { method: "POST", body: new URLSearchParams({ secret: env.TURNSTILE_SECRET, response: t, remoteip: req.headers.get("cf-connecting-ip") || "" }) }).then((r) => r.json()).catch(() => ({}));
    if (!v.success) return new Response("Verification failed. Please go back and try again.", { status: 400 });
  }
  const data = {}; for (const f of cfg.fields) data[f] = String(fd.get(f) || "").slice(0, 4000).trim();
  if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(data.email)) return new Response("Please enter a valid email address.", { status: 400 });
  if (!env.STORE) return new Response("Form storage is not configured.", { status: 500 });
  const id = `${Date.now()}-${crypto.randomUUID().slice(0, 8)}`;
  const entry = { id, form: name, at: new Date().toISOString(), ...data };
  await kvPut(env, `msg:${id}`, entry);
  const idx = await kvGet(env, "msg:index", []); idx.unshift(id); await kvPut(env, "msg:index", idx.slice(0, 2000));
  return back(req, cfg.thanks);
}
export const onRequest = () => new Response("Method not allowed", { status: 405 });
