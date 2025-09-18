# test_rag_pipeline.py
from pathlib import Path
from src.rag.retriever import Retriever

SAMP_DIR = Path("data") / "rubrics"
SAMP_DIR.mkdir(parents=True, exist_ok=True)

def _write_sample():
    (SAMP_DIR / "grading_criteria.txt").write_text(
        "Students should explain gradient descent, learning rate, convergence, and loss.", encoding="utf-8"
    )
    ex_dir = Path("data") / "student_submissions"
    ex_dir.mkdir(parents=True, exist_ok=True)
    (ex_dir / "excellent_answer.txt").write_text(
        "This essay explains gradient descent, step size (learning rate), and convergence behavior of the loss.",
        encoding="utf-8"
    )

def test_build_and_search():
    _write_sample()
    r = Retriever(persist_path="data/grades/test_store.pkl")
    total = r.index_dirs(["data/rubrics", "data/student_submissions"])
    assert total > 0
    r.load()
    hits = r.retrieve("gradient descent and learning rate", k=3)
    assert len(hits) > 0
    # Top result should talk about gradient descent
    joined = " ".join(h[1] for h in hits).lower()
    assert "gradient descent" in joined
