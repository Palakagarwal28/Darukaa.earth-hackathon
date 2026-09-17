"""Benchmark TF-IDF vs BM25+synonyms. Run: python -m knowledge.benchmark_retrieval"""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from src.retriever import Retriever

QUERIES = [
    ("low SOC monoculture wheat semi-arid", {"KB01"}),
    ("water scarcity farm, crops dying, no rain", {"KB04"}),
    ("bees disappearing from fields", {"KB08", "KB29"}),
    ("salt-affected high pH soil, crops fail", {"KB16", "KB06"}),
    ("stubble burning smoke, soil dead", {"KB15"}),
    # adversarial paraphrases: user language, no card keywords
    ("white crust on field, salty, nothing grows", {"KB16"}),
    ("field floods every monsoon, roots rot", {"KB28"}),
]

def run(backend):
    r = Retriever(backend=backend)
    rows = []
    for q, expected in QUERIES:
        hits = [h["id"] for h in r.query(q, {}, top_k=2)]
        hit = bool(set(hits) & expected)
        rows.append((q, hits, sorted(expected), hit))
    return rows

def main():
    out = ["# Retrieval benchmark: TF-IDF vs BM25+synonyms\n",
           "7 queries: 5 keyword + 2 adversarial paraphrases (user language, no card keywords).",
           "Metric: top-2 hits contain at least one expected card.\n",
           "| # | Query | Expected | TF-IDF top-2 | BM25 top-2 |",
           "|---|-------|----------|--------------|------------|"]
    tfidf = run("tfidf"); bm25 = run("bm25")
    s_tf = s_bm = 0
    for i, ((q, th, exp, h1), (_, bh, _, h2)) in enumerate(zip(tfidf, bm25), 1):
        s_tf += h1; s_bm += h2
        out.append(f"| {i} | {q} | {','.join(exp)} | {','.join(th)} {'PASS' if h1 else 'MISS'} "
                   f"| {','.join(bh)} {'PASS' if h2 else 'MISS'} |")
    n = len(QUERIES)
    out += ["", f"**Score: TF-IDF {s_tf}/{n} - BM25+synonyms {s_bm}/{n}**",
            "",
            "Notes: BM25 adds term-saturation + length norm; the agro synonym map",
            "(drought<->water scarcity, SOC<->soil carbon, bees<->pollinator, etc.) bridges",
            "jargon mismatch with zero new dependencies. Dense embeddings",
            "(`RETRIEVER_BACKEND=dense`, all-MiniLM-L6-v2) remain the planned next step",
            "where disk/deps allow — same `query()` interface, no API changes."]
    text = "\n".join(out)
    print(text)
    (pathlib.Path(__file__).parent / "retrieval_benchmark.md").write_text(text, encoding="utf-8")

if __name__ == "__main__":
    main()
