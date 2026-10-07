(function(){
"use strict";
const $ = s => document.querySelector(s);
const esc = s => String(s == null ? "" : s).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const FONTS = window.FUNNIES_FONTS || {};
const fontCSS = Object.entries(FONTS).map(([k, v]) => {
  const [fam, w] = k.split("|");
  return `@font-face{font-family:'${fam}';src:url(${v}) format('truetype');font-weight:${w};font-style:normal}`;
}).join("\n");
if (fontCSS) { const st = document.createElement("style"); st.textContent = fontCSS; document.head.appendChild(st); }

let D, idx = 0, mode = "page";
function toast(t){ const x = $("#toast"); x.textContent = t; x.classList.add("show"); setTimeout(() => x.classList.remove("show"), 1600); }

function load(){
  if (window.FUNNIES) return Promise.resolve(window.FUNNIES);
  return fetch("data/strips.json", {cache:"no-store"}).then(r => r.json());
}

function card(s, i){
  const beats = s.beats && s.beats.length ? `Beats picked: ${s.beats.map(b => `<b>${esc(b.id)}</b>`).join(" · ")}` : (s.kind === "special" ? `${s.panels.length} panels from TokenMax's usage readings + measured project folders` : `${s.panels.length} panels from TokenMax Hub + usage.json`);
  return `<article class="strip-card ${s.kind}" id="${esc(s.id)}" data-i="${i}">
    <div class="svgwrap">${s.svg}</div>
    <div class="strip-tools"><span class="beats">${beats}</span>
      <button class="btn" data-png="${i}">⬇ PNG</button>
      <button class="btn" data-open="${i}">🔎 Open</button>
      <button class="btn" data-link="${i}">🔗 Link</button></div></article>`;
}

function renderArchive(){
  $("#archive").innerHTML = D.strips.map((s, i) =>
    `<button class="chip ${s.kind !== "daily" ? "sun" : ""}" data-i="${i}"><small>${esc(s.kind === "sunday" ? "☀️ Sunday" : s.kind === "special" ? "🚀 Special" : s.date_label.split(",").slice(0, 2).join(",").replace(/^\w+day, /, ""))}</small>${esc(s.title)}</button>`).join("");
  $("#archive").querySelectorAll(".chip").forEach(c => c.addEventListener("click", () => { const i = +c.dataset.i; if (mode === "page") { goPage(i); } else show(i); }));
}

function renderPage(){
  const order = D.strips.map((s, i) => i).reverse();       // newest first, like a paper
  const sun = order.filter(i => D.strips[i].kind !== "daily"), dl = order.filter(i => D.strips[i].kind === "daily");
  $("#page").innerHTML = `<div class="page-head"><h2>Today's funnies</h2><span>${dl.length} daily strips + ${sun.length > 1 ? "the Build Night Special and " : ""}the Sunday special · newest first</span></div>` +
    [...sun, ...dl].map(i => card(D.strips[i], i)).join("");
}

function show(i){
  idx = Math.max(0, Math.min(D.strips.length - 1, i));
  const s = D.strips[idx];
  $("#sDate").textContent = s.date_label; $("#sTitle").textContent = s.title;
  // unique SVG ids in single view (the comics page holds the same strip)
  $("#singleStrip").innerHTML = card(s, idx).replace(/id="([^"]+)"/g, 'id="$1-1up"').replace(/url\(#([^)]+)\)/g, "url(#$1-1up)");
  $("#prev").disabled = idx === 0; $("#next").disabled = idx === D.strips.length - 1;
  markChip(idx);
  history.replaceState(null, "", "#" + s.id);
}
function markChip(i){ document.querySelectorAll(".chip").forEach(c => c.classList.toggle("on", +c.dataset.i === i)); const c = document.querySelector(`.chip[data-i="${i}"]`); if (c) c.scrollIntoView({block:"nearest", inline:"center"}); }
function goPage(i){ const el = document.getElementById(D.strips[i].id); if (el) { el.scrollIntoView({behavior:"smooth", block:"start"}); markChip(i); history.replaceState(null, "", "#" + D.strips[i].id); } }

function setMode(m, i){
  mode = m;
  $("#btnPage").classList.toggle("on", m === "page"); $("#btnSingle").classList.toggle("on", m === "single");
  $("#page").hidden = m !== "page"; $("#single").hidden = m !== "single";
  if (m === "single") show(i == null ? idx : i);
}

function toCanvas(i, done, fail){
  const s = D.strips[i];
  const tmp = document.createElement("div"); tmp.innerHTML = s.svg;
  const svg = tmp.querySelector("svg");
  const st = document.createElementNS("http://www.w3.org/2000/svg", "style"); st.textContent = fontCSS; svg.insertBefore(st, svg.firstChild);
  const w = +svg.getAttribute("width"), h = +svg.getAttribute("height"), k = 2;
  const url = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(new XMLSerializer().serializeToString(svg));
  const img = new Image();
  img.onload = () => { const cv = document.createElement("canvas"); cv.width = w * k; cv.height = h * k; const cx = cv.getContext("2d"); cx.scale(k, k); cx.drawImage(img, 0, 0, w, h); done(cv, s); };
  img.onerror = () => fail && fail();
  img.src = url;
}
function exportPNG(i){
  toCanvas(i, (cv, s) => cv.toBlob(b => { const a = document.createElement("a"); a.href = URL.createObjectURL(b); a.download = `fleet-funnies-${s.id}.png`; document.body.appendChild(a); a.click(); a.remove(); toast(`Saved fleet-funnies-${s.id}.png`); }, "image/png"),
           () => toast("PNG export failed in this browser"));
}

function wire(){
  document.addEventListener("click", e => {
    const b = e.target.closest("[data-png],[data-open],[data-link]"); if (!b) return;
    if (b.dataset.png != null) exportPNG(+b.dataset.png);
    else if (b.dataset.open != null) setMode("single", +b.dataset.open);
    else { const u = location.href.split("#")[0] + "#" + D.strips[+b.dataset.link].id; (navigator.clipboard && window.isSecureContext ? navigator.clipboard.writeText(u) : Promise.reject()).then(() => toast("Link copied"), () => toast(u)); }
  });
  $("#btnPage").addEventListener("click", () => setMode("page"));
  $("#btnSingle").addEventListener("click", () => setMode("single"));
  $("#prev").addEventListener("click", () => show(idx - 1));
  $("#next").addEventListener("click", () => show(idx + 1));
  document.addEventListener("keydown", e => {
    if (e.key === "ArrowLeft") { mode === "single" ? show(idx - 1) : setMode("single", Math.max(0, idx - 1)); }
    if (e.key === "ArrowRight") { mode === "single" ? show(idx + 1) : setMode("single", Math.min(D.strips.length - 1, idx + 1)); }
  });
  if (window.FUNNIES) {   // offline snapshot: no PDF file next to it, so print this page (letter-size print CSS)
    const p = $("#btnPrint"); p.removeAttribute("href"); p.removeAttribute("target");
    p.textContent = "🖨️ Print the funnies"; p.addEventListener("click", e => { e.preventDefault(); setMode("page"); setTimeout(() => window.print(), 50); });
  }
}

load().then(d => {
  D = d; idx = D.strips.length - 1;
  renderArchive(); renderPage(); wire();
  $("#meta").textContent = `Generated ${D.meta.generated} · fleet data ${D.meta.fleetGeneratedAt} · local logs end ${D.meta.logs_end.slice(0, 16).replace("T", " ")} ET · ${D.strips.length} strips`;
  const q = new URLSearchParams(location.search), h = location.hash.slice(1);
  const hi = D.strips.findIndex(s => s.id === h);
  if (q.get("view") === "single" || (hi >= 0 && q.get("view") !== "page")) setMode("single", hi >= 0 ? hi : idx);
  else { setMode("page"); markChip(D.strips.length - 1); }
  document.body.dataset.ready = "1";
  if (q.get("selftest") === "png") toCanvas(D.strips.length - 1, cv => { const u = cv.toDataURL("image/png"); document.body.dataset.pngBytes = String(u.length); document.body.dataset.pngSize = cv.width + "x" + cv.height; }, () => { document.body.dataset.pngBytes = "0"; });
}).catch(err => { $("#main").innerHTML = `<pre>Couldn't load strips: ${esc(err)}</pre>`; });
})();
