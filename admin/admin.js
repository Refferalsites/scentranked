(function(){
const $=s=>document.querySelector(s),api="/api/admin-api",msg=t=>{$("#msg").textContent=t||""};
async function call(action,body){const r=await fetch(api+"?action="+action+(body&&body.qs!==undefined?body.qs:""),body&&body.qs===undefined?{method:"POST",headers:{"content-type":"application/json"},body:JSON.stringify(body)}:{credentials:"same-origin"});
 const d=await r.json().catch(()=>({error:"Bad response"}));if(r.status===401){show(false);throw new Error("Session expired, please sign in")}if(!r.ok)throw new Error(d.error||("Error "+r.status));return d}
function show(app){$("#login").hidden=app;$("#app").hidden=!app}
$("#lf").onsubmit=async e=>{e.preventDefault();$("#lerr").textContent="";const f=new FormData(e.target);
 const r=await fetch("/api/admin-login",{method:"POST",headers:{"content-type":"application/json"},body:JSON.stringify({username:f.get("username"),password:f.get("password")})});
 const d=await r.json().catch(()=>({}));if(r.ok){e.target.reset();start()}else $("#lerr").textContent=d.error||"Login failed"};
$("#logout").onclick=async()=>{await fetch("/api/admin-login",{method:"DELETE"});show(false)};
document.querySelectorAll("header nav button").forEach(b=>b.onclick=()=>{document.querySelectorAll("header nav button").forEach(x=>x.classList.toggle("on",x===b));["posts","products","settings","seo","idx","msgs"].forEach(t=>$("#t-"+t).hidden=t!==b.dataset.tab);msg("");if(b.dataset.tab==="msgs")loadMsgs()});
let META={products:[],categories:[]},SET=null,SETSHA=null,PROD=null,CUR=null;
const pf=$("#pf");
function toLocal(iso){const d=new Date(iso);if(isNaN(d))return"";const p=n=>String(n).padStart(2,"0");return d.getFullYear()+"-"+p(d.getMonth()+1)+"-"+p(d.getDate())+"T"+p(d.getHours())+":"+p(d.getMinutes())}
function toIso(local){const d=new Date(local),o=-d.getTimezoneOffset(),p=n=>String(Math.floor(Math.abs(n))).padStart(2,"0");return local+":00"+(o>=0?"+":"-")+p(o/60)+":"+p(o%60)}
async function loadPosts(){const l=await call("posts",{qs:""});$("#plist").innerHTML="";l.sort().forEach(s=>{const li=document.createElement("li");li.textContent=s;li.onclick=()=>openPost(s,li);$("#plist").appendChild(li)})}
async function openPost(slug,li){document.querySelectorAll("#plist li").forEach(x=>x.classList.toggle("on",x===li));msg("Loading…");const p=await call("post",{qs:"&slug="+encodeURIComponent(slug)});CUR=p;fill(p);$("#ptitle").textContent="Edit post";pf.slug.readOnly=true;$("#delpost").hidden=false;pf.hidden=false;msg("")}
function fill(p){pf.title.value=p.title||"";pf.slug.value=p.slug||"";pf.date.value=toLocal(p.date||new Date().toISOString());pf.status.value=p.status==="published"?"published":"draft";pf.category.value=p.category||META.categories[0]||"";pf.image.value=p.image||"";pf.question.value=p.question||"";pf.description.value=p.description||"";pf.body.value=(p.body||"").trim()}
$("#newpost").onclick=()=>{CUR={};fill({status:"draft",body:"**Short answer:** \n\n## Details\n"});$("#ptitle").textContent="New post";pf.slug.readOnly=false;$("#delpost").hidden=true;pf.hidden=false};
pf.title.oninput=()=>{if(!pf.slug.readOnly)pf.slug.value=pf.title.value.toLowerCase().replace(/[^a-z0-9]+/g,"-").replace(/^-|-$/g,"").slice(0,70)};
pf.onsubmit=async e=>{e.preventDefault();msg("Saving…");try{const d=await call("save-post",{slug:pf.slug.value,sha:CUR&&CUR.sha,title:pf.title.value,date:toIso(pf.date.value),status:pf.status.value,category:pf.category.value,image:pf.image.value,question:pf.question.value,description:pf.description.value,body:pf.body.value});
 CUR.sha=d.sha;CUR.slug=pf.slug.value;pf.slug.readOnly=true;msg("Saved. The site rebuilds automatically (about 1 minute).");loadPosts()}catch(err){msg(err.message)}};
$("#delpost").onclick=async()=>{if(!CUR||!CUR.sha||!confirm("Delete this post permanently?"))return;try{await call("delete-post",{slug:CUR.slug,sha:CUR.sha});pf.hidden=true;msg("Deleted.");loadPosts()}catch(err){msg(err.message)}};
async function loadProducts(){PROD=await call("products",{qs:""});const tb=$("#ptable tbody");tb.innerHTML="";const reviewed=new Set(META.products.map(p=>p.key));
 PROD.products.forEach((p,i)=>{const tr=document.createElement("tr");const inp=(k,t="text")=>{const x=document.createElement("input");x.type=t;if(t==="checkbox")x.checked=!!p[k];else x.value=p[k]||"";x.onchange=()=>{p[k]=t==="checkbox"?x.checked:x.value};const td=document.createElement("td");td.appendChild(x);return td};
 const n=inp("name");n.className="n";if(!reviewed.has(p.key))n.title="No review page: not shown on site";tr.append(n,inp("url","url"),inp("price"),inp("compare_at_price"),inp("image","url"),inp("featured","checkbox"),inp("in_merchant_feed","checkbox"));const lc=document.createElement("td");lc.textContent=p.last_checked?new Date(p.last_checked).toLocaleString():"never";const age=p.last_checked?(Date.now()-new Date(p.last_checked))/36e5:1e9;const ss=document.createElement("td");const st=(p.sync&&p.sync.status)||"never";ss.textContent=(age>48?"STALE · ":"")+st+(p.sync&&p.sync.issues&&p.sync.issues.length?" ("+p.sync.issues.join("; ")+")":"");tr.append(lc,ss);tb.appendChild(tr)});loadRuns()}
async function loadRuns(){try{const d=await call("sync-runs",{qs:""});$("#syncruns").textContent="Recent sync runs: "+(d.runs.map(r=>new Date(r.created_at).toLocaleString()+" "+(r.conclusion||r.status)).join(" · ")||"none")}catch(e){}}
$("#syncnow").onclick=async()=>{msg("Starting price sync…");try{await call("sync-now",{});msg("Price sync started on GitHub Actions. It commits changes and the site rebuilds in a few minutes.");setTimeout(loadRuns,5000)}catch(e){msg(e.message)}};
$("#saveprod").onclick=async()=>{msg("Saving products…");try{const d=await call("save-products",{sha:PROD.sha,products:PROD.products});PROD.sha=d.sha;msg("Products saved. Site rebuilding.")}catch(e){msg(e.message)}};
const get=(o,k)=>k.split(".").reduce((a,x)=>a&&a[x],o),put=(o,k,v)=>{const ks=k.split(".");let a=o;ks.slice(0,-1).forEach(x=>a=a[x]=a[x]||{});a[ks.at(-1)]=v};
function fillForm(f){[...f.elements].forEach(el=>{if(!el.name)return;const v=get(SET,el.name);if(el.type==="checkbox")el.checked=!!v;else el.value=v??""})}
async function saveForm(f){[...f.elements].forEach(el=>{if(el.name)put(SET,el.name,el.type==="checkbox"?el.checked:el.value.trim())});msg("Saving…");try{const d=await call("save-settings",{sha:SETSHA,settings:SET});SETSHA=d.sha;msg("Saved. Site rebuilding (about 1 minute).")}catch(e){msg(e.message)}}
$("#sf").onsubmit=e=>{e.preventDefault();saveForm(e.target)};$("#seof").onsubmit=e=>{e.preventDefault();saveForm(e.target)};
async function loadSettings(){const d=await call("settings",{qs:""});SET=d.settings;SETSHA=d.sha;fillForm($("#sf"));fillForm($("#seof"));
 const st=await call("status",{qs:""});$("#smurl").href=$("#smurl").textContent=st.sitemap;$("#mfurl").href=$("#mfurl").textContent=st.merchantFeed;
 $("#gstat").textContent=st.secrets.GOOGLE_INDEXING_SA_JSON?"configured":"not set";$("#gstat").className=st.secrets.GOOGLE_INDEXING_SA_JSON?"ok":"no";
 $("#secrets").innerHTML=Object.entries(st.secrets).map(([k,v])=>`<li><code>${k}</code><span class="${v?"ok":"no"}">${v?"✓ configured":"✗ not set"}</span></li>`).join("")}
$("#gscsubmit").onclick=async()=>{msg("Submitting…");try{const d=await call("gsc-submit-sitemap",{});msg(d.detail)}catch(e){msg(e.message)}};
$("#mcstatus").onclick=async()=>{msg("Checking…");try{const d=await call("merchant-status",{merchantId:get(SET,"seo.merchant_center_id")});msg("Merchant API: "+d.status+" "+d.detail.slice(0,200))}catch(e){msg(e.message)}};
const esc=s=>String(s??"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
function logHtml(a){return (a&&a.length)?"<table><tr><th>When</th><th>Trigger</th><th>Result</th><th>URLs</th><th>Detail</th></tr>"+a.map(e=>`<tr><td>${esc(new Date(e.at).toLocaleString())}</td><td>${esc(e.trigger)}</td><td class="${e.ok?"ok":"no"}">${e.ok?"OK":"Failed"}${e.status?" ("+e.status+")":""}</td><td>${e.count??""}</td><td>${esc(e.detail)}</td></tr>`).join("")+"</table>":"<p class='small'>No runs yet.</p>"}
async function loadIdx(){const l=await call("indexing-log",{qs:""});$("#inlog").innerHTML=logHtml(l.indexnow);$("#glog").innerHTML=logHtml(l.google);const k=get(SET,"seo.indexnow_key");if(k){$("#ikurl").href=$("#ikurl").textContent=location.origin+"/"+k+".txt"}}
$("#inall").onclick=async()=>{msg("Submitting all URLs to IndexNow…");try{const d=await call("indexnow-submit-all",{});msg("IndexNow: "+d.indexnow.detail);loadIdx()}catch(e){msg(e.message)}};
$("#gnow").onclick=async()=>{msg("Sending to Google…");try{const d=await call("google-index-now",{});msg("Google: "+d.detail);loadIdx()}catch(e){msg(e.message)}};
async function start(){try{await call("me",{qs:""})}catch(e){show(false);return}show(true);
 META=await fetch("/admin/meta.json").then(r=>r.json()).catch(()=>META);
 $("#pcat").innerHTML=META.categories.map(c=>`<option>${c}</option>`).join("");
 $("#slugs").innerHTML="";META.products.forEach(p=>{const b=document.createElement("button");b.type="button";b.textContent=p.name;b.title="{{product:"+p.slug+"}}";b.onclick=()=>{const t=pf.body,i=t.selectionStart;t.setRangeText("\n\n{{product:"+p.slug+"}}\n\n",i,t.selectionEnd,"end");t.focus()};$("#slugs").appendChild(b)});
 try{await Promise.all([loadPosts(),loadProducts(),loadSettings()]);await loadIdx()}catch(e){msg(e.message)}}
start();
async function loadMsgs(){const L=$("#msglist");L.textContent="Loading…";try{const d=await call("messages",{qs:""});
 if(!d.kv){L.textContent="KV binding STORE is not configured.";return}
 if(!d.items.length){L.textContent="No messages yet.";return}
 L.innerHTML="<table><tr><th>When</th><th>Form</th><th>Name</th><th>Email</th><th>Message</th><th></th></tr>"+d.items.map(m=>`<tr><td>${esc(new Date(m.at).toLocaleString())}</td><td>${esc(m.form)}</td><td>${esc(m.name||"")}</td><td><a href="mailto:${esc(m.email)}">${esc(m.email)}</a></td><td style="white-space:pre-wrap">${esc(m.message||"")}</td><td><button type="button" class="danger" data-del="${esc(m.id)}">Delete</button></td></tr>`).join("")+"</table>"+(d.total>d.items.length?`<p class="small">Showing ${d.items.length} of ${d.total}</p>`:"");
 L.querySelectorAll("[data-del]").forEach(b=>b.onclick=async()=>{if(!confirm("Delete this message?"))return;try{await call("delete-message",{id:b.dataset.del});loadMsgs()}catch(e){msg(e.message)}})}catch(e){L.textContent=e.message}}
$("#msgreload").onclick=loadMsgs;
})();
