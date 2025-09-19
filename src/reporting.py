# =============================
# File: src/reporting.py
# =============================
from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Optional
import json
import logging
from datetime import datetime

from .grader.grade_evaluator import GradeResult

logger = logging.getLogger(__name__)

REPORTS_DIR = Path("data/reports")


def generate_markdown_report(submission: Dict, result: GradeResult) -> str:
    """
    Build a readable Markdown report for faculty download.
    
    Args:
        submission: Dictionary containing submission metadata
        result: GradeResult object with grading information
        
    Returns:
        str: Formatted markdown report
        
    Raises:
        ValueError: If required fields are missing from submission or result
    """
    # Validate required fields
    if not result:
        raise ValueError("GradeResult cannot be None")
    
    # Extract and validate submission data with defaults
    student_name = submission.get('student_name', 'N/A')
    filename = submission.get('filename', 'N/A')
    submitted_at = submission.get('submitted_at', 'N/A')
    rubric_text = submission.get('rubric_text', '')
    student_text = submission.get('student_text', '')
    
    # Format evidence list
    if result.evidence and isinstance(result.evidence, (list, tuple)):
        evidence_md = "\n".join([f"- {str(e).strip()}" for e in result.evidence if e])
        if not evidence_md:
            evidence_md = "- (none)"
    else:
        evidence_md = "- (none)"
    
    # Format score safely
    try:
        score_display = f"{result.score:.3f}"
    except (AttributeError, TypeError, ValueError):
        score_display = "N/A"
    
    # Build the markdown report
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
```
{rubric_text.strip() if rubric_text else 'No rubric provided.'}
```

### Student Submission (Preview)
```
{student_text[:2000] if student_text else 'No submission text available.'}{'...' if len(student_text) > 2000 else ''}
```
"""
    return md


def save_report_markdown(submission_id: int, markdown: str) -> Path:
    """
    Save a markdown report to the reports directory.
    
    Args:
        submission_id: Unique identifier for the submission
        markdown: The markdown content to save
        
    Returns:
        Path: Path to the saved report file
        
    Raises:
        ValueError: If submission_id is invalid or markdown is empty
        OSError: If file cannot be written
    """
    if not isinstance(submission_id, int) or submission_id <= 0:
        raise ValueError(f"Invalid submission_id: {submission_id}")
    
    if not markdown or not markdown.strip():
        raise ValueError("Markdown content cannot be empty")
    
    try:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        out_path = REPORTS_DIR / f"report_{submission_id}.md"
        
        # Write with error handling
        out_path.write_text(markdown, encoding="utf-8")
        logger.info(f"Report saved successfully: {out_path}")
        
        return out_path
        
    except OSError as e:
        logger.error(f"Failed to save report for submission {submission_id}: {e}")
        raise


def generate_json_report(submission: Dict, result: GradeResult) -> str:
    """
    Generate a JSON report for programmatic consumption.
    
    Args:
        submission: Dictionary containing submission metadata
        result: GradeResult object with grading information
        
    Returns:
        str: JSON formatted report
    """
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
    """
    Save a JSON report to the reports directory.
    
    Args:
        submission_id: Unique identifier for the submission
        json_content: The JSON content to save
        
    Returns:
        Path: Path to the saved JSON report file
    """
    if not isinstance(submission_id, int) or submission_id <= 0:
        raise ValueError(f"Invalid submission_id: {submission_id}")
    
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = REPORTS_DIR / f"report_{submission_id}.json"
    
    try:
        out_path.write_text(json_content, encoding="utf-8")
        logger.info(f"JSON report saved successfully: {out_path}")
        return out_path
    except OSError as e:
        logger.error(f"Failed to save JSON report for submission {submission_id}: {e}")
        raise


def generate_summary_report(submissions_results: List[tuple]) -> str:
    """
    Generate a summary report across multiple submissions.
    
    Args:
        submissions_results: List of (submission_dict, result) tuples
        
    Returns:
        str: Markdown summary report
    """
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
    """
    Clean up old report files to manage disk space.
    
    Args:
        days_to_keep: Number of days worth of reports to keep
        
    Returns:
        int: Number of files deleted
    """
    if not REPORTS_DIR.exists():
        return 0
    
    cutoff_time = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
    deleted_count = 0
    
    for report_file in REPORTS_DIR.glob("report_*.md"):
        try:
            if report_file.stat().st_mtime < cutoff_time:
                report_file.unlink()
                deleted_count += 1
                
                # Also delete corresponding JSON file if it exists
                json_file = report_file.with_suffix('.json')
                if json_file.exists():
                    json_file.unlink()
                    
        except OSError as e:
            logger.warning(f"Could not delete old report {report_file}: {e}")
    
    logger.info(f"Cleaned up {deleted_count} old report files")
    return deleted_count