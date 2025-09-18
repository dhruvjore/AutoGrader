# retriever.py
from typing import List, Tuple
from pathlib import Path
from .document_loader import load_corpus
from .vector_store import TfidfStore


class Retriever:
    def __init__(self, persist_path: str = "data/grades/tfidf_store.pkl"):
        self.store = TfidfStore(persist_path=persist_path)

    def index_dirs(self, roots: List[str]) -> int:
        pairs = load_corpus([Path(r) for r in roots])
        self.store.build(pairs)
        self.store.save()
        return len(pairs)

    def load(self):
        self.store.load()

    def retrieve(self, query: str, k: int = 5) -> List[Tuple[str, str, float]]:
        return self.store.search(query, k=k)
