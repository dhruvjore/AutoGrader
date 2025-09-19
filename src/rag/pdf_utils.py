from typing import List, Dict
from pypdf import PdfReader

def extract_pdf_pages(path: str) -> List[Dict]:
    """
    Returns a list of dicts: [{"page_index": int, "text": str}]
    """
    pages = []
    reader = PdfReader(path)
    for i, page in enumerate(reader.pages):
        try:
            txt = page.extract_text() or ""
        except Exception:
            txt = ""
        pages.append({"page_index": i, "text": txt})
    return pages
