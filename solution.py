import csv
import json
import sys
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from src.agents.assistant import Assistant

def load_questions(path):
    questions = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            history = []
            if row.get("history"):
                try:
                    history = json.loads(row["history"])
                except json.JSONDecodeError:
                    history = []
            questions.append({
                "id": row.get("id", ""),
                "question": row.get("question", ""),
                "history": history,
            })
    return questions

def main():
    base_dir = Path(__file__).parent
    q_file = base_dir / "demo_questions.csv"
    out_file = base_dir / "demo_output.csv"

    if not q_file.exists():
        print("demo_questions.csv not found", file=sys.stderr)
        sys.exit(1)

    start = time.time()
    assistant = Assistant()
    if not assistant.retriever.ready:
        print("WARNING: index not loaded, answers will be refusals", file=sys.stderr)

    questions = load_questions(q_file)
    print(f"Loaded {len(questions)} questions")

    def process(q):
        try:
            res = assistant.ask(q["question"], q["history"])
        except Exception as e:
            res = {"answer": f"Ошибка обработки: {e}", "sources": []}
        return {
            "id": q["id"],
            "answer": res["answer"],
            "sources": json.dumps(res["sources"], ensure_ascii=False),
        }

    with ThreadPoolExecutor(max_workers=8) as pool:
        answers = list(pool.map(process, questions))

    with open(out_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "answer", "sources"])
        writer.writeheader()
        writer.writerows(answers)

    print(f"Done in {time.time() - start:.1f}s, saved to {out_file}")

if __name__ == "__main__":
    main()