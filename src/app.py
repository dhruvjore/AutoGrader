from pathlib import Path
from dotenv import load_dotenv
import streamlit as st
import pandas as pd

from src.db import init_db, insert_submission, insert_grade, list_all_with_grades, get_submission
from src.reporting import (
    generate_markdown_report, save_report_markdown,
    generate_json_report, save_report_json,
    cleanup_old_reports,
)
from src.rag.retriever import Retriever
from src.grader.grade_evaluator import GradeEvaluator
from src.rag.document_loader import load_file

# Setup
load_dotenv()
st.set_page_config(page_title="AutoGrader RAG", page_icon="📘", layout="wide")
st.title("📘 AutoGrader — Student & Faculty Portal (RAG Baseline)")

# Ensure DB exists
init_db()

# RAG retriever
retriever = Retriever(persist_path="data/grades/tfidf_store.pkl")

with st.sidebar:
    st.header("RAG Index")
    data_roots = ["data/rubrics", "data/answer_keys", "data/student_submissions"]
    if st.button("🔁 Build / Rebuild Index"):
        total = retriever.index_dirs(data_roots)
        st.success(f"Indexed {total} chunks.")
    retriever.load()

    # Optional housekeeping
    if st.button("🧹 Cleanup old reports (30 days)"):
        removed = cleanup_old_reports(days_to_keep=30)
        st.success(f"Removed {removed} old report files.")

# Tabs
student_tab, faculty_tab = st.tabs(["👩‍🎓 Student Upload", "👨‍🏫 Faculty Portal"])

# Student Upload
with student_tab:
    st.subheader("Submit Assignment for Auto-Grading")
    colA, colB = st.columns(2)
    with colA:
        student_name = st.text_input("Student Name", value="")
        up_student = st.file_uploader("Upload Student Assignment (txt/pdf/docx)", type=["txt", "pdf", "docx"], key="stu")
    with colB:
        up_rubric = st.file_uploader("Upload Rubric / Answer Key (txt/pdf/docx)", type=["txt", "pdf", "docx"], key="rub")

    def read_uploaded(upload):
        if not upload:
            return ""
        tmp_dir = Path("data/tmp_uploads")
        tmp_dir.mkdir(parents=True, exist_ok=True)
        fp = tmp_dir / upload.name
        fp.write_bytes(upload.read())
        return load_file(fp)

    stu_text = read_uploaded(up_student)
    rub_text = read_uploaded(up_rubric)

    if stu_text:
        st.text_area("Student Preview", stu_text[:5000], height=200)
    if rub_text:
        st.text_area("Rubric Preview", rub_text[:5000], height=200)

    can_submit = bool(student_name and up_student and up_rubric)
    if st.button("⚖️ Submit & Grade", type="primary", disabled=not can_submit):
        uploads_dir = Path("data/uploads")
        uploads_dir.mkdir(parents=True, exist_ok=True)
        student_file_path = uploads_dir / up_student.name
        up_student.seek(0)
        student_file_path.write_bytes(up_student.read())

        sub_id = insert_submission(
            student_name=student_name,
            filename=up_student.name,
            file_path=str(student_file_path),
            student_text=stu_text,
            rubric_text=rub_text,
        )

        evaluator = GradeEvaluator(retriever=retriever, k=5)
        result = evaluator.evaluate(stu_text, rub_text)

        md = generate_markdown_report(get_submission(sub_id), result)
        md_path = save_report_markdown(sub_id, md)

        json_payload = generate_json_report(get_submission(sub_id), result)
        json_path = save_report_json(sub_id, json_payload)

        insert_grade(
            submission_id=sub_id,
            score=result.score,
            letter=result.grade,
            feedback=result.feedback,
            evidence="\n".join(result.evidence),
            report_path=str(md_path),
        )

        st.success(f"Graded! Submission ID: {sub_id} — Grade: {result.grade} ({result.score:.3f})")
        st.download_button("⬇️ Download Report (Markdown)", data=md.encode("utf-8"),
                           file_name=f"report_{sub_id}.md", mime="text/markdown")
        st.download_button("⬇️ Download Report (JSON)", data=json_payload.encode("utf-8"),
                           file_name=f"report_{sub_id}.json", mime="application/json")

# Faculty Portal
with faculty_tab:
    st.subheader("Submissions & Grades")
    rows = list_all_with_grades()
    if not rows:
        st.info("No submissions yet.")
    else:
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

        ids = [r["id"] for r in rows]
        sel = st.selectbox("Select Submission ID", ids)
        sub = get_submission(int(sel))
        if sub:
            st.markdown(f"**Student:** {sub['student_name']}  ")
            st.markdown(f"**File:** {sub['filename']}")
            st.markdown(f"**Submitted (UTC):** {sub['submitted_at']}")

            joined = next((r for r in rows if r["id"] == int(sel)), None)
            if joined and joined.get("score") is not None:
                st.markdown(f"**Grade:** {joined['letter']} ({joined['score']:.3f})")
                rp = joined.get("report_path")
                if rp and Path(rp).exists():
                    md = Path(rp).read_text(encoding="utf-8")
                    st.download_button("⬇️ Download Report (Markdown)",
                                       data=md.encode("utf-8"),
                                       file_name=Path(rp).name,
                                       mime="text/markdown")
                    # Also offer JSON if present
                    json_path = Path(rp).with_suffix(".json")
                    if json_path.exists():
                        js = json_path.read_text(encoding="utf-8")
                        st.download_button("⬇️ Download Report (JSON)",
                                           data=js.encode("utf-8"),
                                           file_name=json_path.name,
                                           mime="application/json")
            else:
                st.info("No grade on record for this submission.")

            with st.expander("Rubric (Provided)"):
                st.code((sub.get("rubric_text") or "")[:8000])
            with st.expander("Student Submission (Preview)"):
                st.code((sub.get("student_text") or "")[:8000])
