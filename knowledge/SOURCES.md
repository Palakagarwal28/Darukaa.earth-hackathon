# Knowledge Base — coverage & sources

32 evidence cards (`evidence_cards.json`, schema in `schema.json`). Validate: `python -m knowledge.build_index`.

| Need | Cards |
|---|---|
| Soil pH / SOC / moisture | KB01,02,03,06,10,15,16,17,22,27,28,30 |
| Land use / cover | KB05,07,09,13,18,19,23,24,25,31,32 |
| Biodiversity indicators | KB05,08,11,13,18,19,20,24,26,29,30 |
| Climate (temp/rain) | KB02,04,10,14,17,23,25,28,32 |
| Human impact | KB08,09,12,15,21,22,23,30,31 |
| Measurement protocols | KB26 (eDNA), KB27 (soil health card) |
| Non-obvious differentiators | KB29 nesting (not flowers), KB30 dung beetles, KB18 invasives, KB16 sodic |

## Key sources (full citation per card + URL where open)
FAO Soils/Agroforestry/Irrigation/Fire (2017-2022) · IPCC AR6 WGIII Ch.7 + Adaptation · IPBES Pollinators (2016), Global (2019), Invasives (2023) · UNCCD Drought Toolbox · Ramsar · CBD Restoration · CSSRI Karnal · Poeplau & Don 2015 (GCB) · Dainese et al. 2019 (Sci Adv) · Haddad et al. 2015 · Bowles et al. 2020 (Nature Food) · Lehmann & Joseph biochar 2015 · Thomsen & Willerslev eDNA · Ostrom commons.

## Retrieval pipeline (for judges)
`knowledge/evidence_cards.json` → `src/retriever.py` TF-IDF cosine (+region bonus) → `src/reasoner.py` ranks by confidence+score → API returns `provenance[{kb_id,title,score}]` → `GET /provenance?ids=` shows exact cards. Swap to dense embeddings via `RETRIEVER_BACKEND=dense` (same interface).
