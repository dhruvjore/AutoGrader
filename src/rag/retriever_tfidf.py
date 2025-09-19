from typing import List, Dict, Tuple, Callable, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

Doc = Dict[str, Any]

class TfidfRetriever:
    def __init__(self, docs: List[Doc]):
        self.docs = docs
        self.texts = [d["text"] for d in docs]
        self.vectorizer = TfidfVectorizer(
            strip_accents="unicode",
            lowercase=True,
            stop_words="english",
            ngram_range=(1, 2),
            max_features=100_000,
        )
        self.matrix = self.vectorizer.fit_transform(self.texts)

    def search(self, query: str, k: int = 6) -> List[Tuple[float, Doc]]:
        q_vec = self.vectorizer.transform([query])
        sims = cosine_similarity(q_vec, self.matrix)[0]
        idx = sims.argsort()[::-1][:k]
        return [(float(sims[i]), self.docs[i]) for i in idx]

    def search_filtered(self, query: str, predicate: Callable[[Doc], bool], k: int) -> List[Tuple[float, Doc]]:
        q_vec = self.vectorizer.transform([query])
        sims = cosine_similarity(q_vec, self.matrix)[0]
        ranked = sorted(
            [(float(s), self.docs[i]) for i, s in enumerate(sims) if predicate(self.docs[i])],
            key=lambda x: x[0],
            reverse=True,
        )
        return ranked[:k]
