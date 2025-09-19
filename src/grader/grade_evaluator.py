# src/grader/grade_evaluator.py
import json
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field

from ..config import (
    RUBRICS_DIR, QUESTIONS_DIR, SOLUTIONS_DIR,
    CHUNK_SIZE, CHUNK_OVERLAP, TOP_K,
    GROQ_MODEL, TEMPERATURE, MAX_TOKENS, DEFAULT_RUBRIC_NAME
)
from ..rag.ingest import load_corpus
from ..rag.retriever_tfidf import TfidfRetriever
from ..llm.groq_client import GroqClient
from .prompt_templates import PROMPT_HEADER, PROMPT_CONTEXT_BLOCK, PROMPT_USER_BLOCK


@dataclass
class GradeResult:
    grade: str | None
    score: float | None
    feedback: str | None
    evidence: list[str] = field(default_factory=list)


def _letter_from_score(score: float) -> str:
    if score >= 93: return "A"
    if score >= 90: return "A-"
    if score >= 87: return "B+"
    if score >= 83: return "B"
    if score >= 80: return "B-"
    if score >= 77: return "C+"
    if score >= 73: return "C"
    if score >= 70: return "C-"
    if score >= 60: return "D"
    return "F"


def build_context_block(hits: List[Tuple[float, Dict[str, Any]]]) -> str:
    lines = []
    for score, doc in hits:
        path = doc.get("meta", {}).get("path", "?")
        page = doc.get("meta", {}).get("page", None)
        loc = f"{path}" + (f":p{page}" if page is not None else "")
        lines.append(f"[score={round(score, 4)}] {loc} :: {doc.get('text', '')}")
    return "\n---\n".join(lines)


def parse_json_safe(s: str) -> Dict[str, Any]:
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        start = s.find("{")
        end = s.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(s[start:end+1])
            except Exception:
                pass
        return {
            "total_score": 0.0,
            "criteria": [],
            "overall_feedback": "The grader could not parse model output as JSON.",
            "improvable_sections": [],
            "plagiarism_or_policy_flags": ["JSON_PARSE_ERROR"],
        }


class GradeEvaluator:
    def __init__(self):
        self.corpus: List[Dict[str, Any]] = load_corpus(
            RUBRICS_DIR, QUESTIONS_DIR, SOLUTIONS_DIR, CHUNK_SIZE, CHUNK_OVERLAP
        )
        self.retriever = TfidfRetriever(self.corpus)
        self.llm = GroqClient(model=GROQ_MODEL, temperature=TEMPERATURE, max_tokens=MAX_TOKENS)

    def _retrieve_by_type(
        self,
        query: str,
        rubric_allow: Optional[List[str]],
        question_allow: Optional[List[str]],
        k_each: Tuple[int, int] = (4, 2)
    ) -> List[Tuple[float, Dict[str, Any]]]:
        r_k, q_k = k_each

        def allow(match_list: Optional[List[str]], doc_path: str) -> bool:
            if not match_list:
                return True
            return any(name.lower() in doc_path.lower() for name in match_list)

        rubric_hits = self.retriever.search_filtered(
            query,
            predicate=lambda d: d.get("meta", {}).get("type") == "rubric"
                                and allow(rubric_allow, d.get("meta", {}).get("path","")),
            k=r_k
        )
        question_hits = self.retriever.search_filtered(
            query,
            predicate=lambda d: d.get("meta", {}).get("type") == "question"
                                and allow(question_allow, d.get("meta", {}).get("path","")),
            k=q_k
        )
        hits = rubric_hits + question_hits
        if not hits:
            hits = self.retriever.search(query, k=max(r_k+q_k, TOP_K))
        return hits

    def to_grade_result(self, model_result: dict, retrieved_paths: List[str]) -> GradeResult:
        score = float(model_result.get("total_score", 0) or 0)
        feedback = model_result.get("overall_feedback") or ""
        return GradeResult(
            grade=_letter_from_score(score),
            score=score,
            feedback=feedback,
            evidence=retrieved_paths,
        )

    def grade(
        self,
        submission_text: str,
        assignment_hint: Optional[str] = None,
        rubric_allowlist: Optional[List[str]] = None,
        question_allowlist: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Returns a dict with keys: raw_model_text, result, retrieved
        """
        query = assignment_hint or "grading rubric and question and answer key"
        hits = self._retrieve_by_type(query, rubric_allowlist, question_allowlist, k_each=(4, 2))

        ctx_block = build_context_block(hits)

        system_msg = {"role": "system", "content": PROMPT_HEADER}
        user_msg = {
            "role": "user",
            "content": (
                PROMPT_CONTEXT_BLOCK.format(
                    context=ctx_block,
                    rubric="[see rubric chunks above]"
                )
                + "\n\n"
                + PROMPT_USER_BLOCK.format(submission=submission_text)
            ),
        }

        raw = self.llm.chat([system_msg, user_msg])
        result = parse_json_safe(raw)

        try:
            result["total_score"] = float(max(0.0, min(100.0, result.get("total_score", 0.0))))
            for c in result.get("criteria", []):
                c["score"] = float(max(0.0, min(100.0, float(c.get("score", 0.0)))))
        except Exception:
            pass

        retrieved_meta = [
            {
                "score": float(s),
                "path": d.get("meta", {}).get("path"),
                "type": d.get("meta", {}).get("type"),
                "page": d.get("meta", {}).get("page"),
            }
            for s, d in hits
        ]

        return {
            "raw_model_text": raw,
            "result": result,
            "retrieved": retrieved_meta,
        }
