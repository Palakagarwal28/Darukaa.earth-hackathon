"""Integration tests: climate enrichment + LLM verbalizer (mocked, offline-safe)."""
import src.integrations as I
from src.reasoner import assess
from fastapi.testclient import TestClient
from api.main import app

c = TestClient(app)

class _Resp:
    def __init__(self, payload, ok=True):
        self._p = payload; self.ok = ok; self.status_code = 200 if ok else 500
    def raise_for_status(self):
        if not self.ok: raise Exception("http err")
    def json(self): return self._p

def test_climate_enrich_fills_temp(monkeypatch):
    def fake_get(url, params=None, timeout=None):
        return _Resp({"daily": {"precipitation_sum": [1.0] * 90,
                                "temperature_2m_mean": [28.0] * 90}})
    monkeypatch.setattr(I.httpx, "get", fake_get)
    I._cache.clear()
    site, env = I.apply_climate_enrichment({"geo": [13.0, 77.5]})
    assert site["temperature_c"] == 28.0 and env["enriched_from"] == "open-meteo"

def test_climate_failure_is_none(monkeypatch):
    def boom(*a, **k): raise ConnectionError("offline")
    monkeypatch.setattr(I.httpx, "get", boom)
    I._cache.clear()
    assert I.enrich_climate(13.0, 77.5) is None
    site, env = I.apply_climate_enrichment({"geo": [13.0, 77.5]})
    assert env is None and "temperature_c" not in site

def test_user_data_wins_no_api_call(monkeypatch):
    def boom(*a, **k): raise AssertionError("should not call API")
    monkeypatch.setattr(I.httpx, "get", boom)
    site, env = I.apply_climate_enrichment(
        {"geo": [13.0, 77.5], "temperature_c": 30.0, "rainfall": "low"})
    assert env is None and site["temperature_c"] == 30.0

def test_llm_disabled_without_key(monkeypatch):
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    assert I.verbalize({"recommendations": []}) is None
    assert I.llm_configured() is False

def test_assess_enrich_off_no_network(monkeypatch):
    def boom(*a, **k): raise AssertionError("network must not be touched")
    monkeypatch.setattr(I.httpx, "get", boom)
    r = assess({"soc_pct": 0.3, "rainfall": "low", "land_use": "monoculture",
                "geo": [13.0, 77.5]}, "test", enrich=False)
    assert r["enrichment"] is None and r["summary_mode"] == "deterministic"

def test_status_endpoint():
    r = c.get("/integrations/status")
    assert r.status_code == 200
    j = r.json()
    assert "open_meteo" in j and "llm_configured" in j and "kb_cards" in j
