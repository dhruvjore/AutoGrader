# =============================
# File: src/reporting.py
# =============================
from __future__ import annotations
from pathlib import Path
from typing import List, Dict
import json
import logging
from datetime import datetime

from .grader.grade_evaluator import GradeResult

logger = logging.getLogger(__name__)

REPORTS_DIR = Path("data/reports")

def generate_markdown_report(submission: Dict, result: GradeResult) -> str:
    if not result:
        raise ValueError("GradeResult cannot be None")
    student_name = submission.get('student_name', 'N/A')
    filename = submission.get('filename', 'N/A')
    submitted_at = submission.get('submitted_at', 'N/A')
    rubric_text = submission.get('rubric_text', '')
    student_text = submission.get('student_text', '')

    if result.evidence and isinstance(result.evidence, (list, tuple)):
        evidence_md = "\n".join([f"- {str(e).strip()}" for e in result.evidence if e])
        if not evidence_md:
            evidence_md = "- (none)"
    else:
        evidence_md = "- (none)"

    try:
        score_display = f"{result.score:.3f}"
    except (AttributeError, TypeError, ValueError):
        score_display = "N/A"

    md = f"""# AutoGrader Report

**Student:** {student_name}
**File:** {filename}
**Submitted (UTC):** {submitted_at}
**Report Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

## Grade
- **Letter:** {result.grade or 'N/A'}
- **Score:** {score_display}

## Feedback
{result.feedback or 'No feedback provided.'}

## Evidence (Top Retrieved Chunks)
{evidence_md}

---
### Rubric (Provided)
{rubric_text.strip() if rubric_text else 'No rubric provided.'}

### Student Submission (Preview)
{student_text[:2000] if student_text else 'No submission text available.'}{'...' if len(student_text) > 2000 else ''}
"""
    return md

def save_report_markdown(submission_id: int, markdown: str) -> Path:
    if not isinstance(submission_id, int) or submission_id <= 0:
        raise ValueError(f"Invalid submission_id: {submission_id}")
    if not markdown or not markdown.strip():
        raise ValueError("Markdown content cannot be empty")
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = REPORTS_DIR / f"report_{submission_id}.md"
    out_path.write_text(markdown, encoding="utf-8")
    logger.info(f"Report saved successfully: {out_path}")
    return out_path

def generate_json_report(submission: Dict, result: GradeResult) -> str:
    report_data = {
        "metadata": {
            "student_name": submission.get('student_name'),
            "filename": submission.get('filename'),
            "submitted_at": submission.get('submitted_at'),
            "report_generated": datetime.utcnow().isoformat() + "Z"
        },
        "grading": {
            "grade": result.grade,
            "score": result.score,
            "feedback": result.feedback,
            "evidence": result.evidence if result.evidence else []
        },
        "context": {
            "rubric_text": submission.get('rubric_text'),
            "student_text_preview": (submission.get('student_text', '') or '')[:500]
        }
    }
    return json.dumps(report_data, indent=2, ensure_ascii=False)

def save_report_json(submission_id: int, json_content: str) -> Path:
    if not isinstance(submission_id, int) or submission_id <= 0:
        raise ValueError(f"Invalid submission_id: {submission_id}")
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = REPORTS_DIR / f"report_{submission_id}.json"
    out_path.write_text(json_content, encoding="utf-8")
    logger.info(f"JSON report saved successfully: {out_path}")
    return out_path

def generate_summary_report(submissions_results: List[tuple]) -> str:
    if not submissions_results:
        return "# Summary Report\n\nNo submissions to report."
    total_submissions = len(submissions_results)
    grades = [result.grade for _, result in submissions_results if result.grade]
    scores = [result.score for _, result in submissions_results
              if hasattr(result, 'score') and result.score is not None]
    grade_counts = {}
    for grade in grades:
        grade_counts[grade] = grade_counts.get(grade, 0) + 1
    avg_score = sum(scores) / len(scores) if scores else 0

    summary_md = f"""# Grading Summary Report

**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
**Total Submissions:** {total_submissions}

## Grade Distribution
"""
    for grade, count in sorted(grade_counts.items()):
        percentage = (count / total_submissions) * 100
        summary_md += f"- **{grade}:** {count} ({percentage:.1f}%)\n"
    summary_md += f"""
## Statistics
- **Average Score:** {avg_score:.3f}
- **Submissions with Scores:** {len(scores)}

## Individual Results
| Student | Grade | Score | Filename |
|---------|-------|-------|----------|
"""
    for submission, result in submissions_results:
        student = submission.get('student_name', 'N/A')
        filename = submission.get('filename', 'N/A')
        grade = result.grade or 'N/A'
        score = f"{result.score:.3f}" if hasattr(result, 'score') and result.score is not None else 'N/A'
        summary_md += f"| {student} | {grade} | {score} | {filename} |\n"
    return summary_md

def cleanup_old_reports(days_to_keep: int = 30) -> int:
    if not REPORTS_DIR.exists():
        return 0
    cutoff_time = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
    deleted_count = 0
    for report_file in REPORTS_DIR.glob("report_*.md"):
        try:
            if report_file.stat().st_mtime < cutoff_time:
                report_file.unlink()
                deleted_count += 1
                json_file = report_file.with_suffix('.json')
                if json_file.exists():
                    json_file.unlink()
        except OSError as e:
            logger.warning(f"Could not delete old report {report_file}: {e}")
    logger.info(f"Cleaned up {deleted_count} old report files")
    return deleted_count

# ============ Helpers for graded copy ============
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.utils import simpleSplit
import tempfile

def build_appendix_text(submission: Dict, result: GradeResult, retrieved: List[Dict]) -> str:
    lines = []
    lines.append("=== GRADING APPENDIX ===")
    lines.append(f"Student: {submission.get('student_name','N/A')}")
    lines.append(f"File: {submission.get('filename','N/A')}")
    lines.append(f"Generated (UTC): {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    lines.append("")
    lines.append(f"Total Score: {result.score if result.score is not None else 'N/A'}")
    lines.append(f"Letter Grade: {result.grade or 'N/A'}")
    lines.append("")
    lines.append("Overall Feedback:")
    fb = result.feedback or "No feedback."
    lines.extend([f"  {ln}" for ln in fb.splitlines() if ln.strip()])
    lines.append("")
    lines.append("Top Retrieved Context:")
    if retrieved:
        for r in retrieved[:10]:
            path = r.get("path","?")
            page = r.get("page", None)
            score = r.get("score", 0)
            loc = f"{path}" + (f":p{page}" if page else "")
            lines.append(f"  - [{score:.4f}] {loc}")
    else:
        lines.append("  - (none)")
    lines.append("")
    lines.append("End of Appendix")
    return "\n".join(lines)

def _write_plaintext_pdf(text: str, out_pdf_path: Path, page_size=LETTER, margin=54):
    out_pdf_path = Path(out_pdf_path)
    c = canvas.Canvas(str(out_pdf_path), pagesize=page_size)
    width, height = page_size
    x = margin
    y = height - margin
    max_width = width - 2*margin
    for para in text.split("\n"):
        wrapped = simpleSplit(para, "Helvetica", 10, max_width)
        if not wrapped:
            wrapped = [""]
        for line in wrapped:
            if y < margin + 12:
                c.showPage()
                y = height - margin
            c.setFont("Helvetica", 10)
            c.drawString(x, y, line)
            y -= 12
    c.showPage()
    c.save()

def create_graded_copy_from_pdf(original_pdf: Path, appendix_text: str, out_pdf: Path) -> Path:
    original_pdf = Path(original_pdf)
    out_pdf = Path(out_pdf)
    with tempfile.TemporaryDirectory() as td:
        appendix_pdf = Path(td) / "appendix.pdf"
        _write_plaintext_pdf(appendix_text, appendix_pdf)
        writer = PdfWriter()
        for page in PdfReader(str(original_pdf)).pages:
            writer.add_page(page)
        for page in PdfReader(str(appendix_pdf)).pages:
            writer.add_page(page)
        out_pdf.parent.mkdir(parents=True, exist_ok=True)
        with open(out_pdf, "wb") as f:
            writer.write(f)
    return out_pdf

def create_graded_copy_from_text(original_text_path: Path, appendix_text: str, out_text_path: Path) -> Path:
    original_text_path = Path(original_text_path)
    out_text_path = Path(out_text_path)
    out_text_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        body = original_text_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        body = ""
    sep = "\n\n---\n"
    out_text_path.write_text(body + sep + appendix_text + "\n", encoding="utf-8")
    return out_text_path