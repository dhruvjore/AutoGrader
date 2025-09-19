import argparse
from pathlib import Path
from typing import List
from src.config import RUBRICS_DIR, QUESTIONS_DIR, STUDENT_SUBMISSIONS_DIR, REPORTS_DIR
from src.utils.file_select import list_files, pick_one, pick_many
from src.utils.read_any import read_text_any
from src.grader.grade_evaluator import GradeEvaluator

def filenames_only(paths: List[str]) -> List[str]:
    return [Path(p).name for p in paths]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rubric", default="", help="Rubric filename (inside data/rubrics). If omitted, interactive select.")
    parser.add_argument("--question", default="", help="Question filename (inside data/questions). If omitted, interactive select.")
    parser.add_argument("--subs", default="", help="Comma-separated submission filenames (inside data/student_submission), or omit for interactive multi-select.")
    parser.add_argument("--print_only", action="store_true", help="Only print results to console.")
    args = parser.parse_args()

    rubrics = list_files(RUBRICS_DIR)
    questions = list_files(QUESTIONS_DIR)
    submissions = list_files(STUDENT_SUBMISSIONS_DIR)

    # Select rubric
    rubric_path = ""
    if args.rubric:
        rubric_path = str(Path(RUBRICS_DIR) / args.rubric)
        if rubric_path not in rubrics:
            # try fallback by name match
            matches = [r for r in rubrics if Path(r).name.lower() == args.rubric.lower()]
            if not matches:
                raise FileNotFoundError(f"Rubric not found: {args.rubric}")
            rubric_path = matches[0]
    else:
        rubric_path = pick_one(rubrics, prompt="Select a rubric")

    # Select question
    question_path = ""
    if args.question:
        question_path = str(Path(QUESTIONS_DIR) / args.question)
        if question_path not in questions:
            matches = [q for q in questions if Path(q).name.lower() == args.question.lower()]
            if not matches:
                raise FileNotFoundError(f"Question not found: {args.question}")
            question_path = matches[0]
    else:
        question_path = pick_one(questions, prompt="Select a question")

    # Select submissions
    if args.subs:
        wanted = [s.strip() for s in args.subs.split(",") if s.strip()]
        chosen_subs = []
        for w in wanted:
            p = str(Path(STUDENT_SUBMISSIONS_DIR) / w)
            if p in submissions:
                chosen_subs.append(p)
                continue
            # fallback exact-name match
            matches = [s for s in submissions if Path(s).name.lower() == w.lower()]
            if not matches:
                raise FileNotFoundError(f"Submission not found: {w}")
            chosen_subs.append(matches[0])
    else:
        chosen_subs = pick_many(submissions, prompt="Select student submissions")

    rubric_name = Path(rubric_path).name
    question_name = Path(question_path).name

    # Build allowlists to force RAG to those files
    rubric_allow = [rubric_name]
    question_allow = [question_name]

    grader = GradeEvaluator()

    for sub_path in chosen_subs:
        student_text = read_text_any(sub_path)
        out = grader.grade(
            student_text,
            assignment_hint=f"Use rubric {rubric_name} and question {question_name}",
            rubric_allowlist=rubric_allow,
            question_allowlist=question_allow,
        )

        # Save or print
        base = Path(sub_path).stem
        json_out = Path(REPORTS_DIR) / f"{base}__grade.json"
        json_out.write_text(
            # keep raw + result for traceability
            __import__("json").dumps(out, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        if args.print_only:
            print(f"\n=== {Path(sub_path).name} ===")
            print(f"Score: {out['result'].get('total_score', 0)}")
            for c in out["result"].get("criteria", []):
                print(f"- {c.get('name','?')}: {c.get('score',0)}")
            print(out["result"].get("overall_feedback",""))
        else:
            print(f"Wrote {json_out}")

if __name__ == "__main__":
    main()
