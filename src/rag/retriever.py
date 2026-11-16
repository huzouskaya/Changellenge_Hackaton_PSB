from indexer import Indexer
from src.llm.client import LLMClient

class Retriever:
    def __init__(self):
        self.indexer = Indexer()
        self.client = LLMClient()
        self.ready = self.indexer.load()

    def get_context(self, query):
        if not self.ready:
            return []
        return self.indexer.search(query, self.client.embed)