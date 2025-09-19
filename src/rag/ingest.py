from pathlib import Path
from typing import Dict, List
from .text_utils import clean, chunk_text
from .pdf_utils import extract_pdf_pages
import json

ALLOWED_EXT = {".pdf", ".txt", ".md", ".json"}

def _load_dir(folder: str, chunk_size: int, overlap: int, tag: str) -> List[Dict]:
    records: List[Dict] = []
    if not folder:
        return records
    base = Path(folder)
    if not base.exists():
        return records

    rid = 0
    for p in base.rglob("*"):
        if p.is_dir() or p.suffix.lower() not in ALLOWED_EXT:
            continue

        rel = f"{tag}/{p.name}"

        if p.suffix.lower() == ".pdf":
            try:
                pages = extract_pdf_pages(str(p))
            except Exception:
                pages = []
            for pg in pages:
                page_text = clean(pg["text"])
                if not page_text.strip():
                    records.append({
                        "id": f"{tag}-{rid}",
                        "text": "",
                        "meta": {"path": rel, "page": pg["page_index"] + 1, "type": tag, "note": "EMPTY_OR_SCANNED"}
                    })
                    rid += 1
                    continue
                for ch in chunk_text(page_text, chunk_size, overlap):
                    records.append({
                        "id": f"{tag}-{rid}",
                        "text": ch,
                        "meta": {"path": rel, "page": pg["page_index"] + 1, "type": tag}
                    })
                    rid += 1
            continue

        # text-like
        try:
            raw = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            raw = ""
        if p.suffix.lower() == ".json":
            try:
                raw = json.dumps(json.loads(raw), ensure_ascii=False, indent=2)
            except Exception:
                pass
        text = clean(raw)
        for ch in chunk_text(text, chunk_size, overlap):
            records.append({
                "id": f"{tag}-{rid}",
                "text": ch,
                "meta": {"path": rel, "type": tag}
            })
            rid += 1
    return records


def load_corpus(rubrics_dir: str, questions_dir: str, solutions_dir: str,
                chunk_size: int, overlap: int) -> List[Dict]:
    corpus: List[Dict] = []
    corpus += _load_dir(rubrics_dir, chunk_size, overlap, tag="rubric")
    corpus += _load_dir(questions_dir, chunk_size, overlap, tag="question")
    if solutions_dir:
        corpus += _load_dir(solutions_dir, chunk_size, overlap, tag="solution")
    return corpus
