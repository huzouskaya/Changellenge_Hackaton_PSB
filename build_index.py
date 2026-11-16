import sys
import json
import numpy as np
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from loader import load_documents
from config import Config

def main():
    kb_path = Path(Config.KB_PATH)
    print("Загрузка документов...", file=sys.stderr)
    docs = load_documents(kb_path)
    print(f"Загружено документов: {len(docs)}", file=sys.stderr)

    if not docs:
        print("Документы не найдены!", file=sys.stderr)
        sys.exit(1)

    print("Разбиение на чанки...", file=sys.stderr)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=Config.CHUNK_SIZE,
        chunk_overlap=Config.CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""]
    )

    chunks = []
    for doc in docs:
        texts = splitter.split_text(doc["text"])
        for i, text in enumerate(texts):
            chunks.append({
                "text": text,
                "meta": {**doc["meta"], "chunk_id": f"{doc['meta']['source']}_{i}"}
            })

    print(f"Создано чанков: {len(chunks)}", file=sys.stderr)

    print("Загрузка модели BAAI/bge-m3...", file=sys.stderr)
    model = SentenceTransformer("BAAI/bge-m3", trust_remote_code=True)

    print("Создание эмбеддингов...", file=sys.stderr)
    texts = [c["text"] for c in chunks]
    embeddings = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=True,
        normalize_embeddings=True
    )

    print("Сохранение индекса в корень...", file=sys.stderr)
    embeddings_np = np.array(embeddings, dtype=np.float16)
    np.save(Config.EMB_FILE, embeddings_np)

    with open(Config.CHUNKS_FILE, 'w', encoding='utf-8') as f:
        json.dump(chunks, f, ensure_ascii=False)

    emb_size = Path(Config.EMB_FILE).stat().st_size / 1_048_576
    chunks_size = Path(Config.CHUNKS_FILE).stat().st_size / 1_048_576
    print(f"OK: embeddings.npy ({emb_size:.1f} MB), chunks.json ({chunks_size:.1f} MB)", file=sys.stderr)

if __name__ == "__main__":
    main()