import json
import sys
import numpy as np
import faiss
import httpx
from pathlib import Path
from rank_bm25 import BM25Okapi
from langchain_text_splitters import RecursiveCharacterTextSplitter
from config import Config
from loader import load_documents


class Indexer:
    def __init__(self):
        self.index = None
        self.chunks = []
        self.bm25 = None
        self._reranker_available = None

    def load(self):
        if not (Path(Config.EMB_FILE).exists() and Path(Config.CHUNKS_FILE).exists()):
            return False
        try:
            with open(Config.CHUNKS_FILE, 'r', encoding='utf-8') as f:
                self.chunks = json.load(f)
            emb = np.load(Config.EMB_FILE).astype(np.float32)
            if emb.ndim != 2 or emb.shape[0] != len(self.chunks):
                print(f"Несоответствие размеров: emb={emb.shape}, chunks={len(self.chunks)}", file=sys.stderr)
                return False
            faiss.normalize_L2(emb)
            self.index = faiss.IndexFlatIP(emb.shape[1])
            self.index.add(emb)
            tokenized = [self._tokenize_ru(doc["text"]) for doc in self.chunks]
            self.bm25 = BM25Okapi(tokenized)
            return True
        except Exception as e:
            print("Ошибка загрузки индекса")
            return False

    def _save(self, embeddings_np):
        try:
            np.save(Config.EMB_FILE, embeddings_np)
            with open(Config.CHUNKS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.chunks, f, ensure_ascii=False)
        except Exception as e:
            print("Ошибка сохранения индекса")

    def _tokenize_ru(self, text):
        import re
        tokens = re.findall(r'[а-яёa-z0-9]+', text.lower())
        return tokens

    def build(self, kb_path, embed_fn):
        docs = load_documents(kb_path)
        if not docs:
            print("Документы не найдены!", file=sys.stderr)
            return False

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,
            chunk_overlap=200,
            separators=[
                "\nСтатья ", "\nГлава ", "\nРаздел ", "\nПункт ",
                "\n\n", "\n", ". ", " ", ""
            ],
            length_function=len,
        )

        self.chunks = []
        for doc in docs:
            texts = splitter.split_text(doc["text"])
            for i, text in enumerate(texts):
                if text.strip():
                    self.chunks.append({
                        "text": text,
                        "meta": {**doc["meta"], "chunk_id": f"{doc['meta']['source']}_{i}"}
                    })

        print(f"Создано чанков: {len(self.chunks)}", file=sys.stderr)

        if not self.chunks:
            return False

        texts = [c["text"] for c in self.chunks]
        print("Создание эмбеддингов через API...", file=sys.stderr)

        embeddings = []
        batch_size = 32
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            try:
                batch_emb = embed_fn(batch)
                embeddings.extend(batch_emb)
            except:
                print(f"Ошибка эмбеддинга батча {i}")
                embeddings.extend([np.zeros(1024).tolist() for _ in batch])

        embeddings_np = np.array(embeddings, dtype=np.float32)
        faiss.normalize_L2(embeddings_np)

        self.index = faiss.IndexFlatIP(embeddings_np.shape[1])
        self.index.add(embeddings_np)

        tokenized = [self._tokenize_ru(doc["text"]) for doc in self.chunks]
        self.bm25 = BM25Okapi(tokenized)

        self._save(embeddings_np)
        return True

    def _rerank(self, query, docs_with_scores, client):
        if not docs_with_scores or not client:
            return docs_with_scores

        if self._reranker_available is None:
            self._reranker_available = self._check_reranker(client)

        if not self._reranker_available:
            return docs_with_scores[:Config.RERANKER_TOP_N]

        try:
            documents = [doc["text"] for doc, _ in docs_with_scores]
            response = client.post(
                f"{Config.BASE_URL}/rerank",
                json={
                    "model": Config.RERANKER_MODEL,
                    "query": query,
                    "documents": documents,
                    "top_n": Config.RERANKER_TOP_N,
                },
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()

            reranked = []
            for item in data.get("results", []):
                idx = item["index"]
                score = item["relevance_score"]
                reranked.append((docs_with_scores[idx][0], score))

            return reranked

        except:
            print("Реранкер недоступен")
            self._reranker_available = False
            return docs_with_scores[:Config.RERANKER_TOP_N]

    def _check_reranker(self, client):
        try:
            response = client.post(
                f"{Config.BASE_URL}/rerank",
                json={
                    "model": Config.RERANKER_MODEL,
                    "query": "test",
                    "documents": ["test document"],
                    "top_n": 1,
                },
                timeout=10.0,
            )
            return response.status_code == 200
        except:
            return False

    def search(self, query, embed_fn, client=None):
        if self.index is None or not self.chunks:
            return []

        query_emb = np.array(embed_fn([query]), dtype=np.float32).reshape(1, -1)
        faiss.normalize_L2(query_emb)
        dists, ids = self.index.search(query_emb, Config.TOP_K)
        vector_results = [(self.chunks[i], float(d)) for d, i in zip(dists[0], ids[0]) if i != -1]

        query_tokens = self._tokenize_ru(query)
        bm25_scores = self.bm25.get_scores(query_tokens)
        top_ids = np.argsort(bm25_scores)[::-1][:Config.TOP_K]
        bm25_results = [(self.chunks[i], float(bm25_scores[i])) for i in top_ids if bm25_scores[i] > 0]

        k = 60
        combined = {}

        for rank, (doc, _) in enumerate(vector_results, 1):
            cid = doc["meta"]["chunk_id"]
            rrf_score = 1.0 / (k + rank)
            combined[cid] = {"doc": doc, "score": rrf_score}

        for rank, (doc, _) in enumerate(bm25_results, 1):
            cid = doc["meta"]["chunk_id"]
            rrf_score = 1.0 / (k + rank)
            if cid in combined:
                combined[cid]["score"] += rrf_score
            else:
                combined[cid] = {"doc": doc, "score": rrf_score}

        ranked = sorted(combined.values(), key=lambda x: x["score"], reverse=True)
        hybrid_results = [(r["doc"], r["score"]) for r in ranked[:Config.TOP_K]]

        if client and len(hybrid_results) > Config.RERANKER_TOP_N:
            final_results = self._rerank(query, hybrid_results, client)
        else:
            final_results = hybrid_results[:Config.RERANKER_TOP_N]

        return final_results