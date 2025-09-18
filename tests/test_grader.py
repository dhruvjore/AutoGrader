# test_grader.py
from src.rag.retriever import Retriever
from src.grader.grade_evaluator import GradeEvaluator

def test_grade_baseline():
    r = Retriever(persist_path="data/grades/test_store.pkl")
    r.index_dirs(["data/rubrics", "data/student_submissions"])
    r.load()
    evaluator = GradeEvaluator(retriever=r, k=3)
    student = "I describe gradient descent and the effect of the learning rate on convergence of the loss."
    rubric =  "Students should explain gradient descent, learning rate, convergence, and loss."
    res = evaluator.evaluate(student, rubric)
    assert res.grade in {"A", "A-", "B+", "B", "B-","C+","C","D"}
    assert 0.0 <= res.score <= 1.0
    assert isinstance(res.feedback, str)
    assert len(res.evidence) > 0
 