import os
import sys
from dotenv import load_dotenv

load_dotenv()

_DEBUG_KEYWORDS = ("LLM", "OPENAI", "API", "KEY", "URL", "MODEL", "DATA", "DIR",
                    "TEMP", "TOKEN", "WORKER", "TOP", "CHUNK", "EMB", "RERANK")

def _mask(value):
    if not value:
        return ""
    if len(value) <= 12:
        return value
    return value[:6] + "..." + value[-4:]

def _dump_env():
    print(file=sys.stderr, flush=True)
    print("ENV DEBUG (platform variables)", file=sys.stderr, flush=True)
    for key in sorted(os.environ):
        if any(k in key.upper() for k in _DEBUG_KEYWORDS):
            val = os.environ[key]
            if "KEY" in key.upper() or "TOKEN" in key.upper() or "SECRET" in key.upper():
                val = _mask(val)
            print(f"  {key} = {val}", file=sys.stderr, flush=True)
    print(file=sys.stderr, flush=True)

_dump_env()

def _first(*names, default=""):
    for n in names:
        v = os.getenv(n)
        if v:
            return v
    return default

def _as_int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default

def _as_float(value, default):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

class Config:
    API_KEY = _first("LLM_API_KEY", "OPENAI_API_KEY", "API_KEY", default="EMPTY")
    BASE_URL = _first("LLM_BASE_URL", "OPENAI_BASE_URL", "OPENAI_BASE", default="http://localhost:8000/v1")
    LLM_MODEL = _first("LLM_MODEL", "OPENAI_MODEL", "GEN_MODEL", default="deepseek-v4.1-flash")
    EMB_MODEL = _first("EMB_MODEL", "EMBED_MODEL", default="BAAI/bge-m3")
    RERANKER_MODEL = _first("RERANKER_MODEL", default="Qwen3 Reranker 8B")
    RERANKER_TOP_N = _as_int(_first("RERANKER_TOP_N"), 8)

    DATA_DIR = _first("DATA_DIR", default="data")
    KB_PATH = _first("KB_PATH", default=os.path.join(DATA_DIR, "knowledge-base"))
    KB_ZIP = os.path.join(DATA_DIR, "knowledge-base.zip")
    QUESTIONS_FILE = os.path.join(DATA_DIR, "questions.csv")
    OUTPUT_FILE = "submission.csv"

    TEMPERATURE = _as_float(_first("TEMPERATURE"), 0.0)
    MAX_TOKENS = _as_int(_first("MAX_TOKENS"), 2000)
    MAX_WORKERS = _as_int(_first("MAX_WORKERS"), 4)
    TOP_K = _as_int(_first("TOP_K"), 25)
    CHUNKER = _first("CHUNKER")

    CHUNK_SIZE = 1200
    CHUNK_OVERLAP = 150
    TOP_K_FINAL = RERANKER_TOP_N
    REQUEST_TIMEOUT = 90.0

    EMB_FILE = os.path.join(ROOT_DIR, "embeddings.npy")
    CHUNKS_FILE = os.path.join(ROOT_DIR, "chunks.json")

    @classmethod
    def summary(cls):
        return {
            "BASE_URL": cls.BASE_URL,
            "LLM_MODEL": cls.LLM_MODEL,
            "EMB_MODEL": cls.EMB_MODEL,
            "DATA_DIR": cls.DATA_DIR,
            "KB_PATH": cls.KB_PATH,
            "TOP_K": cls.TOP_K,
            "TOP_K_FINAL": cls.TOP_K_FINAL,
            "MAX_WORKERS": cls.MAX_WORKERS,
            "TEMPERATURE": cls.TEMPERATURE,
            "MAX_TOKENS": cls.MAX_TOKENS,
            "API_KEY_set": bool(cls.API_KEY and cls.API_KEY != "EMPTY"),
        }