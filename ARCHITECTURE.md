# System Architecture — for evaluators

How Darukaa.Earth meets each requirement, and exactly where to verify it.

## 1. Big picture

```
 Text / JSON / Geo
        │
        ▼
 Conversation Manager ── SQLite memory (per session id)
        │  merges: stored site ← explicit JSON ← text extraction (incl. "lat, lon")
        ▼
 Metric Extractor ── 5 domains: soil / land / biodiversity / climate / human impact
        │
        ├── Geo inference (offline region boxes) + optional Open-Meteo enrichment (flagged)
        ▼
 Knowledge Retriever ── 32 evidence cards → BM25 + agro synonyms (default; TF-IDF/dense optional)
        │  every hit: kb_id + score + matched_terms (why this card)
        ▼
 Reasoning Engine ── interaction diagnosis (≥3 vars) → confidence → sequencing → trade-offs
        │
        ▼
 Response ── diagnosis + phased plan + targets + recommendations + measure-next + provenance
             (optional LLM rephrase of grounded output only; default deterministic)
```

No generic LLM-only path exists: without retrieved cards there are no recommendations.

## 2. Request lifecycle (worked example)

Input: `SOC 0.3%, low rainfall 450mm, monoculture wheat, semi-arid`

1. **Extract:** `soc_pct=0.3, rainfall=low/450mm, land_use=monoculture, crop=wheat, region=semi-arid`
   (`src/conversation.py::extract_metrics`; missing slots trigger clarifying questions instead).
2. **Retrieve:** BM25 over 32 card-documents (+region bonus) → KB01 (0.25), KB20, KB02, KB11,
   each with matched terms, e.g. KB01 ← `monoculture, wheat, cereal` (`src/retriever.py`, `src/bm25.py`).
3. **Reason:** diagnosis links the variables —
   *low SOC → poor water holding → amplifies drought → monoculture removes refugia → pollinator/pest imbalance*;
   confidence per rec (evidence strength ± region fit + completeness); sequencing puts chemistry
   first, water early (`src/reasoner.py`).
4. **Respond:** diagnosis + Now/Season/Year-1–3 plan + per-metric targets + 4 recs
   (WHAT/WHY/metrics/effect/time/confidence/ref `[KB-ID]`) + trade-offs + `measure_next`
   + `provenance[{kb_id,title,score}]`. Verify: `POST /assess` with `demo/example_semi_arid.json`.

## 3. Knowledge system design (20%)

- **Store:** `knowledge/evidence_cards.json` (32 cards) validated by `knowledge/schema.json`
  (`python -m knowledge.build_index` checks IDs, fields, coverage).
- **Coverage:** soil 12 · land 11 · biodiversity 11 · climate 9 · human impact 9 ·
  measurement protocols 2 (eDNA KB26, soil card KB27); horizons short 14 / medium 11 / long 7;
  confidence high 17 / medium 15. Sources: FAO, IPCC AR6, IPBES (2016/2019/2023), UNCCD,
  Ramsar, CBD + peer-reviewed meta-analyses (full map: `knowledge/SOURCES.md`).
- **Retrieval:** BM25 (term saturation + length norm) + curated agro synonym map in both
  directions (`drought<->water scarcity`, `bees->pollinator`, `crust->sodic`, `floods->waterlogging`…).
  Backends switch via `RETRIEVER_BACKEND=bm25|tfidf|dense` with one `query()` interface.
- **Measured:** 7-query benchmark (`python -m knowledge.benchmark_retrieval`,
  report in `knowledge/retrieval_benchmark.md`) — TF-IDF 5/7, BM25 7/7, with 2 genuine flips on
  farmer-phrased queries ("white crust…"→KB16, "floods…"→KB28). Known limit (documented):
  zero-overlap paraphrases still miss on lexical backends — the case for dense embeddings later.
- **Latency (dev machine):** BM25 top-4 median 2.3 ms; `assess()` end-to-end 2.7 ms;
  `POST /assess` over HTTP 13.4 ms. No LLM/paid API in the critical path.

## 4. Conversational intelligence (15%)

- **Clarifying questions:** `REQUIRED_SLOTS = soc_pct, rainfall, land_use`; vague input returns
  targeted questions, never a guess (`src/conversation.py::chat`, `missing_slots`).
- **Memory:** every turn persisted in SQLite (`sessions.db`, gitignored); explicit JSON overrides
  memory; new text merges in. Inspect: `GET /sessions/{sid}`.
- **Value-of-information:** `measure_next` ranks the 3 missing inputs by decision impact, so
  follow-ups are the questions that most raise confidence.

## 5. How to verify each criterion (5-minute script)

| Criterion | Do this | Expect |
|---|---|---|
| Knowledge grounding | `GET /knowledge/search?q=white crust salty field` | KB16 top hit with score + matched terms |
| No generic answers | `POST /assess` with 1 variable only | clarifying request (chat) / low-confidence flagged report |
| Multi-metric (≥3 vars) | wheat demo JSON | diagnosis chaining SOC×rain×monoculture; `variables_count: 6` |
| Evidence per rec | any report → `GET /provenance?ids=<KB-IDs>` | full cards: mechanism, effect size, source |
| Memory | same `session_id`, two messages | second answer reuses first message's site data |
| Offline | disconnect network, repeat all above | identical results (integrations degrade gracefully) |

Test suite: `python -m pytest tests -q` → 12 passed (reasoning, memory, geo, enrichment
on/off/failure, LLM-off default, provenance, judge-feature fields). CI runs it on every push.
