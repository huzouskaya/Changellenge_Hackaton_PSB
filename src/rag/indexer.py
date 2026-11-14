import json
import numpy as np
import faiss
from pathlib import Path
from rank_bm25 import BM25Okapi
from src.config import Config

class Indexer:
    def __init__(self):
        self.index_path = Path(Config.INDEX_PATH)
        self.index = None
        self.chunks = []
        self.bm25 = None

    def save(self, embeddings, chunks):
        self.index_path.mkdir(parents=True, exist_ok=True)
        emb16 = np.array(embeddings, dtype=np.float16)
        np.save(self.index_path / "embeddings.npy", emb16)
        with open(self.index_path / "chunks.json", "w", encoding="utf-8") as f:
            json.dump(chunks, f, ensure_ascii=False)

    def load(self):
        emb_file = self.index_path / "embeddings.npy"
        chunks_file = self.index_path / "chunks.json"
        if not (emb_file.exists() and chunks_file.exists()):
            return False

        with open(chunks_file, "r", encoding="utf-8") as f:
            self.chunks = json.load(f)

        emb = np.load(emb_file).astype(np.float32)
        faiss.normalize_L2(emb)
        self.index = faiss.IndexFlatIP(emb.shape[1])
        self.index.add(emb)

        tokenized = [doc["text"].lower().split() for doc in self.chunks]
        self.bm25 = BM25Okapi(tokenized)
        return True

    def search(self, query, embed_fn):
        if self.index is None or not self.chunks:
            return []

        query_emb = np.array(embed_fn([query]), dtype=np.float32)
        faiss.normalize_L2(query_emb)
        dists, ids = self.index.search(query_emb, Config.TOP_K_RETRIEVE)

        vector_results = [
            (self.chunks[i], float(d))
            for d, i in zip(dists[0], ids[0])
            if i != -1
        ]

        bm25_scores = self.bm25.get_scores(query.lower().split())
        top_ids = np.argsort(bm25_scores)[::-1][: Config.TOP_K_RETRIEVE]
        bm25_results = [
            (self.chunks[i], float(bm25_scores[i]))
            for i in top_ids
            if bm25_scores[i] > 0
        ]

        max_v = max([s for _, s in vector_results], default=1.0) or 1.0
        max_b = max([s for _, s in bm25_results], default=1.0) or 1.0

        combined = {}
        for doc, score in vector_results:
            cid = doc["meta"]["chunk_id"]
            combined[cid] = {"doc": doc, "score": 0.7 * (score / max_v)}
        for doc, score in bm25_results:
            cid = doc["meta"]["chunk_id"]
            bonus = 0.3 * (score / max_b)
            if cid in combined:
                combined[cid]["score"] += bonus
            else:
                combined[cid] = {"doc": doc, "score": bonus}

        ranked = sorted(combined.values(), key=lambda x: x["score"], reverse=True)
        return [(r["doc"], r["score"]) for r in ranked[: Config.TOP_K_FINAL]]