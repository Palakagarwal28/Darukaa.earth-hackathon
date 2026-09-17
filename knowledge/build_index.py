"""Validate KB, print coverage matrix, smoke-test retrieval. Run: python -m knowledge.build_index"""
import json, pathlib, sys
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parents[1]
KB = ROOT / "knowledge" / "evidence_cards.json"
SCHEMA = ROOT / "knowledge" / "schema.json"

REQUIRED = json.loads(SCHEMA.read_text())["required"]
DOMAINS_MUST = ["soil", "land use", "biodiversity", "climate", "human impact"]
REGIONS = ["semi-arid", "arid", "subhumid", "humid", "tropical", "temperate", "grassland", "all"]

def main():
    cards = json.loads(KB.read_text(encoding="utf-8"))
    errs = []
    ids = [c.get("id") for c in cards]
    if len(ids) != len(set(ids)): errs.append("duplicate IDs")
    for c in cards:
        for f in REQUIRED:
            if not c.get(f): errs.append(f"{c.get('id')}: missing {f}")
        if c.get("confidence") not in ("high", "medium", "low"): errs.append(f"{c.get('id')}: bad confidence")
        if c.get("time_horizon") not in ("short", "medium", "long"): errs.append(f"{c.get('id')}: bad horizon")
    print(f"cards: {len(cards)} | unique IDs: {len(set(ids))}")
    # domain coverage
    blob = " ".join(c.get("domain", "") for c in cards).lower()
    print("\n-- domain coverage --")
    for d in DOMAINS_MUST:
        print(f"  {'OK ' if d in blob else 'GAP'}  {d}: {blob.count(d)} cards mention it")
    # region coverage
    print("\n-- region coverage --")
    cnt = Counter()
    for c in cards:
        for r in c.get("region_fit", []): cnt[r.lower()] += 1
    for r in REGIONS: print(f"  {r:10s}: {cnt.get(r, 0)}")
    # horizon + confidence balance
    print("\n-- horizons:", Counter(c["time_horizon"] for c in cards))
    print("-- confidence:", Counter(c["confidence"] for c in cards))
    # provenance quality
    with_url = sum(1 for c in cards if c.get("source_url"))
    with_year = sum(1 for c in cards if c.get("year"))
    print(f"-- provenance: {with_url}/{len(cards)} with URL, {with_year}/{len(cards)} with year")
    # retrieval smoke test (needs sklearn)
    try:
        sys.path.insert(0, str(ROOT))
        from src.retriever import Retriever
        r = Retriever()
        for q in ["low SOC monoculture wheat semi-arid", "pesticide pollinator decline",
                  "sodic alkaline soil", "wetland amphibian pond", "dung beetle grazing"]:
            hits = r.query(q, {}, top_k=2)
            print(f"  Q:{q[:40]:42s} -> {[h['id'] for h in hits]}")
    except Exception as e:
        print("retrieval smoke test skipped:", e)
    if errs:
        print("\nERRORS:"); [print(" -", e) for e in errs[:20]]; sys.exit(1)
    print("\nKB VALID [ok]")

if __name__ == "__main__":
    main()
