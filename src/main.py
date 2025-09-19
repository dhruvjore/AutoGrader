import argparse
from pathlib import Path
from typing import List
from src.config import (
    RUBRICS_DIR, QUESTIONS_DIR, STUDENT_SUBMISSIONS_DIR,
    REPORTS_DIR, GRADED_COPIES_DIR
)
from src.utils.file_select import list_files, pick_one, pick_many
from src.utils.read_any import read_text_any
from src.grader.grade_evaluator import GradeEvaluator
from src.reporting import (
    generate_markdown_report, generate_json_report,
    save_report_markdown, save_report_json,
    build_appendix_text, create_graded_copy_from_pdf, create_graded_copy_from_text
)

def filenames_only(paths: List[str]) -> List[str]:
    return [Path(p).name for p in paths]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rubric", default="", help="Rubric filename (inside data/rubrics). If omitted, interactive select.")
    parser.add_argument("--question", default="", help="Question filename (inside data/questions). If omitted, interactive select.")
    parser.add_argument("--subs", default="", help="Comma-separated submission filenames (inside data/student_submission), or omit for interactive multi-select.")
    parser.add_argument("--print_only", action="store_true", help="Only print results to console (still writes graded copy).")
    parser.add_argument("--no_markdown", action="store_true", help="Skip markdown report generation.")
    args = parser.parse_args()

    rubrics = list_files(RUBRICS_DIR)
    questions = list_files(QUESTIONS_DIR)
    submissions = list_files(STUDENT_SUBMISSIONS_DIR)

    # Select rubric
    if args.rubric:
        rubric_path = next((r for r in rubrics if Path(r).name.lower() == args.rubric.lower()), None)
        if not rubric_path:
            raise FileNotFoundError(f"Rubric not found: {args.rubric}")
    else:
        rubric_path = pick_one(rubrics, prompt="Select a rubric")

    # Select question
    if args.question:
        question_path = next((q for q in questions if Path(q).name.lower() == args.question.lower()), None)
        if not question_path:
            raise FileNotFoundError(f"Question not found: {args.question}")
    else:
        question_path = pick_one(questions, prompt="Select a question")

    # Select submissions
    if args.subs:
        wanted = [s.strip() for s in args.subs.split(",") if s.strip()]
        chosen_subs = []
        for w in wanted:
            match = next((s for s in submissions if Path(s).name.lower() == w.lower()), None)
            if not match:
                raise FileNotFoundError(f"Submission not found: {w}")
            chosen_subs.append(match)
    else:
        chosen_subs = pick_many(submissions, prompt="Select student submissions")

    rubric_name = Path(rubric_path).name
    question_name = Path(question_path).name

    rubric_allow = [rubric_name]
    question_allow = [question_name]

    grader = GradeEvaluator()

    for idx, sub_path in enumerate(chosen_subs, start=1):
        sub_p = Path(sub_path)
        student_text = read_text_any(sub_path)

        submission_meta = {
            "student_name": sub_p.stem,  # adjust if you have a mapping
            "filename": sub_p.name,
            "submitted_at": None,
            "rubric_text": "",           # PDFs shown via retrieved; keep empty
            "student_text": student_text
        }

        out = grader.grade(
            student_text,
            assignment_hint=f"Use rubric {rubric_name} and question {question_name}",
            rubric_allowlist=rubric_allow,
            question_allowlist=question_allow,
        )

        # Convert to GradeResult and include evidence (paths + pages)
        retrieved_lines = []
        for r in out["retrieved"]:
            p = r.get("path", "?")
            pg = r.get("page", None)
            sc = r.get("score", 0.0)
            loc = f"{p}" + (f":p{pg}" if pg else "")
            retrieved_lines.append(f"[{sc:.4f}] {loc}")

        grade_result = grader.to_grade_result(out["result"], retrieved_lines)

        # Reports
        json_str = generate_json_report(submission_meta, grade_result)
        json_path = save_report_json(idx, json_str)

        if not args.no_markdown:
            md = generate_markdown_report(submission_meta, grade_result)
            md_path = save_report_markdown(idx, md)

        # Graded copy (appendix)
        appendix = build_appendix_text(submission_meta, grade_result, out["retrieved"])
        graded_name = sub_p.stem + "__GRADED" + sub_p.suffix
        graded_out = GRADED_COPIES_DIR / graded_name

        if sub_p.suffix.lower() == ".pdf":
            create_graded_copy_from_pdf(sub_p, appendix, graded_out)
        else:
            create_graded_copy_from_text(sub_p, appendix, graded_out.with_suffix(sub_p.suffix))

        if args.print_only:
            print(f"\n=== {sub_p.name} ===")
            print(f"Score: {grade_result.score}")
            print(f"Grade: {grade_result.grade}")
            print(grade_result.feedback or "")
        else:
            print(f"Wrote: {json_path}")
            if not args.no_markdown:
                print(f"Wrote: {md_path}")
            print(f"Wrote graded copy: {graded_out}")

if __name__ == "__main__":
    main()
