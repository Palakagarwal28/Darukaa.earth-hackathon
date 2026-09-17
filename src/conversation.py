"""Conversation manager: extraction (text+JSON+geo), slot-filling, SQLite memory."""
import json, re, sqlite3, pathlib, time
from src.reasoner import assess, missing_slots
from src.geo import apply_geo

DB = pathlib.Path(__file__).resolve().parents[1] / "sessions.db"

def _db():
    con = sqlite3.connect(DB)
    con.execute("""CREATE TABLE IF NOT EXISTS turns
        (sid TEXT, role TEXT, text TEXT, site TEXT, ts REAL)""")
    return con

def save(sid, role, text, site):
    con = _db()
    con.execute("INSERT INTO turns VALUES (?,?,?,?,?)",
                (sid, role, text, json.dumps(site or {}), time.time()))
    con.commit(); con.close()

def history(sid, n=10):
    con = _db()
    rows = con.execute("SELECT role, text FROM turns WHERE sid=? ORDER BY ts DESC LIMIT ?",
                       (sid, n)).fetchall()
    con.close()
    return list(reversed(rows))

def last_site(sid) -> dict:
    con = _db()
    row = con.execute("SELECT site FROM turns WHERE sid=? ORDER BY ts DESC LIMIT 1", (sid,)).fetchone()
    con.close()
    if row:
        try: return json.loads(row[0])
        except Exception: return {}
    return {}

CLARIFY = {
    "soc_pct": "soil organic carbon % (e.g., 0.3% — below 0.5% is critical)",
    "rainfall": "rainfall pattern (low/medium/high or mm/year)",
    "land_use": "land use (e.g., monoculture wheat? grazed? fragmented? burning/pesticide?)",
}

def extract_metrics(text: str, site: dict) -> dict:
    site = dict(site or {})
    t = (text or "").lower()
    m = re.search(r"soc[^0-9]*(\d+\.?\d*)\s*%?", t)
    if m: site["soc_pct"] = float(m.group(1))
    m = re.search(r"(?:ph|p\.h)[^0-9]*(\d+\.?\d*)", t)
    if m and "phone" not in t: site["soil_ph"] = float(m.group(1))
    m = re.search(r"(\d{2,4})\s*mm", t)
    if m:
        site["rainfall_mm"] = float(m.group(1))
        site["rainfall"] = "low" if float(m.group(1)) < 600 else ("medium" if float(m.group(1)) < 1000 else "high")
    for w in ["low", "medium", "high"]:
        if re.search(rf"rain\w*\s*(is|:)?\s*{w}", t): site["rainfall"] = w
        if re.search(rf"\b{w}\s+rain\w*", t): site["rainfall"] = w
    if "monoculture" in t: site["land_use"] = "monoculture"
    if "wheat" in t: site["crop"] = "wheat"
    for r in ["semi-arid", "semi arid", "arid", "humid", "subhumid", "temperate", "tropical"]:
        if r in t: site["region"] = r.replace("semi arid", "semi-arid")
    if "burn" in t: site["burning"] = True
    if "pesticide" in t or "spray" in t: site["pesticide_use"] = True
    if "deforest" in t or "cut trees" in t or "tree loss" in t: site["deforestation"] = True
    m = re.search(r"(-?\d{1,2}\.\d+)\s*,\s*(-?\d{1,3}\.\d+)", text or "")
    if m: site["geo"] = [float(m.group(1)), float(m.group(2))]
    return apply_geo(site)

def format_report(result: dict) -> str:
    lines = [f"Diagnosis (multi-metric, {result['variables_count']} vars): " + "; ".join(result["diagnosis_interactions"])]
    if result.get("enrichment"):
        e = result["enrichment"]
        lines.append(f"[Enriched via {e.get('enriched_from')}: applied {', '.join(e.get('applied', [])) or 'nothing new'}]")
    for i, r in enumerate(result["recommendations"], 1):
        lines.append(
            f"\n{i}. WHAT: {r['recommendation']}\n   WHY: {r['why_it_works']}\n"
            f"   METRICS: {', '.join(r['metrics_improved'])} | EFFECT: {r['expected_effect']}\n"
            f"   TIME: {r['time_horizon']} | CONFIDENCE: {r['confidence']} ({r['confidence_score']}) | REF: {r['reference']} [{r['kb_id']}]")
    if result.get("tradeoffs"):
        lines.append("\nTrade-offs: " + " | ".join(result["tradeoffs"]))
    if result.get("summary"):
        lines.append("\nSummary: " + result["summary"])
    return "\n".join(lines)

def chat(sid: str, message: str, site_json: dict | None = None,
         enrich: bool = True, verbalize: bool = False):
    # merge: persisted memory <- explicit JSON <- newly extracted text
    site = last_site(sid)
    if site_json: site.update({k: v for k, v in site_json.items() if v is not None})
    site = extract_metrics(message, site)
    save(sid, "user", message, site)
    miss = missing_slots(site)
    if miss:
        q = "Can you provide " + "; ".join(CLARIFY[m] for m in miss) + "?"
        save(sid, "assistant", q, site)
        return {"reply": f"I need a bit more to reason scientifically. {q}",
                "need": miss, "site": site, "done": False,
                "history_turns": len(history(sid))}
    result = assess(site, message, enrich=enrich, verbalize=verbalize)
    reply = format_report(result)
    save(sid, "assistant", reply, site)
    return {"reply": reply, "need": [], "site": site, "done": True,
            "history_turns": len(history(sid)), **result}
