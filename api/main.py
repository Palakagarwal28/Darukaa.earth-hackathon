"""Darukaa.Earth Biodiversity Intelligence API — hackathon backend."""
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from src.schemas import ChatIn, AssessIn
from src.conversation import chat, history
from src.reasoner import assess
from src.retriever import get_retriever, load_cards
from src.integrations import integrations_status

log = logging.getLogger("darukaa")
app = FastAPI(title="Darukaa.Earth Biodiversity Intelligence",
              description="RAG-grounded AI environmental scientist. Every recommendation carries evidence + provenance.",
              version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/health")
def health():
    r = get_retriever()
    return {"ok": True, "kb_cards": len(r.cards), "retriever_backend": r.backend}

@app.get("/knowledge/search")
def knowledge_search(q: str, top_k: int = 4, region: str = ""):
    """Debug endpoint for judges: shows exactly how knowledge is retrieved and scored."""
    r = get_retriever()
    hits = r.query(q, {"region": region}, top_k=top_k)
    return {"query": q, "backend": r.backend,
            "hits": [{"kb_id": h["id"], "title": h["title"], "score": h["retrieval_score"],
                      "matched_terms": h.get("matched_terms", []),
                      "source": h["source"], "region_fit": h.get("region_fit"),
                      "domain": h.get("domain"), "intervention": h.get("intervention"),
                      "mechanism": h.get("mechanism"), "effect_size": h.get("effect_size"),
                      "metrics_improved": h.get("metrics_improved", []),
                      "time_horizon": h.get("time_horizon"), "confidence": h.get("confidence")} for h in hits]}

@app.get("/provenance")
def provenance(ids: str):
    want = {i.strip() for i in ids.split(",") if i.strip()}
    if not want: raise HTTPException(400, "pass ?ids=KB01,KB04")
    return [c for c in load_cards() if c["id"] in want]

@app.post("/assess")
def assess_route(inp: AssessIn):
    """Structured JSON in → full scientific report. Must combine ≥3 variables."""
    try:
        return assess(inp.site.to_dict(), inp.query, enrich=inp.enrich, verbalize=inp.verbalize)
    except Exception as e:
        log.exception("assess failed"); raise HTTPException(500, str(e))

@app.post("/chat")
def chat_route(inp: ChatIn):
    """Text (+optional JSON + geo) with multi-turn memory. Asks clarifying Qs if incomplete."""
    try:
        site = inp.site_json.to_dict() if inp.site_json else None
        return chat(inp.session_id, inp.message, site, enrich=inp.enrich, verbalize=inp.verbalize)
    except Exception as e:
        log.exception("chat failed"); raise HTTPException(500, str(e))

@app.get("/integrations/status")
def integrations_status_route():
    """Show which external APIs are live. Core engine works even if all are down."""
    r = get_retriever()
    return {"kb_cards": len(r.cards), "retriever_backend": r.backend, **integrations_status()}

@app.get("/sessions/{sid}")
def session_history(sid: str, n: int = 10):
    return {"session_id": sid, "turns": history(sid, n)}

app.mount("/", StaticFiles(directory="api/static", html=True), name="static")
