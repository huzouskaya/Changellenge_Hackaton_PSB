import os
from pathlib import Path
from pypdf import PdfReader
from docx import Document
from bs4 import BeautifulSoup

class Loader:
    def __init__(self, base_path):
        self.base_path = Path(base_path)

    def load(self):
        docs = []
        if not self.base_path.exists():
            return docs
        for file_path in self.base_path.rglob("*"):
            if not file_path.is_file():
                continue
            try:
                if file_path.suffix.lower() == '.pdf':
                    docs.extend(self._load_pdf(file_path))
                elif file_path.suffix.lower() == '.docx':
                    docs.extend(self._load_docx(file_path))
                elif file_path.suffix.lower() == '.html':
                    docs.extend(self._load_html(file_path))
                elif file_path.suffix.lower() == '.txt':
                    docs.extend(self._load_txt(file_path))
            except Exception:
                pass
        return docs

    def _load_pdf(self, path):
        docs = []
        reader = PdfReader(path)
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text and text.strip():
                docs.append({"text": text, "meta": {"source": str(path), "page": i + 1}})
        return docs

    def _load_docx(self, path):
        doc = Document(path)
        text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
        if text:
            return [{"text": text, "meta": {"source": str(path)}}]
        return []

    def _load_html(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'lxml')
            text = soup.get_text(separator='\n', strip=True)
        if text:
            return [{"text": text, "meta": {"source": str(path)}}]
        return []

    def _load_txt(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            text = f.read()
        if text and text.strip():
            return [{"text": text, "meta": {"source": str(path)}}]
        return []