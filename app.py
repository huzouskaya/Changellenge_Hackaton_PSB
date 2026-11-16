from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Dict
from pathlib import Path
from assistant import Assistant

app = FastAPI(title="Юридический ассистент ПСБ")

static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

assistant = Assistant()

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[Message] = []

class ChatResponse(BaseModel):
    answer: str
    sources: List[Dict]

@app.get("/", response_class=HTMLResponse)
async def index():
    with open(Path(__file__).parent / "templates" / "index.html", 'r', encoding='utf-8') as f:
        return f.read()

@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    try:
        history = [{"role": m.role, "content": m.content} for m in req.history]
        res = assistant.ask(req.message, history)
        return ChatResponse(answer=res["answer"], sources=res["sources"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)