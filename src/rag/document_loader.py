from pathlib import Path
from typing import List, Tuple
import re

try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None

try:
    import docx  # python-docx
except Exception:
    docx = None


def _chunk_text(text: str, chunk_size: int = 800, overlap: int = 120, min_chars: int = 120) -> List[str]:
    text = re.sub(r"\s+", " ", text).strip()
    chunks: List[str] = []
    i = 0
    L = len(text)
    step = max(1, chunk_size - overlap)
    while i < L:
        chunk = text[i:i+chunk_size]
        if len(chunk) >= min_chars:
            chunks.append(chunk)
        i += step
    return chunks


def load_file(path: Path) -> str:
    suffix = path.suffix.lower()

    if suffix == ".txt":
        try:
            return path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return ""

    if suffix == ".pdf" and PdfReader is not None:
        out = []
        try:
            reader = PdfReader(str(path))
            for p in reader.pages:
                try:
                    t = p.extract_text() or ""
                except Exception:
                    t = ""
                if t.strip():
                    out.append(t)
        except Exception:
            return ""
        return "\n".join(out)

    if suffix == ".docx" and docx is not None:
        try:
            d = docx.Document(str(path))
            return "\n".join(p.text for p in d.paragraphs if p.text)
        except Exception:
            return ""

    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def load_corpus(
    roots: List[Path],
    glob_patterns: Tuple[str, ...] = ("*.txt", "*.pdf", "*.docx"),
    chunk_size: int = 800,
    overlap: int = 120,
    min_chars: int = 120,
) -> List[Tuple[str, str]]:
    """
    Returns list of (doc_id, chunk_text)
    doc_id uses POSIX relative path + chunk id: "<relative_path>::chunk_<n>"
    """
    all_chunks: List[Tuple[str, str]] = []
    for root in roots:
        root = Path(root)
        if not root.exists():
            continue
        for pattern in glob_patterns:
            for f in root.rglob(pattern):
                if not f.is_file():
                    continue
                try:
                    raw = load_file(f)
                    if not raw.strip():
                        continue
                    chunks = _chunk_text(raw, chunk_size, overlap, min_chars)
                    if not chunks:
                        continue
                    rel = f.relative_to(root).as_posix() if f.is_relative_to(root) else f.as_posix()
                    for n, ch in enumerate(chunks):
                        doc_id = f"{rel}::chunk_{n}"
                        all_chunks.append((doc_id, ch))
                except Exception:
                    continue
    return all_chunks
