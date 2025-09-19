# 📚 AutoGrader – AI-Powered Assignment Grading

AutoGrader is a **Streamlit-based AI application** that grades assignments, exam papers, and submissions automatically using **LLM-powered evaluation + rubrics + answer keys**.  
It supports multiple file types (PDFs, text, JSON rubrics), generates **percentage-based grades**, and produces **detailed markdown/PDF reports** for instructors.

---

## ✨ Features

- 🔍 **Rubric-Driven Grading**  
  Upload rubrics (criteria, weightages, answer keys) and grade assignments fairly.  
- 📊 **Percentage-Based Evaluation**  
  Works for assignments of any maximum marks — grading normalized to 100%.  
- 🧠 **LLM-Powered Feedback**  
  Uses Gemini / Groq / Prometheus models for AI-assisted grading & evidence generation.  
- 📑 **Beautiful Reports**  
  Exports **Markdown reports** (and optionally PDF) with student name, score, grade, and evidence.  
- 📂 **Organized Storage**  
  - `data/reports/` → Final reports  
  - `data/graded_copies/` → Graded student submissions  
  - `data/submissions/` → Uploaded submissions  
  - `data/knowledge/` → Rubrics, questions, and reference material  
- ⚡ **Streamlit UI**  
  Easy drag-and-drop interface for faculty to upload rubrics & assignments.

---

## 🚀 Quick Start

### 1. Clone the Repo
```bash
git clone https://github.com/dhruvjore/AutoGrader.git
cd AutoGrader
```

### 2. Setup Environment
```bash
python -m venv autograder_venv
.\autograder_venv\Scripts\activate   # Windows
# or
source autograder_venv/bin/activate  # Mac/Linux
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the App
```bash
streamlit run app.py
```

---

## 🏗️ Project Structure

```
AutoGrader/
│── app.py                  # Streamlit main app
│── grader.py               # Core grading pipeline
│── requirements.txt        # Python dependencies
│── .gitignore              # Ignored files & folders
│── data/
│   ├── submissions/        # Student uploads
│   ├── graded_copies/      # Annotated student copies
│   ├── reports/            # Generated reports
│   └── knowledge/          # Rubrics & reference docs
│── src/
    ├── grader/             # Grade evaluator, models
    ├── reporting.py        # Markdown/PDF report generator
    └── llm/                # Gemini/Groq client
```

---

## ⚙️ Configuration

Project settings are stored in `.env`:

```env
DOCS_DIR=data/knowledge
CHUNK_SIZE=1200
CHUNK_OVERLAP=200
TOP_K=6
LLM_PROVIDER=gemini
OPENAI_COMPAT_BASE_URL=...
OPENAI_COMPAT_API_KEY=...
OPENAI_COMPAT_MODEL=gemma-7b-it
```

---

## 📈 Example Workflow

1. Instructor uploads `rubric.json` and `student_submissions.pdf`
2. AutoGrader parses submissions & rubrics
3. AI evaluator assigns percentage + letter grade (A+, B, etc.)
4. Generates a `report.md` in `data/reports/` with grading evidence

---

## 🔮 Roadmap

- [ ] Support image-aware grading (diagrams, plots in PDFs)
- [ ] LMS integration (Canvas, Moodle)
- [ ] Multi-rubric & peer grading support
- [ ] Detailed analytics dashboard for instructors

---

## 🤝 Contributing

PRs are welcome! Fork the repo and submit a pull request 🚀

---

## 📜 License

MIT License © 2025 Dhruv Jore
