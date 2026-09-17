"""BM25 retrieval with agro-domain synonym expansion. Zero new dependencies (numpy only).

Why: TF-IDF misses vocabulary mismatch ("water scarcity" vs "drought",
"SOC" vs "soil carbon"). BM25 adds term-saturation + length normalization;
the synonym map bridges domain jargon. This is the lexical half of a hybrid
RAG pipeline; dense embeddings remain available via RETRIEVER_BACKEND=dense.
"""
import re
import numpy as np

SYNONYMS = {
    "soc": ["soil organic carbon", "soil carbon", "organic matter", "carbon"],
    "drought": ["water scarcity", "water-limited", "dry", "arid", "low rainfall"],
    "water scarcity": ["drought", "low rainfall", "dry", "arid"],
    "monoculture": ["single crop", "monocrop", "cereal monoculture"],
    "pollinator": ["bee", "bees", "pollination", "flower visitor"],
    "pesticide": ["insecticide", "spray", "agrochemical"],
    "sodic": ["alkaline", "saline", "salt-affected", "high ph"],
    "alkaline": ["sodic", "high ph", "salt-affected"],
    "wetland": ["pond", "marsh", "waterbody", "amphibian habitat"],
    "pond": ["wetland", "waterbody", "farm pond"],
    "grazing": ["pasture", "livestock", "overgrazing", "grassland"],
    "fire": ["burn", "burning", "wildfire", "stubble"],
    "heat": ["high temperature", "heatwave", "hot", "thermal stress"],
    "fertilizer": ["nitrogen", "nutrient", "urea", "n runoff"],
    "erosion": ["soil loss", "wind erosion", "runoff", "degradation"],
    "native": ["indigenous", "local", "local-provenance"],
    "invasive": ["lantana", "weed", "alien species", "juliflora"],
    "corridor": ["hedgerow", "connectivity", "habitat link", "wildlife passage"],
    "mulch": ["residue cover", "straw cover", "ground cover"],
    "biochar": ["charcoal", "pyrolysis", "black carbon"],
    # user-language keys (what farmers type) -> card vocabulary
    "bees": ["pollinator", "pollination", "bee", "flower visitor"],
    "bee": ["pollinator", "pollination"],
    "dry": ["drought", "low rainfall", "arid", "water-limited"],
    "salt": ["sodic", "alkaline", "saline", "salt-affected"],
    "salty": ["sodic", "alkaline", "saline", "salt-affected"],
    "crust": ["sodic", "alkaline", "saline", "salt-affected"],
    "flood": ["waterlogging", "drainage", "flooded", "waterlogged"],
    "floods": ["waterlogging", "drainage", "flooded"],
    "nest": ["nesting", "nest sites", "ground-nesting", "cavity-nester"],
    "nests": ["nesting", "nest sites", "ground-nesting"],
    "spray": ["pesticide", "insecticide", "agrochemical"],
    "worm": ["deworming", "anthelmintic", "ivermectin", "faecal-egg-count"],
}

def expand(query: str) -> str:
    q = query.lower()
    extra = []
    for key, syns in SYNONYMS.items():
        if re.search(r"\b" + re.escape(key) + r"s?\b", q):
            extra.extend(syns)
    return query + " " + " ".join(extra)

_TOKEN = re.compile(r"[a-z]+")

def tokenize(text: str):
    return _TOKEN.findall(text.lower())

class BM25:
    def __init__(self, docs, k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.docs = [tokenize(d) for d in docs]
        self.N = len(self.docs)
        self.avgdl = float(np.mean([len(d) for d in self.docs])) or 1.0
        df = {}
        for d in self.docs:
            for t in set(d):
                df[t] = df.get(t, 0) + 1
        self.idf = {t: float(np.log(1 + (self.N - f + 0.5) / (f + 0.5))) for t, f in df.items()}

    def scores(self, query: str):
        q = tokenize(expand(query))
        out = np.zeros(self.N)
        for i, d in enumerate(self.docs):
            dl = len(d) or 1
            freq = {}
            for t in d:
                freq[t] = freq.get(t, 0) + 1
            s = 0.0
            for t in q:
                f = freq.get(t, 0)
                if not f:
                    continue
                idf = self.idf.get(t, 0.0)
                s += idf * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * dl / self.avgdl))
            out[i] = s
        # normalize to 0..1 for comparability with cosine scores
        mx = out.max()
        return out / mx if mx > 0 else out

    def explain(self, query: str, doc_idx: int, top: int = 3):
        """Top contributing query terms for one doc: [(term, contribution)]."""
        q = tokenize(expand(query))
        d = self.docs[doc_idx]
        dl = len(d) or 1
        freq = {}
        for t in d:
            freq[t] = freq.get(t, 0) + 1
        contrib = {}
        for t in q:
            f = freq.get(t, 0)
            if not f:
                continue
            idf = self.idf.get(t, 0.0)
            c = idf * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * dl / self.avgdl))
            contrib[t] = contrib.get(t, 0.0) + c
        return sorted(contrib.items(), key=lambda x: x[1], reverse=True)[:top]
