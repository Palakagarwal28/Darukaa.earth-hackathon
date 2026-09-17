"""External API integrations — all optional, offline-safe, provenance-tracked.

1. Climate (Open-Meteo, free, no key): enriches geo sites with observed temp +
   recent precipitation. Never silently overrides user data; everything is flagged.
2. LLM verbalizer (any OpenAI-compatible endpoint via env): rephrases the
   deterministic engine's grounded output only. Never invents recommendations.
   Disabled by default (no key = pure deterministic mode for judges).
"""
import os, time
import httpx

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
_cache: dict = {}
CACHE_TTL = 3600

def _cache_get(key):
    hit = _cache.get(key)
    if hit and time.time() - hit[1] < CACHE_TTL:
        return hit[0]
    return None

def _cache_set(key, val):
    _cache[key] = (val, time.time())

def enrich_climate(lat: float, lon: float, timeout: float = 8.0) -> dict | None:
    """Return observed climate enrichment or None (offline/failure-safe)."""
    key = f"{round(lat, 2)},{round(lon, 2)}"
    hit = _cache_get(key)
    if hit is not None:
        return hit
    try:
        r = httpx.get(OPEN_METEO_URL, params={
            "latitude": lat, "longitude": lon,
            "daily": "precipitation_sum,temperature_2m_mean",
            "past_days": 90, "forecast_days": 1,
            "timezone": "auto",
        }, timeout=timeout)
        r.raise_for_status()
        daily = r.json().get("daily", {})
        prec = [p or 0 for p in daily.get("precipitation_sum", [])]
        temps = [t for t in daily.get("temperature_2m_mean", []) if t is not None]
        if not prec:
            return None
        total_90 = round(sum(prec), 1)
        tmean = round(sum(temps) / len(temps), 1) if temps else None
        # 90-day window is season-dependent: only infer annual class at extremes,
        # otherwise report observed and let the user confirm.
        annual_hint = None
        if total_90 < 100:
            annual_hint = "low"
        elif total_90 > 600:
            annual_hint = "high"
        out = {"source": "open-meteo", "precip_90d_mm": total_90,
               "tmean_90d_c": tmean, "annual_rainfall_hint": annual_hint,
               "note": "90-day observed window; annual class is a hint, confirm locally"}
        _cache_set(key, out)
        return out
    except Exception:
        return None  # offline or API down: caller proceeds without enrichment

def apply_climate_enrichment(site: dict, timeout: float = 8.0) -> tuple[dict, dict | None]:
    """Fill missing temperature_c / rainfall from geo enrichment. Returns (site, enrichment)."""
    site = dict(site)
    g = site.get("geo")
    if not (isinstance(g, (list, tuple)) and len(g) == 2):
        return site, None
    if site.get("temperature_c") is not None and site.get("rainfall") not in (None, ""):
        return site, None  # user data wins; no call needed
    try:
        env = enrich_climate(float(g[0]), float(g[1]), timeout=timeout)
    except Exception:
        return site, None
    if not env:
        return site, None
    applied = []
    if site.get("temperature_c") is None and env.get("tmean_90d_c") is not None:
        site["temperature_c"] = env["tmean_90d_c"]; applied.append("temperature_c")
    if site.get("rainfall") in (None, "") and env.get("annual_rainfall_hint"):
        site["rainfall"] = env["annual_rainfall_hint"]; applied.append("rainfall(hint)")
    enrichment = {**env, "applied": applied, "enriched_from": "open-meteo"}
    extra = dict(site.get("extra") or {}); extra["climate_enrichment"] = enrichment
    site["extra"] = extra
    return site, enrichment

# ---- LLM verbalizer (grounded rephrase only) ----

def llm_configured() -> bool:
    return bool(os.getenv("LLM_API_KEY") and os.getenv("LLM_MODEL"))

def verbalize(report: dict, timeout: float = 20.0) -> str | None:
    """Rephrase grounded report in friendly tone. Returns None if unconfigured/failing."""
    if not llm_configured():
        return None
    url = os.getenv("LLM_API_URL", "https://api.openai.com/v1/chat/completions")
    model = os.getenv("LLM_MODEL", "")
    recs = "\n".join(f"- {r['recommendation']} [{r['kb_id']}] ({r['reference']})"
                      for r in report.get("recommendations", []))
    diag = "; ".join(report.get("diagnosis_interactions", []))
    prompt = (f"Diagnosis: {diag}\nGrounded recommendations:\n{recs}\n\n"
              "Rewrite as a concise farmer-friendly summary (<=150 words). "
              "Rules: mention every recommendation, keep each [KB-ID] tag, "
              "do NOT add new advice, do NOT invent numbers.")
    try:
        r = httpx.post(url,
            headers={"Authorization": f"Bearer {os.environ['LLM_API_KEY']}"},
            json={"model": model, "temperature": 0.2, "max_tokens": 300,
                  "messages": [{"role": "system", "content": "You are a science-grounded agriculture explainer."},
                               {"role": "user", "content": prompt}]},
            timeout=timeout)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception:
        return None

def integrations_status(timeout: float = 6.0) -> dict:
    meteo = "unknown"
    try:
        r = httpx.get(OPEN_METEO_URL, params={"latitude": 13, "longitude": 77,
                      "daily": "temperature_2m_mean", "past_days": 1, "forecast_days": 1},
                      timeout=timeout)
        meteo = "reachable" if r.status_code == 200 else f"http-{r.status_code}"
    except Exception as e:
        meteo = f"unreachable ({type(e).__name__})"
    return {"open_meteo": meteo,
            "llm_configured": llm_configured(),
            "llm_model": os.getenv("LLM_MODEL", "") or None,
            "note": "All integrations optional; core engine runs fully offline."}
