import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    API_KEY = (
        os.getenv("LLM_API_KEY")
        or os.getenv("OPENAI_API_KEY")
        or os.getenv("API_KEY")
        or "EMPTY"
    )
    BASE_URL = (
        os.getenv("LLM_BASE_URL")
        or os.getenv("OPENAI_BASE_URL")
        or "http://localhost:8000/v1"
    )
    LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-v4.1-flash")
    EMBED_MODEL = os.getenv("EMBED_MODEL", "BAAI/bge-m3")
    KB_PATH = os.getenv("KB_PATH", "./data/knowledge-base")
    INDEX_PATH = os.getenv("INDEX_PATH", "./data/index")
    CHUNK_SIZE = 800
    CHUNK_OVERLAP = 100
    TOP_K_RETRIEVE = 15
    TOP_K_FINAL = 5
    REQUEST_TIMEOUT = 90.0
    MAX_WORKERS = 8