import csv
import time
import zipfile
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

try:
    from openai import OpenAI
    from config import Config
    from indexer import Indexer
    from assistant import Assistant
except:
    with open("submission.csv", "w", encoding="utf-8", newline="") as f:
        f.write("id,answer\n")
    raise SystemExit(0)

FALLBACK_ANSWER = (
    "Недостаточно информации в базе знаний для достоверного ответа. "
    "База нормативных документов не загрузилась или релевантные положения не найдены."
)

def safe_unpack_kb():
    try:
        kb_path = Path(Config.KB_PATH)
        kb_zip = Path(Config.KB_ZIP)
        
        if kb_path.exists() and any(kb_path.rglob("*")):
            return kb_path
            
        if kb_zip.exists():
            kb_path.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(kb_zip, 'r') as zf:
                zf.extractall(kb_path)
            if any(kb_path.rglob("*")):
                return kb_path
    except:
        print("Ошибка распаковки базы знаний")
    return None

def main():
    try:
        start = time.time()

        questions = []
        q_file = Path(Config.QUESTIONS_FILE)
        try:
            with open(q_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    questions.append({
                        "id": row.get("id", ""), 
                        "question": row.get("question", "")
                    })
        except:
            print("Не удалось прочитать questions.csv")

        if not questions:
            with open(Config.OUTPUT_FILE, 'w', encoding='utf-8', newline='') as f:
                f.write("id,answer\n")
            return

        client = None
        index_ok = False
        indexer = Indexer()

        try:
            if Config.API_KEY and Config.API_KEY != "EMPTY":
                client = OpenAI(
                    api_key=Config.API_KEY,
                    base_url=Config.BASE_URL,
                    timeout=Config.REQUEST_TIMEOUT,
                    max_retries=2,
                )

                def embed_fn(texts):
                    resp = client.embeddings.create(model=Config.EMB_MODEL, input=texts)
                    return [item.embedding for item in resp.data]

                kb_path = safe_unpack_kb()
                if kb_path:
                    if not indexer.load():
                        index_ok = indexer.build(kb_path, embed_fn)
                    else:
                        index_ok = True
        except:
            print("Ошибка инициализации или построения индекса")

        answers = []
        
        if not index_ok:
            answers = [{"id": q["id"], "answer": FALLBACK_ANSWER} for q in questions]
        else:
            assistant = Assistant()
            assistant.indexer = indexer
            assistant.client = client

            def process(q):
                try:
                    res = assistant.ask(q["question"])
                    return {"id": q["id"], "answer": res["answer"]}
                except Exception as e:
                    return {"id": q["id"], "answer": f"{FALLBACK_ANSWER} (Ошибка обработки: {e})"}

            try:
                with ThreadPoolExecutor(max_workers=Config.MAX_WORKERS) as pool:
                    answers = list(pool.map(process, questions))
            except:
                print("Ошибка пула потоков")
                answers = [{"id": q["id"], "answer": FALLBACK_ANSWER} for q in questions]

        try:
            with open(Config.OUTPUT_FILE, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=["id", "answer"])
                writer.writeheader()
                writer.writerows(answers)
        except:
            print("КРИТИЧЕСКАЯ ОШИБКА ЗАПИСИ CSV")
            with open(Config.OUTPUT_FILE, 'w', encoding='utf-8') as f:
                f.write("id,answer\n")

    except:
        print("ГЛОБАЛЬНАЯ ОШИБКА В MAIN")
        try:
            with open("submission.csv", 'w', encoding='utf-8') as f:
                f.write("id,answer\n")
        except:
            pass

if __name__ == "__main__":
    main()