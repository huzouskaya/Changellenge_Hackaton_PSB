from openai import OpenAI
from src.config import Config

class LLMClient:
    def __init__(self):
        self.client = OpenAI(
            api_key=Config.API_KEY,
            base_url=Config.BASE_URL,
            timeout=Config.REQUEST_TIMEOUT,
            max_retries=2,
        )

    def chat(self, messages, temperature=0.1, max_tokens=2000):
        response = self.client.chat.completions.create(
            model=Config.LLM_MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""

    def embed(self, texts):
        response = self.client.embeddings.create(
            model=Config.EMBED_MODEL,
            input=texts,
        )
        return [item.embedding for item in response.data]