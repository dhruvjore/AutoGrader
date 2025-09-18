#app.py
import streamlit as st
from dotenv import load_dotenv
from pathlib import Path

from src.rag.retriever import Retriever
from src.grader.grade_evaluator import GradeEvaluator

# --- helpers to read uploads ---
def read_uploaded_text(uploaded_file) -> str:
    suffix = Path(uploaded_file.name).suffix.lower()
    data = uploaded_file.read()
    if suffix == ".txt":
        return data.decode("utf-8", errors="ignore")
    # Keep it simple in app: basic text previews only.
    # For PDF/DOCX, we could call the loader again, but that expects a path.
    # For now, ask users to upload TXT or paste text.
    try:
        return data.decode("utf-8", errors="ignore")
    except Exception:
        return ""

load_dotenv()
st.set_page_config(page_title="AutoGrader (RAG baseline)", page_icon="📘", layout="wide")
st.title("📘 AutoGrader — RAG Baseline")

# --- Index controls ---
st.sidebar.header("RAG Indexing")
data_roots = [
    "data/rubrics",
    "data/answer_keys",
    "data/student_submissions"  # optional: prior A+ answers as exemplars
]
retriever = Retriever(persist_path="data/grades/tfidf_store.pkl")

index_btn = st.sidebar.button("🔁 Build / Rebuild Index")
if index_btn:
    total = retriever.index_dirs(data_roots)
    st.sidebar.success(f"Indexed {total} chunks.")

# Always try to load an existing index
retriever.load()

# --- Upload area ---
col1, col2 = st.columns(2)
with col1:
    st.subheader("Student Submission (TXT preferred)")
    up_student = st.file_uploader("Upload student submission", type=["txt", "pdf", "docx"], key="stu")
with col2:
    st.subheader("Rubric / Answer Key (TXT preferred)")
    up_rubric = st.file_uploader("Upload rubric or answer key", type=["txt", "pdf", "docx"], key="rub")

student_text = read_uploaded_text(up_student) if up_student else ""
rubric_text  = read_uploaded_text(up_rubric) if up_rubric else ""

if up_student:
    st.text_area("Preview: Student Text", student_text[:5000], height=200)
if up_rubric:
    st.text_area("Preview: Rubric Text", rubric_text[:5000], height=200)

disabled = not (student_text and rubric_text)
if st.button("⚖️ Grade with RAG Baseline", type="primary", disabled=disabled):
    if disabled:
        st.error("Please upload both student and rubric files (TXT preferred).")
    else:
        evaluator = GradeEvaluator(retriever=retriever, k=5)
        result = evaluator.evaluate(student_text, rubric_text)
        st.subheader("Grade Report")
        st.markdown(f"**Letter Grade:** {result.grade}")
        st.markdown(f"**Score (0..1):** {result.score:.3f}")
        st.markdown("**Feedback:**")
        st.write(result.feedback)
        with st.expander("Evidence (retrieved chunks)"):
            for e in result.evidence:
                st.write(f"- {e}")
