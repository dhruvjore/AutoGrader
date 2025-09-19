from pathlib import Path
from ..rag.pdf_utils import extract_pdf_pages

def read_text_any(path: str) -> str:
    p = Path(path)
    if p.suffix.lower() == ".pdf":
        pages = extract_pdf_pages(str(p))
        return "\n".join(pg["text"] or "" for pg in pages)
    return p.read_text(encoding="utf-8", errors="ignore")
