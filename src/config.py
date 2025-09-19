import os
from dotenv import load_dotenv

load_dotenv()

# Groq
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama3-70b-8192")
GROQ_BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")

# Data layout
BASE_DATA_DIR = os.getenv("BASE_DATA_DIR", "data")
RUBRICS_DIR = os.path.join(BASE_DATA_DIR, "rubrics")
QUESTIONS_DIR = os.path.join(BASE_DATA_DIR, "questions")
STUDENT_SUBMISSIONS_DIR = os.path.join(BASE_DATA_DIR, "student_submission")
# optional: solutions; leave empty if you don’t use it
SOLUTIONS_DIR = os.getenv("SOLUTIONS_DIR", "").strip()

# RAG
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1200"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))
TOP_K = int(os.getenv("TOP_K", "6"))

# Grading
DEFAULT_RUBRIC_NAME = os.getenv("DEFAULT_RUBRIC_NAME", "rubric.pdf")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.0"))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "1200"))
TIMEOUT_S = int(os.getenv("TIMEOUT_S", "60"))

# Reports
REPORTS_DIR = os.getenv("REPORTS_DIR", "data/reports")
os.makedirs(REPORTS_DIR, exist_ok=True)
