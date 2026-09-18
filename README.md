# Darukaa.Earth — AI Biodiversity Intelligence Scientist

Behaves like an **AI environmental scientist, not a chatbot**: multi-metric reasoning over
soil · land · biodiversity · climate · human impact, with every recommendation backed by
retrievable evidence (`knowledge/evidence_cards.json`, 32 cards).

For the full system design, see **[ARCHITECTURE.md](ARCHITECTURE.md)** 

## Run it (2 minutes, offline, no keys needed)

```powershell
pip install -r requirements.txt
python -m pytest tests -q              # 12 passed
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000
# open http://127.0.0.1:8000  (API docs at /docs)
```

Or double-click `run_local.ps1`. Offline demo with no internet required:
`python -m app.chat --demo demo/example_semi_arid.json`
Shareable live demos: `?tab=chat&demo=1`, `?tab=assess&demo=1`, `?tab=kb&demo=1&q=...`

## What to try (maps to requirements)

1. **Chat tab** → send *"Biodiversity is declining on my land"* → system asks clarifying
   questions (SOC %, rainfall, land use), then returns a grounded report. Try
   **▶ Run semi-arid wheat demo**.
2. **Structured Assess tab** → fill the site form (or **▶ Fill wheat demo**) → diagnosis +
   phased action plan + measurable targets + evidence-backed recommendations.
3. **Knowledge tab** → search the evidence base (scores + matched terms shown) → click
   📖 to read the full cited card behind any recommendation.

## API (all local)

| Endpoint | Purpose |
|---|---|
| `POST /chat` | text + memory (clarifying Qs when incomplete) |
| `POST /assess` | `{site, query?}` JSON → full scientific report |
| `GET /knowledge/search` | retrieval trace for judges |
| `GET /provenance?ids=` | exact evidence cards cited |
| `GET /health`, `/integrations/status`, `/docs` | status + OpenAPI docs |

## Layout

```
api/ (FastAPI + UI)  src/ (retriever, reasoner, conversation, geo, integrations, schemas)
knowledge/ (32 cards + schema + SOURCES + benchmark)  tests/ (12)  demo/  Dockerfile  .github/workflows/ci.yml
```

## Notes for submission

- No deployment, no credentials, no keys needed — everything runs offline; external
  integrations (climate, LLM) are optional and degrade gracefully.
- CI runs tests on every push (green).
- Design details, data flow, and evaluation summary: **[ARCHITECTURE.md](ARCHITECTURE.md)**.
