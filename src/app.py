import streamlit as st
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

st.set_page_config(page_title="AutoGrader", page_icon="📘", layout="wide")

st.title("📘 AutoGrader")
st.write("Upload student assignments and evaluate them against rubrics or answer keys.")

# File uploader
uploaded_file = st.file_uploader("Upload a student submission (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"])

# Rubric uploader
uploaded_rubric = st.file_uploader("Upload a rubric or answer key (TXT, DOCX, PDF)", type=["pdf", "docx", "txt"])

# Placeholder grading logic
if uploaded_file and uploaded_rubric:
    st.success("✅ Files uploaded successfully!")
    if st.button("Grade Assignment"):
        with st.spinner("Evaluating..."):
            # TODO: connect grader logic here
            st.subheader("Grade Report")
            st.write("**Grade:** B+")
            st.write("**Feedback:** Good attempt. Improve structure and add more references.")
