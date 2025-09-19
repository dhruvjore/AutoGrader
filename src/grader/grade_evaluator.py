from dataclasses import dataclass
from typing import Dict, List, Tuple
import re
from ..rag.retriever import Retriever

def keyword_score(student_text: str, rubric_text: str, context_snippets: List[str]) -> Tuple[float, Dict]:
    """
    Scores 0..1 by overlapping informative tokens between student and rubric+context.
    """
    def toks(s: str) -> set:
        s = s.lower()
        s = re.sub(r"[^a-z0-9\s]", " ", s)
        words = [w for w in s.split() if len(w) > 3]
        return set(words)

    stu = toks(student_text)
    rub = toks(rubric_text + " " + " ".join(context_snippets))
    if not stu or not rub:
        return 0.0, {"common": [], "total_terms": len(rub)}
    common = stu.intersection(rub)
    score = len(common) / max(1, len(rub))
    return score, {"common": sorted(list(common))[:20], "total_terms": len(rub)}

def numeric_to_letter(x: float) -> str:
    if x >= 0.85: return "A"
    if x >= 0.75: return "A-"
    if x >= 0.65: return "B+"
    if x >= 0.55: return "B"
    if x >= 0.45: return "B-"
    if x >= 0.35: return "C+"
    if x >= 0.25: return "C"
    return "D"

@dataclass
class GradeResult:
    grade: str
    score: float
    feedback: str
    evidence: List[str]

class GradeEvaluator:
    """
    RAG-driven evaluator (retrieves k chunks, then judges).
    """
    def __init__(self, retriever: Retriever, judge_fn=keyword_score, k: int = 5):
        self.retriever = retriever
        self.judge_fn = judge_fn
        self.k = k

    def evaluate(self, student_text: str, rubric_text: str) -> GradeResult:
        hits = self.retriever.retrieve(student_text, k=self.k)
        context_snips = [t for (_id, t, _s) in hits]
        score, meta = self.judge_fn(student_text, rubric_text, context_snips)
        letter = numeric_to_letter(score)
        feedback = (
            f"Auto-graded using RAG baseline.\n"
            f"- Matched {len(meta.get('common', []))} key terms "
            f"against rubric/context ({meta.get('total_terms')} terms).\n"
            f"- Retrieval used top-{self.k} chunks.\n"
            f"Consider expanding explanations where missing."
        )
        evidence = [f"{doc_id} (sim={sim:.3f})" for (doc_id, _t, sim) in hits]
        return GradeResult(grade=letter, score=score, feedback=feedback, evidence=evidence)
