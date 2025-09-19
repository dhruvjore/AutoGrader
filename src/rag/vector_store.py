from dataclasses import dataclass
from typing import List, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pickle
from pathlib import Path

@dataclass
class IndexedCorpus:
    vectorizer: TfidfVectorizer
    matrix: any  # scipy sparse
    ids: List[str]
    texts: List[str]

class TfidfStore:
    def __init__(self, persist_path: str = "data/grades/tfidf_store.pkl"):
        self.persist_path = Path(persist_path)
        self.idx: IndexedCorpus | None = None

    def build(self, pairs: List[Tuple[str, str]]):
        if not pairs:
            self.idx = None
            return
        ids, texts = zip(*pairs)
        vec = TfidfVectorizer(ngram_range=(1, 2), max_features=50_000, stop_words="english")
        X = vec.fit_transform(list(texts))
        self.idx = IndexedCorpus(vec, X, list(ids), list(texts))

    def save(self):
        if not self.idx:
            return
        self.persist_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.persist_path, "wb") as f:
            pickle.dump(self.idx, f)

    def load(self):
        if self.persist_path.exists():
            with open(self.persist_path, "rb") as f:
                self.idx = pickle.load(f)

    def search(self, query: str, k: int = 5) -> List[Tuple[str, str, float]]:
        if not self.idx:
            return []
        qv = self.idx.vectorizer.transform([query])
        sims = cosine_similarity(qv, self.idx.matrix).ravel()
        order = sims.argsort()[::-1][:k]
        return [(self.idx.ids[i], self.idx.texts[i], float(sims[i])) for i in order]
