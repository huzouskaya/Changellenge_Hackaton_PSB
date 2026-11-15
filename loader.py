from pathlib import Path
from docx import Document
from pypdf import PdfReader
from bs4 import BeautifulSoup

def load_documents(kb_path):
    docs = []
    kb_path = Path(kb_path)
    if not kb_path.exists():
        return docs
    for file_path in kb_path.rglob("*"):
        if not file_path.is_file():
            continue
        try:
            if file_path.suffix.lower() == '.pdf':
                reader = PdfReader(file_path)
                for i, page in enumerate(reader.pages):
                    text = page.extract_text()
                    if text and text.strip():
                        docs.append({"text": text, "meta": {"source": file_path.name, "page": i + 1}})
            elif file_path.suffix.lower() == '.docx':
                doc = Document(file_path)
                if text := "\n".join([p.text for p in doc.paragraphs if p.text.strip()]):
                    docs.append({"text": text, "meta": {"source": file_path.name}})
            elif file_path.suffix.lower() == '.html':
                with open(file_path, 'r', encoding='utf-8') as f:
                    soup = BeautifulSoup(f.read(), 'lxml')
                    text = soup.get_text(separator='\n', strip=True)
                if text:
                    docs.append({"text": text, "meta": {"source": file_path.name}})
            elif file_path.suffix.lower() == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
                if text and text.strip():
                    docs.append({"text": text, "meta": {"source": file_path.name}})
        except:
            pass
    return docs