# Darukaa.Earth — AI Biodiversity Intelligence Scientist

A conversational system that behaves like an **AI environmental scientist, not a chatbot**:
multi-metric reasoning over soil · land · biodiversity · climate · human impact, with every
recommendation backed by retrievable evidence.

- **Live demo:** _(deploy URL goes here — see Deployment)_
- **API docs (local):** http://127.0.0.1:8000/docs
- **Tests:** 12/12 passing · **CI:** green · **Knowledge base:** 32 evidence cards

## Why this wins (mapped to judging criteria)

| Criterion (weight) | How we score |
|---|---|
| Depth of Reasoning 30% | Interaction diagnosis across ≥3 variables; sequenced action plan (chemistry first, water early, biology over seasons); trade-offs spelled out |
| Scientific Grounding 25% | 32 cards citing FAO / IPCC AR6 / IPBES / UNCCD / Ramsar / CBD + peer-reviewed meta-analyses; every claim carries `[KB-ID]` + full provenance |
| Knowledge System 20% | Real RAG pipeline (BM25 + agro synonyms, TF-IDF + dense options), scored retrieval with matched-term explanations, benchmarked 7/7 |
| Conversational Intelligence 15% | Slot-filling clarifying questions, SQLite multi-turn memory, text + JSON + geo input, value-of-information "measure next" |
| Output Clarity 10% | WHAT / WHY / metrics / effect / time / confidence / ref on every rec + phased checklist + one-click Markdown export |

## Architecture

```
Text / JSON / Geo ──▶ Conversation Manager (slot-fill + SQLite memory)
  ──▶ Metric Extractor (5 domains) ──▶ Geo inference + Open-Meteo enrichment (optional, flagged)
  ──▶ Hybrid Retriever (BM25 default | TF-IDF | dense) → kb_id + score + matched_terms
  ──▶ Multi-Metric Reasoning Engine (interaction graph, confidence, trade-offs)
  ──▶ Response: diagnosis + phased action plan + targets + recs + measure-next + provenance
       (optional LLM verbalizer rephrases grounded output only — never invents)
```

## Knowledge system

- `knowledge/evidence_cards.json` — **32 cards**, schema in `knowledge/schema.json`
- Per card: `id, title, domain, intervention, mechanism, metrics_improved, effect_size, time_horizon, confidence, source (+year, url, evidence_type), region_fit, conditions, tags, contraindications`
- **Coverage:** soil pH/SOC/moisture 12 · land use/cover 11 · biodiversity indicators 11 ·
  climate temp/rainfall 9 · human impact 9 · measurement protocols 2 (eDNA KB26, soil health card KB27) ·
  non-obvious differentiators: nesting-not-flowers KB29, dung beetles KB30, Lantana KB18, sodic KB16
- **Balance:** horizons short 14 / medium 11 / long 7 · confidence high 17 / medium 15 ·
  17/32 cards with source URL + year
- Tooling: `python -m knowledge.build_index` (validates + prints coverage + retrieval smoke test);
  `knowledge/SOURCES.md` (coverage map + pipeline notes)

## Evaluation

### Retrieval benchmark (`python -m knowledge.benchmark_retrieval` → `knowledge/retrieval_benchmark.md`)

7 queries (5 keyword + 2 adversarial farmer paraphrases), metric = expected card in top-2:

| # | Query | Expected | TF-IDF | BM25+syn |
|---|---|---|---|---|
| 1 | low SOC monoculture wheat semi-arid | KB01 | ✅ | ✅ |
| 2 | water scarcity farm, crops dying | KB04 | ✅ | ✅ |
| 3 | bees disappearing from fields | KB08/KB29 | ✅ | ✅ |
| 4 | salt-affected high pH soil | KB16/KB06 | ✅ | ✅ |
| 5 | stubble burning smoke | KB15 | ✅ | ✅ |
| 6 | *white crust on field, salty…* | KB16 | ❌ (KB05,KB28) | ✅ (KB16,KB06) |
| 7 | *field floods every monsoon…* | KB28 | ❌ (KB05,KB21) | ✅ (KB28,KB05) |
| **Score** | | | **5/7 (71%)** | **7/7 (100%)** |

**Error analysis (honest):** TF-IDF miss rate 28.6% → BM25 0% on this set — but it is a small
7-query set, and pure paraphrases with zero shared vocabulary ("urea overload", "goats ate
commons") still miss on *both* lexical backends. That residual gap is the documented case for
dense embeddings (`RETRIEVER_BACKEND=dense`, same interface) where deps/disk allow.

### Efficiency (measured on dev machine, 32-card KB)

| Operation | Median | p95 |
|---|---|---|
| TF-IDF retrieval (top-4) | 17.3 ms | 22.5 ms |
| BM25 retrieval (top-4) | 2.3 ms | 6.1 ms |
| `assess()` end-to-end (in-process) | 2.7 ms | 6.6 ms |
| `POST /assess` over HTTP (localhost) | 13.4 ms | — |
| Test suite (12 tests) | ~6–11 s | — |

Zero-cost-at-query design: no LLM calls in the critical path, no paid APIs, ~MB-scale memory.
Optional integrations (Open-Meteo ≈1 HTTP call cached 1h; LLM only when `verbalize=true`).

### Test suite

`python -m pytest tests -q` → **12 passed**: health/KB size, semi-arid reasoning (≥3 vars,
mandatory rec fields), chat clarify-then-answer memory, geo inference, provenance, climate
enrich success/failure/user-wins, LLM-off default, enrich-off makes zero network calls,
status shape, judge-feature fields (action plan, targets, measure-next, matched terms).

## Reasoning engine (`src/reasoner.py`)

- **Interaction diagnosis**, never single-variable (e.g. low SOC × drought × monoculture × pH × burning)
- **Confidence score** = evidence strength ± region fit + data completeness (0.3–0.95)
- **Sequencing:** pH cards first, water early, biology over seasons → `action_plan` (Now / This season / Year 1–3)
- **`targets`** (metric → expected effect → horizon → via which card) and **`tradeoffs`**
  (e.g. year-1 tree water competition, biochar N-lock without compost)
- **`measure_next`**: top-3 missing inputs ranked by decision impact — feeds clarifying questions

## Conversational intelligence (`src/conversation.py`)

- Vague input ("biodiversity is declining") → asks only for missing slots (SOC %, rainfall, land use)
- Merges SQLite session memory ← explicit JSON ← freshly extracted text (incl. `lat, lon` geo)
- Example: semi-arid wheat case yields 4 grounded recs with effects, horizons, confidence 0.72–0.92

## API integrations (`src/integrations.py` — all optional, offline-safe)

- **Climate (Open-Meteo, free, keyless):** fills `temperature_c` + rainfall *hint* (extremes only,
  labeled as 90-day-observation hint) when geo is present; user data always wins; everything flagged
  in `enrichment`/`extra`. Fails gracefully offline.
- **LLM verbalizer (any OpenAI-compatible API):** `LLM_API_KEY` + `LLM_MODEL` (see `.env.example`);
  constrained rephrase prompt (keep `[KB-ID]`, add nothing). Off by default → `summary_mode: deterministic`.
- **Status:** `GET /integrations/status` shows live health of each integration.

## API reference

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | liveness + KB size + retriever backend |
| POST | `/assess` | `{site, query?, enrich=true, verbalize=false}` → full report |
| POST | `/chat` | `{session_id, message, site_json?, enrich, verbalize}` → reply + memory |
| GET | `/knowledge/search?q=&region=&top_k=` | retrieval debug trace (scores + matched terms) |
| GET | `/provenance?ids=KB01,KB04` | exact evidence cards used |
| GET | `/sessions/{sid}` | conversation history |
| GET | `/integrations/status` | external API health |
| GET | `/docs` | interactive OpenAPI docs |

Frontend (`api/static/`, zero build step): **Chat Scientist** · **Structured Assess**
(form → phased report cards) · **Knowledge Explorer** (scores + evidence modal + `.md` export).

## Project structure

```
api/main.py api/static/   FastAPI + 3-tab UI        src/retriever.py src/bm25.py  RAG (BM25/TF-IDF/dense)
src/reasoner.py           diagnosis+plan+confidence  src/conversation.py          memory + extraction
src/geo.py src/integrations.py  geo + climate + LLM src/schemas.py               validation
knowledge/                32 cards + schema + SOURCES + benchmark + build_index
tests/ (12)  demo/example_semi_arid.json  app/chat.py (CLI)  Dockerfile  .github/workflows/ci.yml
```

## Local setup

```powershell
# easiest: double-click run_local.ps1, wait for the green URL, open http://127.0.0.1:8000
pip install -r requirements.txt
python -m pytest tests -q          # 12 passed
$env:RETRIEVER_BACKEND = "bm25"    # default; tfidf|dense also supported
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000
python -m app.chat --demo demo/example_semi_arid.json   # CLI demo
python -m knowledge.build_index                       # validate KB
python -m knowledge.benchmark_retrieval               # retrieval benchmark
```

Docker: `docker build -t darukaa .; docker run -p 8000:8000 darukaa`

## Database / schema

No server DB required. `sessions.db` (SQLite, gitignored) holds multi-turn memory;
knowledge is versioned JSON (`knowledge/schema.json`) → migratable to Postgres+pgvector/Chroma
(`RETRIEVER_BACKEND=dense` already uses the same `query()` interface).

## CI/CD

GitHub Actions (`ci.yml`): `pip install` + `python -m pytest -q` on every push — green.
Deploy: Dockerfile (uvicorn :8000) → Render / Fly.io / Hugging Face Spaces; set
`RETRIEVER_BACKEND=bm25` in deploy env.

## Configuration

Copy `.env.example` → `.env`. Everything runs unset (deterministic offline mode);
set `LLM_API_KEY` + `LLM_MODEL` only to enable the verbalizer.

## Limitations & roadmap

1. Lexical retrieval still misses zero-overlap paraphrases → dense embeddings when deps/disk allow.
2. Climate enrichment is a 90-day observed hint, not annual climatology — flagged as such.
3. KB is 32 curated cards (breadth over exhaustiveness); measurement cards (KB26/KB27) let users verify gains.
4. LLM verbalizer untested against a live key in CI (offline-first by design).

## Submission checklist

1. GitHub: this repo (public link; if private, invite the 4 reviewer accounts).
2. Live demo URL: deployed app link.
3. This README = architecture + DB/schema + setup + CI/CD overview.
4. Notes: no credentials needed; runs fully offline; optional integrations degrade gracefully.
