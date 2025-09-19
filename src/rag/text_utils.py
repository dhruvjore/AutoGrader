import re
from typing import List

def clean(text: str) -> str:
    if not text:
        return ""
    text = text.replace("\u00a0", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text

def chunk_text(text: str, chunk_size: int = 1200, overlap: int = 200) -> List[str]:
    text = clean(text)
    if len(text) <= chunk_size:
        return [text]
    chunks, i = [], 0
    step = max(1, chunk_size - overlap)
    while i < len(text):
        chunks.append(text[i:i+chunk_size])
        i += step
    return chunks
