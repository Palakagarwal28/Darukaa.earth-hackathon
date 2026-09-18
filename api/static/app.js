/* Darukaa.Earth frontend — talks to /chat /assess /knowledge/search /provenance /health */
const $ = (id) => document.getElementById(id);
const esc = (s) => String(s ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

async function api(path, opts) {
  const r = await fetch(path, opts);
  if (!r.ok) { const t = await r.text(); throw new Error(`HTTP ${r.status_code || r.status} — ${t.slice(0, 200)}`); }
  return r.json();
}

/* ---------- status ---------- */
async function loadStatus() {
  const dot = $("dot"), txt = $("statusTxt");
  try {
    const [h, i] = await Promise.all([api("/health"), api("/integrations/status")]);
    dot.className = "dot ok";
    txt.textContent = `${h.kb_cards} evidence cards · ${i.retriever_backend} retrieval · climate: ${i.open_meteo} · LLM ${i.llm_configured ? "on" : "off (deterministic)"}`;
  } catch (e) { dot.className = "dot bad"; txt.textContent = "backend unreachable — start with: uvicorn api.main:app"; }
}

/* ---------- tabs ---------- */
function tab(name) {
  document.querySelectorAll(".tab").forEach(b => b.classList.toggle("active", b.dataset.tab === name));
  document.querySelectorAll(".panel").forEach(p => p.classList.toggle("active", p.id === "panel-" + name));
}

/* ---------- provenance modal ---------- */
async function showProvenance(ids) {
  const m = $("modal"), box = $("modalBox");
  m.classList.add("open"); box.innerHTML = "<p><span class='spin'></span> loading evidence…</p>";
  try {
    const cards = await api("/provenance?ids=" + encodeURIComponent(ids.join(",")));
    box.innerHTML = "<h3>Evidence grounding</h3>" + cards.map(fullCard).join("") +
      "<div class='row'><button class='ghost' onclick=\"document.getElementById('modal').classList.remove('open')\">Close</button></div>";
  } catch (e) { box.innerHTML = `<p>Failed: ${esc(e.message)}</p>`; }
}
function fullCard(c) {
  return `<div class="rec"><h4>${esc(c.id)} · ${esc(c.title)}</h4>
    <div class="why"><b>Intervention:</b> ${esc(c.intervention)}</div>
    <div class="why"><b>Mechanism:</b> ${esc(c.mechanism)}</div>
    <div class="badges"><span class="badge">${esc(c.time_horizon)}</span>
    <span class="badge">${esc(c.confidence)} confidence</span>
    ${(c.metrics_improved || []).map(m => `<span class="badge">${esc(m)}</span>`).join("")}</div>
    <div class="why"><b>Effect:</b> ${esc(c.effect_size)}</div>
    <div class="src">Ref: ${esc(c.source)}${c.source_url ? ` · <a href="${esc(c.source_url)}" target="_blank">source</a>` : ""}</div></div>`;
}

/* ---------- shared report renderer ---------- */
function reportHTML(j) {
  window._lastReport = j;
  let h = `<div class="row"><button class="ghost" onclick="downloadReport()">⬇ Download report (.md)</button></div>`;
  if (j.diagnosis_interactions)
    h += `<div class="diag"><b>Diagnosis (${j.variables_count} variables):</b><br>• ${j.diagnosis_interactions.map(esc).join("<br>• ")}</div>`;
  if ((j.action_plan || []).length)
    h += `<h3 style="margin:14px 0 4px">Action plan</h3>` + j.action_plan.map(p =>
      `<div class="rec" style="border-left-color:#7fb3ff"><h4>${esc(p.phase)} — ${esc(p.goal)}</h4>
       <div class="why">• ${p.steps.map(esc).join("<br>• ")}</div>
       <div class="muted">${p.kb_ids.map(k => `<span class="badge kb" data-kb="${esc(k)}">📖 ${esc(k)}</span>`).join(" ")}</div></div>`).join("");
  if ((j.targets || []).length)
    h += `<div class="diag"><b>Measurable targets:</b><br>• ${j.targets.map(t =>
      `${esc(t.metric)} → ${esc(t.expected)} <span class="muted">(${esc(t.by)}-term, via ${esc(t.via)})</span>`).join("<br>• ")}</div>`;
  if ((j.measure_next || []).length)
    h += `<div class="trade"><b>Measure next (biggest confidence gains):</b><br>• ${j.measure_next.map(m =>
      `<b>${esc(m.measure)}</b> — ${esc(m.why)}`).join("<br>• ")}</div>`;
  if (j.enrichment)
    h += `<div class="muted">Enriched via ${esc(j.enrichment.enriched_from)}: ${esc((j.enrichment.applied || []).join(", ") || "nothing new")} (90-day observed ${esc(j.enrichment.precip_90d_mm)} mm, mean ${esc(j.enrichment.tmean_90d_c)}°C)</div>`;
  (j.recommendations || []).forEach((r, i) => {
    const pct = Math.round((r.confidence_score || 0) * 100);
    h += `<div class="rec"><h4>${i + 1}. ${esc(r.recommendation)}</h4>
      <div class="why"><b>Why it works:</b> ${esc(r.why_it_works)}</div>
      <div class="badges">${(r.metrics_improved || []).map(m => `<span class="badge">${esc(m)}</span>`).join("")}
        <span class="badge time">${esc(r.time_horizon)}-term</span>
        <span class="badge kb" data-kb="${esc(r.kb_id)}" title="view evidence">📖 ${esc(r.kb_id)}</span></div>
      <div class="why"><b>Expected:</b> ${esc(r.expected_effect)}</div>
      <div class="src">Ref: ${esc(r.reference)}</div>
      <div class="muted">Confidence: ${esc(r.confidence)} (${pct}%) · retrieval score ${esc(r.retrieval_score)}</div>
      ${(r.matched_terms || []).length ? `<div class="muted">Matched on: ${(r.matched_terms || []).map(m => `<kbd>${esc(m)}</kbd>`).join(" ")}</div>` : ""}
      <div class="confbar"><i style="width:${pct}%"></i></div></div>`;
  });
  if ((j.tradeoffs || []).length)
    h += `<div class="trade"><b>Trade-offs:</b><br>• ${j.tradeoffs.map(esc).join("<br>• ")}</div>`;
  if (j.summary) h += `<div class="diag"><b>Summary (${esc(j.summary_mode)}):</b> ${esc(j.summary)}</div>`;
  const prov = (j.provenance || []).map(p => `${esc(p.kb_id)} (${esc(p.score)})`).join(", ");
  if (prov) h += `<div class="muted">Provenance: ${prov} · <a href="#" onclick="showProvenance([${(j.provenance || []).map(p => `'${p.kb_id}'`).join(",")}]);return false;">view evidence</a></div>`;
  return h;
}
document.addEventListener("click", (e) => {
  const b = e.target.closest("[data-kb]");
  if (b) showProvenance([b.dataset.kb]);
});

/* ---------- markdown export ---------- */
function downloadReport() {
  const j = window._lastReport; if (!j) return;
  let md = `# Darukaa.Earth Biodiversity Report\n\n## Diagnosis (${j.variables_count} variables)\n` +
    (j.diagnosis_interactions || []).map(d => `- ${d}`).join("\n") + "\n";
  (j.action_plan || []).forEach(p => { md += `\n## ${p.phase}: ${p.goal}\n` + p.steps.map(s => `- [ ] ${s}`).join("\n") + "\n"; });
  md += "\n## Recommendations\n";
  (j.recommendations || []).forEach((r, i) => {
    md += `\n### ${i + 1}. ${r.recommendation}\n- Why: ${r.why_it_works}\n- Metrics: ${r.metrics_improved.join(", ")}\n- Expected: ${r.expected_effect}\n- Time: ${r.time_horizon} | Confidence: ${r.confidence} (${r.confidence_score})\n- Ref: ${r.reference} [${r.kb_id}]\n`;
  });
  if ((j.tradeoffs || []).length) md += "\n## Trade-offs\n" + j.tradeoffs.map(t => `- ${t}`).join("\n") + "\n";
  md += "\n## Provenance\n" + (j.provenance || []).map(p => `- ${p.kb_id} (${p.score}): ${p.title}`).join("\n") + "\n";
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([md], { type: "text/markdown" }));
  a.download = "darukaa-report.md"; a.click(); URL.revokeObjectURL(a.href);
}

/* ---------- chat ---------- */
function bubble(who, text) {
  const t = $("thread");
  const d = document.createElement("div");
  d.className = "bub " + who; d.textContent = text;
  t.appendChild(d); t.scrollTop = t.scrollHeight;
  return d;
}
async function sendChat() {
  const msg = $("msg").value.trim(); if (!msg) return;
  const btn = $("sendBtn"); btn.disabled = true;
  bubble("user", msg); $("msg").value = "";
  const wait = bubble("sys", "reasoning…");
  try {
    const j = await api("/chat", { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: $("sid").value || "demo", message: msg }) });
    wait.remove();
    const d = document.createElement("div"); d.className = "bub ai";
    if (j.done) d.innerHTML = reportHTML(j);
    else d.innerHTML = `<b>Need a bit more:</b><br>${esc(j.reply)}`;
    $("thread").appendChild(d); $("thread").scrollTop = $("thread").scrollHeight;
  } catch (e) { wait.textContent = "Error: " + e.message; }
  btn.disabled = false;
}
function demoChat() {
  $("sid").value = "demo1";
  $("msg").value = "SOC 0.3%, low rainfall 450mm, monoculture wheat, semi-arid";
  sendChat();
}

/* ---------- assess form ---------- */
function formSite() {
  const v = (id) => { const x = $(id).value.trim(); return x === "" ? null : x; };
  const f = (id) => { const x = $(id).value.trim(); return x === "" ? null : parseFloat(x); };
  const site = { soc_pct: f("f_soc"), soil_ph: f("f_ph"), soil_moisture: v("f_moist"),
    land_use: v("f_land"), crop: v("f_crop"), rainfall: v("f_rain"), rainfall_mm: f("f_mm"),
    temperature_c: f("f_temp"), region: v("f_region"), pollution: v("f_poll"),
    pesticide_use: $("f_pest").checked || null, deforestation: $("f_def").checked || null,
    burning: $("f_burn").checked || null };
  const lat = f("f_lat"), lon = f("f_lon");
  if (lat !== null && lon !== null) site.geo = [lat, lon];
  Object.keys(site).forEach(k => site[k] === null && delete site[k]);
  return site;
}
async function runAssess() {
  const out = $("assessOut"), btn = $("assessBtn"); btn.disabled = true;
  out.innerHTML = "<p class='muted'><span class='spin'></span> retrieving evidence + reasoning…</p>";
  try {
    const j = await api("/assess", { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ site: formSite(), query: $("f_q").value, enrich: $("f_enrich").checked }) });
    out.innerHTML = reportHTML(j);
  } catch (e) { out.innerHTML = `<p>Error: ${esc(e.message)}</p>`; }
  btn.disabled = false;
}
function demoAssess() {
  $("f_soc").value = "0.3"; $("f_mm").value = "450"; $("f_rain").value = "low";
  $("f_land").value = "monoculture"; $("f_crop").value = "wheat"; $("f_region").value = "semi-arid";
  runAssess();
}

/* ---------- knowledge explorer ---------- */
async function kbSearch() {
  const q = $("kb_q").value.trim(); if (!q) return;
  const out = $("kbOut"); out.innerHTML = "<p class='muted'><span class='spin'></span> searching…</p>";
  try {
    const j = await api("/knowledge/search?q=" + encodeURIComponent(q) + "&region=" + encodeURIComponent($("kb_region").value) + "&top_k=6");
    out.innerHTML = `<p class="muted">Backend: ${esc(j.backend)} · top ${j.hits.length} for “${esc(j.query)}”</p>` +
      j.hits.map(h => `<div class="rec"><h4>${esc(h.kb_id)} · ${esc(h.title)} <span class="muted">(score ${esc(h.score)})</span></h4>
        <div class="why">${esc(h.intervention)}</div>
        ${(h.matched_terms || []).length ? `<div class="muted">Matched on: ${h.matched_terms.map(m => `<kbd>${esc(m)}</kbd>`).join(" ")}</div>` : ""}
        <div class="badges"><span class="badge">${esc(h.confidence)}</span><span class="badge time">${esc(h.time_horizon)}</span>
        ${(h.metrics_improved || []).map(m => `<span class="badge">${esc(m)}</span>`).join("")}
        <span class="badge kb" data-kb="${esc(h.kb_id)}">📖 evidence</span></div>
        <div class="src">${esc(h.source)}</div></div>`).join("");
  } catch (e) { out.innerHTML = `<p>Error: ${esc(e.message)}</p>`; }
}

window.addEventListener("DOMContentLoaded", () => {
  loadStatus();
  $("msg").addEventListener("keydown", (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendChat(); } });
  bubble("ai", "Welcome — I reason like an environmental scientist: every recommendation cites evidence. Try the demo, or tell me about your land (SOC %, rainfall, land use).");
  // shareable deep links: ?tab=chat|assess|kb &demo=1 &q=...
  const p = new URLSearchParams(location.search);
  if (p.get("tab")) tab(p.get("tab"));
  if (p.get("q")) $("kb_q").value = p.get("q");
  if (p.get("demo") === "1") {
    const t = p.get("tab") || "chat";
    if (t === "assess") demoAssess();
    else if (t === "kb") kbSearch();
    else demoChat();
  }
});
