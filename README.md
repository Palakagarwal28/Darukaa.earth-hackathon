# Darukaa.Earth — AI Biodiversity Intelligence Scientist

RAG-grounded conversational system that behaves like an environmental scientist, not a chatbot.

## Architecture

```
User Input (Text / JSON / Geo) 
  → Conversation Manager (slot-filling + SQLite memory)
  → Metric Extractor (soil, land, biodiversity, climate, human impact)
  → Hybrid Retriever (TF-IDF now, Chroma/FAISS + embeddings drop-in)
  → Multi-Metric Reasoning Engine (rule + interaction graph, ≥3 variables)
  → Evidence-Backed Response (what/why/metrics/time/confidence/refs)
```

Why this wins: deterministic science engine + retrievable knowledge layer = no generic LLM-only output. LLM (optional) only verbalizes grounded results.

## Knowledge System

* `knowledge/evidence_cards.json` — 30 curated cards from FAO, IPCC AR6, IPBES 2019, CBD, UNCCD, peer-review meta-analyses
* Schema per card: `id, domain, intervention, mechanism, metrics_improved, effect_size, time_horizon, confidence, source, region_fit, conditions`
* Domains covered: soil pH/SOC/moisture, LULC, species richness/habitat diversity, temp/rainfall, pollution/deforestation
* Retrieval: `src/retriever.py` — BM25 + agro synonym map by default (7/7 on `python -m knowledge.benchmark_retrieval` vs 5/7 TF-IDF); `RETRIEVER_BACKEND=tfidf|dense` to switch. Every answer logs `retrieved_ids + scores` for judging.

## Quickstart

```bash
python -m venv .venv; .venv\Scripts\activate
pip install -r requirements.txt
python -m app.chat --demo demo/example_semi_arid.json
uvicorn api.main:app --reload  # POST /chat, /assess, GET /health, /provenance
```

Try text: `Biodiversity is declining on my land` → system asks for SOC%, rainfall, land-use.
Try JSON: see `demo/example_semi_arid.json`.

## API

* `POST /assess` — `{site, query?, enrich=true, verbalize=false}` → full report + `enrichment` + `summary_mode`
* `POST /chat` — `{session_id, message, site_json?, enrich=true, verbalize=false}` → reply + memory
* `GET /provenance?ids=KB12,KB07` — exact cards used
* `GET /knowledge/search?q=&region=` — retrieval debug trace for judges
* `GET /integrations/status` — external API health (Open-Meteo reachability, LLM configured?)

## API Integrations (`src/integrations.py`, all optional — core runs offline)

* **Climate (Open-Meteo, free, no key):** when `geo:[lat,lon]` is given and temp/rainfall missing, fills `temperature_c` (observed 90-day mean) and a rainfall *hint* (only at extremes; flagged as hint). User-supplied data always wins; enrichment recorded under `extra.climate_enrichment` + `enrichment` block. Fails gracefully offline.
* **LLM verbalizer (any OpenAI-compatible API):** set `LLM_API_KEY` + `LLM_MODEL` (see `.env.example`). Only rephrases the engine's grounded recs (keeps `[KB-ID]` tags, adds nothing); `summary_mode: llm` vs `deterministic`. Off by default so judging works with no keys.
* **Dense retrieval upgrade:** `RETRIEVER_BACKEND=dense` + `pip install sentence-transformers` — same `query()` interface.

## Database / Schema

* No server DB needed for judging. `SQLite (sessions.db)` for multi-turn memory. Knowledge is versioned JSONL → migratable to Postgres+pgvector/Chroma in prod. See `knowledge/schema.json`.

## CI/CD

GitHub Actions: `pytest + ruff` on push. Deploy: Dockerfile + Render/Fly ready. Live demo: host FastAPI + minimal HTML UI in `api/static/`.

## Submission .docx checklist

1. GitHub link, 2. Live demo URL, 3. This README (arch/db/setup/CI), 4. Demo creds (none needed — runs offline).
