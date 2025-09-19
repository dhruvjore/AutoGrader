from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

DB_PATH = Path("data/grades/autograder.db")

SCHEMA_SQL = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_name TEXT,
    filename TEXT,
    file_path TEXT,
    student_text TEXT,
    rubric_text TEXT,
    submitted_at TEXT,
    status TEXT DEFAULT 'graded'
);

CREATE TABLE IF NOT EXISTS grades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    submission_id INTEGER REFERENCES submissions(id) ON DELETE CASCADE,
    score REAL,
    letter TEXT,
    feedback TEXT,
    evidence TEXT,
    report_path TEXT,
    created_at TEXT
);
"""

def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.execute("PRAGMA foreign_keys=ON;")
    return con

def init_db() -> None:
    con = _connect()
    try:
        con.executescript(SCHEMA_SQL)
        con.commit()
    finally:
        con.close()

def insert_submission(student_name: str, filename: str, file_path: str, student_text: str, rubric_text: str) -> int:
    con = _connect()
    try:
        cur = con.execute(
            "INSERT INTO submissions(student_name, filename, file_path, student_text, rubric_text, submitted_at) VALUES (?,?,?,?,?,?)",
            (student_name, filename, file_path, student_text, rubric_text, datetime.utcnow().isoformat()),
        )
        con.commit()
        return int(cur.lastrowid)
    finally:
        con.close()

def insert_grade(submission_id: int, score: float, letter: str, feedback: str, evidence: str, report_path: str) -> int:
    con = _connect()
    try:
        cur = con.execute(
            "INSERT INTO grades(submission_id, score, letter, feedback, evidence, report_path, created_at) VALUES (?,?,?,?,?,?,?)",
            (submission_id, score, letter, feedback, evidence, report_path, datetime.utcnow().isoformat()),
        )
        con.commit()
        return int(cur.lastrowid)
    finally:
        con.close()

def list_all_with_grades() -> List[Dict[str, Any]]:
    con = _connect()
    try:
        cur = con.execute(
            """
            SELECT s.id, s.student_name, s.filename, s.submitted_at,
                   g.score, g.letter, g.report_path
            FROM submissions s
            LEFT JOIN grades g ON g.submission_id = s.id
            ORDER BY s.id DESC
            """
        )
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]
    finally:
        con.close()

def get_submission(submission_id: int) -> Optional[Dict[str, Any]]:
    con = _connect()
    try:
        cur = con.execute("SELECT * FROM submissions WHERE id=?", (submission_id,))
        row = cur.fetchone()
        if not row:
            return None
        cols = [d[0] for d in cur.description]
        return dict(zip(cols, row))
    finally:
        con.close()
