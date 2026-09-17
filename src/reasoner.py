"""Multi-metric reasoning engine v2: interaction graph, confidence scoring, trade-offs,
external climate enrichment (geo → Open-Meteo, flagged, never overrides user data)."""
from src.retriever import get_retriever
from src.geo import apply_geo
from src.integrations import apply_climate_enrichment, verbalize as llm_verbalize

REQUIRED_SLOTS = ["soc_pct", "rainfall", "land_use"]
CONF_W = {"high": 0.85, "medium": 0.65, "low": 0.45}

def missing_slots(site: dict):
    # rainfall satisfied by rainfall OR rainfall_mm
    miss = []
    if site.get("soc_pct") in (None, ""): miss.append("soc_pct")
    if site.get("rainfall") in (None, "") and site.get("rainfall_mm") in (None, ""): miss.append("rainfall")
    if site.get("land_use") in (None, ""): miss.append("land_use")
    return miss

def diagnose(site: dict):
    d = []
    soc = site.get("soc_pct"); rain = str(site.get("rainfall", "")).lower()
    mm = site.get("rainfall_mm"); lu = str(site.get("land_use", "")).lower()
    ph = site.get("soil_ph"); crop = str(site.get("crop", "")).lower()
    low_water = "low" in rain or (isinstance(mm, (int, float)) and mm < 600)
    if isinstance(soc, (int, float)) and soc < 0.5:
        d.append("critically low SOC (<0.5%): weak microbial base + poor water holding — amplifies drought")
    elif isinstance(soc, (int, float)) and soc < 1.0:
        d.append("low SOC (0.5–1.0%): carbon-limited microbes, fragile aggregates")
    if low_water:
        d.append("water-limited regime: seedling mortality + pollinator forage gaps in dry months")
    if "monoculture" in lu or "wheat" in crop or "monoculture" in crop:
        d.append("monoculture/fragmentation: no refugia → pest release + pollinator deficit (IPBES)")
    if isinstance(ph, (int, float)) and (ph < 5.5 or ph > 8.2):
        d.append(f"pH {ph} locks P/micronutrients: fertilizing before correcting wastes input")
    if site.get("burning"):
        d.append("residue burning: oxidizes SOC + kills surface fauna (IPCC: switch to biochar/compost)")
    if site.get("pesticide_use") or "pesticid" in str(site.get("pollution", "")).lower():
        d.append("pesticide pressure: non-target mortality suppresses natural pest control")
    if site.get("deforestation"):
        d.append("tree loss: breaks connectivity + removes microclimate buffering")
    return d or ["general diversity decline — multi-metric workup needed"]

def _confidence(card: dict, site: dict) -> float:
    base = CONF_W.get(card.get("confidence", "medium"), 0.6)
    region = str(site.get("region", "")).lower()
    fits = [r.lower() for r in card.get("region_fit", ["all"])]
    if "all" in fits or (region and region in fits): base += 0.05
    else: base -= 0.1
    completeness = sum(1 for k in ("soc_pct", "rainfall", "land_use", "region", "soil_ph") if site.get(k) not in (None, "")) / 5
    base += (completeness - 0.6) * 0.1
    return round(max(0.3, min(0.95, base)), 2)

def build_recommendations(site: dict, retrieved: list, top_n: int = 4):
    recs = []
    for c in retrieved:
        recs.append({
            "recommendation": c["intervention"],
            "why_it_works": c["mechanism"],
            "metrics_improved": c["metrics_improved"],
            "expected_effect": c["effect_size"],
            "time_horizon": c["time_horizon"],
            "confidence": c["confidence"],
            "confidence_score": _confidence(c, site),
            "reference": c["source"],
            "kb_id": c["id"],
            "retrieval_score": c["retrieval_score"],
            "matched_terms": c.get("matched_terms", []),
        })
    recs.sort(key=lambda r: (r["confidence_score"], r["retrieval_score"]), reverse=True)
    return recs[:top_n]

def tradeoffs(site: dict):
    t = []
    if str(site.get("land_use", "")).lower().startswith("monoculture") and site.get("rainfall") == "low":
        t.append("Trees compete for water in year 1 — use 10-20/ha parkland spacing + mulch, not dense block planting.")
    if site.get("burning") is None and isinstance(site.get("soc_pct"), (int, float)) and site["soc_pct"] < 0.5:
        t.append("Biochar without compost can immobilize N short-term — always co-apply compost/manure.")
    return t

VARS = ["soc_pct", "soil_ph", "soil_moisture", "rainfall", "rainfall_mm",
        "land_use", "crop", "region", "temperature_c", "pollution",
        "pesticide_use", "deforestation", "burning", "geo"]

PH_FIRST = {"KB06", "KB16"}
WATER_EARLY = {"KB04", "KB17", "KB28"}

def _phase_order(recs):
    """Sequencing logic: fix chemistry first, secure water early, build biology over seasons."""
    def key(r):
        seq = 0 if r["kb_id"] in PH_FIRST else (1 if r["kb_id"] in WATER_EARLY else 2)
        return (seq, -r["confidence_score"])
    return sorted(recs, key=key)

def action_plan(recommendations):
    short = _phase_order([r for r in recommendations if r["time_horizon"] == "short"])
    med = _phase_order([r for r in recommendations if r["time_horizon"] == "medium"])
    long = _phase_order([r for r in recommendations if r["time_horizon"] == "long"])
    phases = []
    if short:
        phases.append({"phase": "Now (0-30 days)",
                       "goal": "Stop the bleeding: water, chemistry, quick habitat",
                       "steps": [s["recommendation"] for s in short],
                       "kb_ids": [s["kb_id"] for s in short]})
    if med:
        phases.append({"phase": "This season (1-6 months)",
                       "goal": "Rebuild the engine: carbon, microbes, corridors",
                       "steps": [s["recommendation"] for s in med],
                       "kb_ids": [s["kb_id"] for s in med]})
    if long:
        phases.append({"phase": "Year 1-3",
                       "goal": "Lock in resilience: trees, structure, income diversity",
                       "steps": [s["recommendation"] for s in long],
                       "kb_ids": [s["kb_id"] for s in long]})
    return phases

def targets(recommendations):
    seen, out = set(), []
    for r in recommendations:
        for m in r["metrics_improved"]:
            if m not in seen:
                seen.add(m)
                out.append({"metric": m, "expected": r["expected_effect"],
                            "by": r["time_horizon"], "via": r["kb_id"]})
    return out

MEASURE_WHY = {
    "soil_ph": "pH decides whether any fertilizer works — wrong pH wastes every rupee of input",
    "soc_pct": "SOC below 0.5% changes the whole strategy (rescue mode vs build mode)",
    "rainfall_mm": "Annual mm separates 'store water' from 'drain water' strategies",
    "temperature_c": "Heat above 32C triggers phenology + shade measures",
    "soil_moisture": "Moisture regime picks drip vs bunds vs drainage",
    "pesticide_use": "Spray history decides whether predators can recover in one season",
    "deforestation": "Tree loss flips the plan toward corridors + ANR",
}

def measure_next(site):
    out = []
    for k, why in MEASURE_WHY.items():
        if site.get(k) in (None, ""):
            out.append({"measure": k, "why": why})
    return out[:3]

def assess(site: dict, query_text: str = "", top_n: int = 4,
           enrich: bool = True, verbalize: bool = False):
    site = apply_geo(dict(site))
    enrichment = None
    if enrich:
        site, enrichment = apply_climate_enrichment(site)
    if site.get("rainfall_mm") is not None and not site.get("rainfall"):
        mm = site["rainfall_mm"]
        site["rainfall"] = "low" if mm < 600 else ("medium" if mm < 1000 else "high")
    ret = get_retriever()
    q = query_text or f"{site.get('crop','')} {site.get('land_use','')} {site.get('region','')} biodiversity decline"
    retrieved = ret.query(q, site, top_k=max(4, top_n))
    recs = build_recommendations(site, retrieved, top_n)
    result = {
        "diagnosis_interactions": diagnose(site),
        "variables_used": {k: site.get(k) for k in VARS},
        "variables_count": sum(1 for k in VARS if site.get(k) not in (None, "")),
        "recommendations": recs,
        "action_plan": action_plan(recs),
        "targets": targets(recs),
        "measure_next": measure_next(site),
        "tradeoffs": tradeoffs(site),
        "provenance": [{"kb_id": c["id"], "title": c["title"], "score": c["retrieval_score"],
                        "matched_terms": c.get("matched_terms", [])} for c in retrieved[:top_n]],
        "retriever_backend": ret.backend,
        "enrichment": enrichment,
    }
    summary = llm_verbalize(result) if verbalize else None
    result["summary"] = summary
    result["summary_mode"] = "llm" if summary else "deterministic"
    return result
