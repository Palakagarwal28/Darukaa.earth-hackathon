from fastapi.testclient import TestClient
from api.main import app

c = TestClient(app)

def test_health():
    r = c.get("/health")
    assert r.status_code == 200 and r.json()["kb_cards"] >= 10

def test_assess_semi_arid():
    r = c.post("/assess", json={"site": {"soc_pct": 0.3, "rainfall": "low",
        "rainfall_mm": 450, "land_use": "monoculture", "crop": "wheat", "region": "semi-arid"},
        "query": "declining biodiversity"})
    assert r.status_code == 200
    j = r.json()
    assert j["variables_count"] >= 3 and len(j["recommendations"]) >= 3
    for rec in j["recommendations"]:
        for k in ("recommendation", "why_it_works", "metrics_improved",
                  "time_horizon", "confidence", "confidence_score", "reference", "kb_id"):
            assert rec[k], k

def test_chat_clarify_and_memory():
    import uuid
    sid = f"t1-{uuid.uuid4().hex[:8]}"  # fresh session each run (memory persists in SQLite)
    r = c.post("/chat", json={"session_id": sid, "message": "Biodiversity is declining on my land"})
    assert r.status_code == 200 and r.json()["done"] is False  # asks clarifying Qs
    r = c.post("/chat", json={"session_id": sid,
        "message": "SOC 0.3%, low rainfall, monoculture wheat semi-arid"})
    assert r.json()["done"] is True and "KB" in r.json()["reply"]

def test_geo_inference():
    r = c.post("/assess", json={"site": {"soc_pct": 0.4, "rainfall": "low",
        "land_use": "grassland", "geo": [13.0, 77.5]}, "query": "degraded"})
    assert r.json()["variables_used"]["region"] == "semi-arid"

def test_provenance():
    assert c.get("/provenance?ids=KB01,KB04").status_code == 200

def test_judge_features():
    r = c.post("/assess", json={"site": {"soc_pct": 0.3, "rainfall": "low",
        "land_use": "monoculture", "crop": "wheat", "region": "semi-arid"},
        "query": "declining biodiversity", "enrich": False})
    j = r.json()
    assert len(j["action_plan"]) >= 2  # phased Now/Season/Years
    assert len(j["targets"]) >= 4 and all("metric" in t and "expected" in t for t in j["targets"])
    assert len(j["measure_next"]) >= 1  # value-of-information
    assert all(j["recommendations"][0]["matched_terms"])  # explainable retrieval
    assert all("matched_terms" in p for p in j["provenance"])
