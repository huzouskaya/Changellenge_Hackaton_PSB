from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
from pathlib import Path
import uvicorn

app = FastAPI(title="Юридический ассистент ПСБ")

static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

assistant = None
assistant_error = None
try:
    from assistant import Assistant
    assistant = Assistant()
    if not assistant.ready:
        assistant_error = "Индекс базы знаний не загружен. Ответы будут недоступны."
except Exception as e:
    assistant_error = f"Ассистент не инициализирован: {e}"
    print(f"[WARN] {assistant_error}")

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[Message] = []

class ChatResponse(BaseModel):
    answer: str
    sources: List[Dict] = []
    bot_available: bool = True

@app.get("/", response_class=HTMLResponse)
async def index():
    tpl = Path(__file__).parent / "templates" / "index.html"
    if not tpl.exists():
        return "<h1>templates/index.html не найден</h1>"
    return tpl.read_text(encoding="utf-8")

@app.get("/api/health")
async def health():
    return {
        "bot_available": assistant is not None and assistant.ready,
        "error": assistant_error,
    }

@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    # Если ассистент недоступен — возвращаем заглушку, но UI работает
    if assistant is None or not assistant.ready:
        return ChatResponse(
            answer=(
                "⚠️ Бот временно недоступен. "
                f"{assistant_error or 'Проверьте наличие API-ключа и базы знаний.'}\n\n"
                "Интерфейс работает. Повторите запрос, когда бот будет готов."
            ),
            sources=[],
            bot_available=False,
        )
    try:
        history = [{"role": m.role, "content": m.content} for m in req.history]
        res = assistant.ask(req.message, history)
        return ChatResponse(
            answer=res.get("answer", ""),
            sources=res.get("sources", []),
            bot_available=True,
        )
    except Exception as e:
        return ChatResponse(
            answer=f"Ошибка при генерации ответа: {e}",
            sources=[],
            bot_available=False,
        )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)