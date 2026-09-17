# Retrieval benchmark: TF-IDF vs BM25+synonyms

7 queries: 5 keyword + 2 adversarial paraphrases (user language, no card keywords).
Metric: top-2 hits contain at least one expected card.

| # | Query | Expected | TF-IDF top-2 | BM25 top-2 |
|---|-------|----------|--------------|------------|
| 1 | low SOC monoculture wheat semi-arid | KB01 | KB01,KB11 PASS | KB01,KB02 PASS |
| 2 | water scarcity farm, crops dying, no rain | KB04 | KB04,KB32 PASS | KB04,KB20 PASS |
| 3 | bees disappearing from fields | KB08,KB29 | KB24,KB29 PASS | KB29,KB24 PASS |
| 4 | salt-affected high pH soil, crops fail | KB06,KB16 | KB06,KB27 PASS | KB06,KB16 PASS |
| 5 | stubble burning smoke, soil dead | KB15 | KB15,KB22 PASS | KB15,KB27 PASS |
| 6 | white crust on field, salty, nothing grows | KB16 | KB05,KB28 MISS | KB16,KB06 PASS |
| 7 | field floods every monsoon, roots rot | KB28 | KB05,KB21 MISS | KB28,KB05 PASS |

**Score: TF-IDF 5/7 - BM25+synonyms 7/7**

Notes: BM25 adds term-saturation + length norm; the agro synonym map
(drought<->water scarcity, SOC<->soil carbon, bees<->pollinator, etc.) bridges
jargon mismatch with zero new dependencies. Dense embeddings
(`RETRIEVER_BACKEND=dense`, all-MiniLM-L6-v2) remain the planned next step
where disk/deps allow — same `query()` interface, no API changes.