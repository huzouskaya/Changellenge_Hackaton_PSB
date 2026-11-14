import os
import json
import numpy as np
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from openai import OpenAI
from src.config import Config
from src.rag.loader import Loader
from src.rag.indexer import Indexer

def main():
    client = OpenAI(api_key=Config.API_KEY, base_url=Config.BASE_URL)

    docs = Loader(Config.KB_PATH).load()
    print(f"Docs: {len(docs)}")
    if not docs:
        print("No documents found")
        return

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=Config.CHUNK_SIZE,
        chunk_overlap=Config.CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = []
    for doc in docs:
        for i, text in enumerate(splitter.split_text(doc["text"])):
            chunks.append({
                "text": text,
                "meta": {**doc["meta"], "chunk_id": f"{doc['meta']['source']}_{i}"},
            })
    print(f"Chunks: {len(chunks)}")

    texts = [c["text"] for c in chunks]
    embeddings = []
    for i in range(0, len(texts), 32):
        batch = texts[i:i + 32]
        embeddings.extend(client.embeddings.create(model=Config.EMBED_MODEL, input=batch).data)
        print(f"Embedded {min(i + 32, len(texts))}/{len(texts)}")

    embeddings = [e.embedding for e in embeddings]

    indexer = Indexer()
    indexer.save(embeddings, chunks)

    size = (Path(Config.INDEX_PATH) / "embeddings.npy").stat().st_size / 1_048_576
    print(f"Index saved. embeddings.npy = {size:.1f} MB")

if __name__ == "__main__":
    main()