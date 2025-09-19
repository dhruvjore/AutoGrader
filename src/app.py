# app.py  — Streamlit front-end for instant grading on upload
import io
import os
from pathlib import Path
from typing import List, Dict

import streamlit as st

# Your modules
from src.config import (
    BASE_DATA_DIR, RUBRICS_DIR, QUESTIONS_DIR, STUDENT_SUBMISSIONS_DIR,
    REPORTS_DIR, GRADED_COPIES_DIR
)
from src.grader.grade_evaluator import GradeEvaluator
from src.utils.read_any import read_text_any
from src.reporting import (
    generate_markdown_report, generate_json_report,
    save_report_markdown, save_report_json,
    build_appendix_text, create_graded_copy_from_pdf, create_graded_copy_from_text
)

# Ensure dirs exist
for d in [Path(BASE_DATA_DIR), Path(RUBRICS_DIR), Path(QUESTIONS_DIR), Path(STUDENT_SUBMISSIONS_DIR), REPORTS_DIR, GRADED_COPIES_DIR]:
    Path(d).mkdir(parents=True, exist_ok=True)

st.set_page_config(page_title="Assignment Grader", layout="wide")
st.title("Assignment Grader — RAG + Groq")

# ---------- Helpers ----------
def save_uploaded_file(folder: Path, file) -> Path:
    out_path = folder / file.name
    with open(out_path, "wb") as f:
        f.write(file.getbuffer())
    return out_path

def list_files(folder: Path, exts={".pdf", ".txt", ".md", ".json"}) -> List[Path]:
    return sorted([p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in exts], key=lambda p: p.name.lower())

@st.cache_resource(show_spinner=False)
def get_evaluator() -> GradeEvaluator:
    return GradeEvaluator()

def grade_single_submission(
    sub_path: Path,
    rubric_name: str,
    question_name: str,
):
    grader = get_evaluator()

    student_text = read_text_any(str(sub_path))

    submission_meta = {
        "student_name": sub_path.stem,  # adjust if you parse names differently
        "filename": sub_path.name,
        "submitted_at": None,
        "rubric_text": "",
        "student_text": student_text
    }

    out = grader.grade(
        student_text,
        assignment_hint=f"Use rubric {rubric_name} and question {question_name}",
        rubric_allowlist=[rubric_name],
        question_allowlist=[question_name],
    )

    # Build GradeResult for reporting
    retrieved_lines = []
    for r in out["retrieved"]:
        p = r.get("path", "?")
        pg = r.get("page", None)
        sc = r.get("score", 0.0)
        loc = f"{p}" + (f":p{pg}" if pg else "")
        retrieved_lines.append(f"[{sc:.4f}] {loc}")

    # Use GradeEvaluator helper to normalize
    grade_result = grader.to_grade_result(out["result"], retrieved_lines)

    # Persist reports
    # Use a deterministic id per file by hashing name; or just increment.
    # Simple approach: use index-like suffix from count of existing report_*.json
    existing_jsons = list(REPORTS_DIR.glob("report_*.json"))
    new_id = (len(existing_jsons) + 1)

    json_str = generate_json_report(submission_meta, grade_result)
    json_path = save_report_json(new_id, json_str)

    md_path = None
    md = generate_markdown_report(submission_meta, grade_result)
    md_path = save_report_markdown(new_id, md)

    # Graded copy
    appendix = build_appendix_text(submission_meta, grade_result, out["retrieved"])
    graded_name = sub_path.stem + "__GRADED" + sub_path.suffix
    graded_out = GRADED_COPIES_DIR / graded_name

    if sub_path.suffix.lower() == ".pdf":
        create_graded_copy_from_pdf(sub_path, appendix, graded_out)
    else:
        create_graded_copy_from_text(sub_path, appendix, graded_out.with_suffix(sub_path.suffix))

    return {
        "score": grade_result.score,
        "letter": grade_result.grade,
        "feedback": grade_result.feedback,
        "json": json_path,
        "md": md_path,
        "graded_copy": graded_out,
        "retrieved": out["retrieved"],
    }

# ---------- Sidebar: Uploads ----------
with st.sidebar:
    st.header("Upload & Manage")

    st.subheader("Rubric")
    r_file = st.file_uploader("Upload rubric", type=["pdf", "txt", "md", "json"], key="rubric_up")
    if r_file is not None:
        saved = save_uploaded_file(Path(RUBRICS_DIR), r_file)
        st.success(f"Rubric saved: {saved.name}")

    st.subheader("Question")
    q_file = st.file_uploader("Upload question", type=["pdf", "txt", "md"], key="question_up")
    if q_file is not None:
        saved = save_uploaded_file(Path(QUESTIONS_DIR), q_file)
        st.success(f"Question saved: {saved.name}")

    st.subheader("Student Submissions")
    s_files = st.file_uploader("Upload one or more", type=["pdf", "txt", "md"], accept_multiple_files=True, key="subs_up")
    auto_grade = st.checkbox("Auto-grade on upload (if rubric & question selected)", value=True)

    if s_files:
        saved_paths = []
        for f in s_files:
            saved_paths.append(save_uploaded_file(Path(STUDENT_SUBMISSIONS_DIR), f))
        st.success(f"Saved {len(saved_paths)} student file(s).")
        st.session_state["newly_uploaded_submissions"] = [str(p) for p in saved_paths]
    else:
        st.session_state.pop("newly_uploaded_submissions", None)

# ---------- Main: Selection + Grading ----------
col1, col2, col3 = st.columns([1.2, 1.2, 1.0])

with col1:
    st.subheader("Select Rubric")
    rubric_files = list_files(Path(RUBRICS_DIR))
    rubric_names = [p.name for p in rubric_files]
    rubric_sel = st.selectbox("Rubric file", rubric_names, index=0 if rubric_names else None, placeholder="Upload a rubric")

with col2:
    st.subheader("Select Question")
    question_files = list_files(Path(QUESTIONS_DIR))
    question_names = [p.name for p in question_files]
    question_sel = st.selectbox("Question file", question_names, index=0 if question_names else None, placeholder="Upload a question")

with col3:
    st.subheader("Actions")
    run_btn = st.button("Grade all current submissions")

st.divider()

# Show current submissions
sub_files = list_files(Path(STUDENT_SUBMISSIONS_DIR))
st.write(f"**Current submissions:** {len(sub_files)}")
if sub_files:
    st.dataframe(
        {"filename": [p.name for p in sub_files]},
        hide_index=True,
        use_container_width=True,
    )

def render_result_row(fname: str, result: Dict):
    st.markdown(f"### {fname}")
    cols = st.columns([0.8, 0.6, 2.0])
    with cols[0]:
        st.metric("Score", f"{result['score']:.1f}" if result['score'] is not None else "N/A")
        st.write(f"**Grade:** {result['letter'] or 'N/A'}")
    with cols[1]:
        if result.get("json"):
            st.download_button("Download JSON", data=Path(result["json"]).read_bytes(), file_name=Path(result["json"]).name, mime="application/json")
        if result.get("md"):
            st.download_button("Download Markdown", data=Path(result["md"]).read_bytes(), file_name=Path(result["md"]).name, mime="text/markdown")
        if result.get("graded_copy") and Path(result["graded_copy"]).exists():
            gc = Path(result["graded_copy"])
            st.download_button("Download Graded Copy", data=gc.read_bytes(), file_name=gc.name, mime="application/pdf" if gc.suffix.lower()==".pdf" else "text/plain")
    with cols[2]:
        st.write("**Feedback**")
        st.write(result["feedback"] or "(none)")
        with st.expander("Retrieved context (top hits)"):
            if result.get("retrieved"):
                for r in result["retrieved"]:
                    path = r.get("path","?")
                    page = r.get("page", None)
                    score = r.get("score", 0.0)
                    st.write(f"- [{score:.4f}] {path}" + (f":p{page}" if page else ""))
            else:
                st.write("(none)")

results_section = st.container()

def do_grading_for_paths(paths: List[Path]):
    rubric_ready = rubric_sel is not None and rubric_sel != ""
    question_ready = question_sel is not None and question_sel != ""
    if not (rubric_ready and question_ready):
        st.warning("Please select a rubric and a question before grading.")
        return

    with st.spinner("Grading in progress..."):
        for p in paths:
            res = grade_single_submission(
                sub_path=p,
                rubric_name=rubric_sel,
                question_name=question_sel,
            )
            with results_section:
                render_result_row(p.name, res)

# Auto-grade immediately for newly uploaded files (if option checked)
if auto_grade and st.session_state.get("newly_uploaded_submissions") and rubric_sel and question_sel:
    new_paths = [Path(p) for p in st.session_state["newly_uploaded_submissions"]]
    do_grading_for_paths(new_paths)
    # Clear them so we don’t re-grade on every rerun
    st.session_state.pop("newly_uploaded_submissions", None)

# Manual run button: grade everything currently in folder
if run_btn:
    do_grading_for_paths(sub_files)
