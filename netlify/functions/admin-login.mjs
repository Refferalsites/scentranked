import crypto from "node:crypto";
import { getStore } from "@netlify/blobs";
import { json, makeSession, sessionCookie, sameOrigin } from "../lib/admin.mjs";
// Best-effort rate limit: per warm function instance. 5 failures / 15 min per IP, plus a global floor delay.
const fails = new Map();
const WINDOW = 15 * 60 * 1000, MAX = 5;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const digest = (s) => crypto.createHash("sha256").update(String(s), "utf8").digest();
export default async (req, context) => {
  if (req.method === "DELETE") return json({ ok: true }, 200, { "set-cookie": sessionCookie("", 0) });
  if (req.method !== "POST") return json({ error: "Method not allowed" }, 405);
  if (!sameOrigin(req)) return json({ error: "Bad origin" }, 403);
  const U = process.env.ADMIN_USERNAME || "", H = (process.env.ADMIN_PASSWORD_SHA256 || "").trim().toLowerCase();
  if (!U || !/^[0-9a-f]{64}$/.test(H) || !process.env.SESSION_SECRET) return json({ error: "Admin login is not configured on the server." }, 500);
  const ip = context?.ip || req.headers.get("x-nf-client-connection-ip") || "unknown";
  const now = Date.now(); let st = null; try { st = getStore("admin-rate"); } catch {}
  const key = "ip-" + String(ip).replace(/[^0-9a-fA-F:.]/g, "");
  let rec = (fails.get(ip) || []); try { if (st) rec = rec.concat((await st.get(key, { type: "json" })) || []); } catch {}
  rec = [...new Set(rec)].filter((t) => now - t < WINDOW);
  if (rec.length >= MAX) return json({ error: "Too many attempts. Try again in 15 minutes." }, 429, { "retry-after": "900" });
  let body = {}; try { body = await req.json(); } catch {}
  const userOk = crypto.timingSafeEqual(digest(body.username || ""), digest(U));
  const passOk = crypto.timingSafeEqual(digest(body.password || ""), Buffer.from(H, "hex"));
  await sleep(400 + Math.floor(Math.random() * 300));
  if (!(userOk && passOk)) { rec.push(now); fails.set(ip, rec); try { if (st) await st.setJSON(key, rec); } catch {} return json({ error: "Invalid username or password." }, 401); }
  fails.delete(ip); try { if (st) await st.delete(key); } catch {}
  return json({ ok: true, user: U }, 200, { "set-cookie": sessionCookie(makeSession(U)) });
};
