from pathlib import Path
from typing import List

ALLOWED = {".pdf", ".txt", ".md"}

def list_files(folder: str) -> List[str]:
    base = Path(folder)
    if not base.exists():
        return []
    files = [str(p) for p in base.iterdir() if p.is_file() and p.suffix.lower() in ALLOWED]
    files.sort()
    return files

def pick_one(files: List[str], prompt: str) -> str:
    if not files:
        raise ValueError("No files found.")
    print(f"\n{prompt}\n")
    for i, f in enumerate(files, start=1):
        print(f"[{i}] {Path(f).name}")
    sel = input("Enter number: ").strip()
    idx = int(sel) - 1
    if idx < 0 or idx >= len(files):
        raise ValueError("Invalid selection")
    return files[idx]

def pick_many(files: List[str], prompt: str) -> List[str]:
    if not files:
        raise ValueError("No files found.")
    print(f"\n{prompt}\n")
    for i, f in enumerate(files, start=1):
        print(f"[{i}] {Path(f).name}")
    sel = input("Enter numbers (comma-separated) or 'all': ").strip().lower()
    if sel == "all":
        return files
    idxs = []
    for tok in sel.split(","):
        tok = tok.strip()
        if not tok:
            continue
        idx = int(tok) - 1
        if idx < 0 or idx >= len(files):
            raise ValueError(f"Invalid selection: {tok}")
        idxs.append(idx)
    return [files[i] for i in idxs]
