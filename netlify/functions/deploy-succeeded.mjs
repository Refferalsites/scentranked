// Netlify event function: runs automatically after every successful production deploy.
import { runIndexing } from "../lib/indexing.mjs";
export default async (req) => {
  try { const r = await runIndexing("deploy"); return new Response(JSON.stringify(r), { status: 200 }); }
  catch (e) { return new Response(String(e.message || e), { status: 200 }); }
};
