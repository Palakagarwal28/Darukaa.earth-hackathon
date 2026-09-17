"""Retriever v2: TF-IDF default (offline) | BM25+synonyms | dense embeddings.
Set RETRIEVER_BACKEND=tfidf|bm25|dense (default tfidf). The query() signature
is identical across backends, so reasoner/API need no change."""
import json, os, pathlib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

KB_PATH = pathlib.Path(__file__).resolve().parents[1] / "knowledge" / "evidence_cards.json"

def load_cards():
    return json.loads(KB_PATH.read_text(encoding="utf-8"))

def _doc(c):
    return " ".join([c["title"], c["domain"], c["intervention"], c["mechanism"],
                     " ".join(c["metrics_improved"]), " ".join(c.get("region_fit", []))])

_BACKEND = os.getenv("RETRIEVER_BACKEND", "bm25")
_instance = None

class Retriever:
    """Provenance: every hit returns kb_id + retrieval_score."""
    def __init__(self, backend: str | None = None):
        self.backend = backend or _BACKEND
        self.cards = load_cards()
        self.docs = [_doc(c) for c in self.cards]
        if self.backend == "bm25":
            from src.bm25 import BM25
            self.bm25 = BM25(self.docs)
        elif self.backend == "dense":
            try:
                from sentence_transformers import SentenceTransformer
                import numpy as np
                self.model = SentenceTransformer("all-MiniLM-L6-v2")
                self.embs = self.model.encode(self.docs, normalize_embeddings=True)
                self._np = np
            except Exception as e:
                print(f"[retriever] dense unavailable ({e}), falling back to tfidf")
                self.backend = "tfidf"
        if self.backend == "tfidf":
            self.vec = TfidfVectorizer(stop_words="english")
            self.mat = self.vec.fit_transform(self.docs)

    def query(self, text: str, site: dict | None = None, top_k: int = 4):
        site = site or {}
        boost = f" {site.get('region','')} {site.get('land_use','')} {site.get('crop','')}"
        q = (text or "") + boost
        if self.backend == "dense":
            qv = self.model.encode([q], normalize_embeddings=True)
            scores = (qv @ self.embs.T)[0]
            ranked = sorted(zip(range(len(self.cards)), self.cards, scores),
                            key=lambda x: x[2], reverse=True)
        elif self.backend == "bm25":
            scores = self.bm25.scores(q)
            ranked = sorted(zip(range(len(self.cards)), self.cards, scores),
                            key=lambda x: x[2], reverse=True)
        else:
            qv = self.vec.transform([q])
            scores = cosine_similarity(qv, self.mat)[0]
            ranked = sorted(zip(range(len(self.cards)), self.cards, scores),
                            key=lambda x: x[2], reverse=True)
        region = str(site.get("region", "")).lower()
        out = []
        for idx, card, s in ranked[:top_k * 2]:
            fits = [r.lower() for r in card.get("region_fit", ["all"])]
            bonus = 0.05 if ("all" in fits or (region and region in fits)) else 0.0
            out.append({**card, "retrieval_score": round(float(s) + bonus, 3),
                        "matched_terms": self._explain(q, idx)})
        out.sort(key=lambda c: c["retrieval_score"], reverse=True)
        return out[:top_k]

    def _explain(self, q: str, idx: int):
        """Why this card matched: top contributing terms (empty for dense)."""
        try:
            if self.backend == "bm25":
                return [t for t, _ in self.bm25.explain(q, idx)]
            if self.backend == "tfidf":
                import numpy as np
                feats = self.vec.get_feature_names_out()
                qv = self.vec.transform([q]).toarray()[0]
                row = self.mat[idx].toarray()[0]
                contrib = qv * row
                top = np.argsort(contrib)[::-1][:3]
                return [str(feats[i]) for i in top if contrib[i] > 0]
        except Exception:
            pass
        return []

def get_retriever() -> Retriever:
    global _instance
    if _instance is None:
        _instance = Retriever()
    return _instance
