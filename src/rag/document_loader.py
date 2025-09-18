# document_loader.py

from pathlib import Path
from typing import List, Tuple
import re

# Optional imports for richer formats
try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None

try:
    import docx
except Exception:
    docx = None


def _chunk_text(text: str, chunk_size: int = 800, overlap: int = 120) -> List[str]:
    text = re.sub(r"\s+", " ", text).strip()
    chunks = []
    i = 0
    while i < len(text):
        chunk = text[i:i+chunk_size]
        chunks.append(chunk)
        i += chunk_size - overlap
    return [c for c in chunks if c]


def load_file(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".txt":
        return path.read_text(encoding="utf-8", errors="ignore")
    if suffix in [".pdf"] and PdfReader is not None:
        text = []
        reader = PdfReader(str(path))
        for page in reader.pages:
            text.append(page.extract_text() or "")
        return "\n".join(text)
    if suffix in [".docx"] and docx is not None:
        d = docx.Document(str(path))
        return "\n".join(p.text for p in d.paragraphs)
    # Fallback: treat as text
    return path.read_text(encoding="utf-8", errors="ignore")


def load_corpus(
    roots: List[Path],
    glob_patterns: Tuple[str, ...] = ("*.txt", "*.pdf", "*.docx"),
    chunk_size: int = 800,
    overlap: int = 120,
) -> List[Tuple[str, str]]:
    """
    Returns list of (doc_id, chunk_text)
    doc_id is "<relative_path>::chunk_<n>"
    """
    all_chunks: List[Tuple[str, str]] = []
    for root in roots:
        root = Path(root)
        for pattern in glob_patterns:
            for f in root.rglob(pattern):
                try:
                    raw = load_file(f)
                    chunks = _chunk_text(raw, chunk_size, overlap)
                    for n, ch in enumerate(chunks):
                        doc_id = f"{f.as_posix()}::chunk_{n}"
                        all_chunks.append((doc_id, ch))
                except Exception:
                    # be resilient
                    continue
    return all_chunks
