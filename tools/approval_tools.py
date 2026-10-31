"""
Human approval workflow for student fee due-date changes.

Place this file at: tools/approval_tools.py

A student's request is stored as PENDING. The students.json fee record is
updated only after an authenticated administrator approves the request.
"""

import json
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timezone
from pathlib import Path
from uuid import uuid4

from auth.auth_manager import is_registered_admin

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "approvals.db"
STUDENTS_FILE = DATA_DIR / "students.json"


@contextmanager
def _connect():
    """
    Provide a SQLite connection that is always closed after use.

    The built-in sqlite3 connection context manager handles transactions,
    but does not close the connection. Explicitly closing it prevents
    Windows from locking the temporary database during test cleanup.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row

    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def initialize_approval_db():
    """Create approval-request and audit-log tables if they do not exist."""
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS approval_requests (
                request_id TEXT PRIMARY KEY,
                student_id TEXT NOT NULL,
                current_due_date TEXT NOT NULL,
                requested_due_date TEXT NOT NULL,
                reason TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL CHECK(status IN
                    ('PENDING', 'APPROVED', 'REJECTED')),
                requested_at TEXT NOT NULL,
                reviewed_at TEXT,
                reviewed_by TEXT,
                decision_note TEXT
            )
            """
        )
        # Backward-compatible migration for databases created before the
        # request reason was stored as its own column.
        columns = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(approval_requests)").fetchall()
        }
        if "reason" not in columns:
            conn.execute(
                "ALTER TABLE approval_requests ADD COLUMN reason TEXT NOT NULL DEFAULT ''"
            )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_log (
                audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
                actor_type TEXT NOT NULL,
                actor_id TEXT NOT NULL,
                action TEXT NOT NULL,
                request_id TEXT,
                student_id TEXT,
                details TEXT NOT NULL,
                outcome TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )


def _validate_date(value, field_name):
    try:
        parsed = date.fromisoformat(str(value))
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} must use YYYY-MM-DD format.")
    return parsed


def _read_students():
    if not STUDENTS_FILE.exists():
        raise FileNotFoundError(
            f"Student data file not found: {STUDENTS_FILE}"
        )
    with STUDENTS_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def _write_students_atomically(data):
    temporary_file = STUDENTS_FILE.with_suffix(".json.tmp")
    with temporary_file.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)
        file.flush()
    temporary_file.replace(STUDENTS_FILE)


def _find_student_record(data, student_id):
    """
    Find a student in the project's supported JSON formats:
    1. {"students": [{...}, {...}]}
    2. [{...}, {...}]
    3. {"STU1001": {...}, "STU1002": {...}}
    """
    normalized_id = str(student_id).strip().upper()

    # This project stores records inside the top-level "students" key.
    if isinstance(data, dict) and isinstance(data.get("students"), list):
        records = data["students"]
    elif isinstance(data, list):
        records = data
    elif isinstance(data, dict):
        records = list(data.values())
        direct_record = data.get(normalized_id)
        if isinstance(direct_record, dict):
            return direct_record
    else:
        records = []

    for record in records:
        if not isinstance(record, dict):
            continue

        record_id = str(record.get("student_id", "")).strip().upper()
        if record_id == normalized_id:
            return record

    raise ValueError("Student record was not found.")


def create_due_date_change_request(
    student_id,
    requested_due_date,
    authenticated_student_id,
    reason="",
):
    """
    Create a pending request. This function NEVER edits students.json.
    authenticated_student_id must come from the logged-in session.
    """
    initialize_approval_db()

    if not authenticated_student_id:
        return {"success": False, "error": "AUTHENTICATION_REQUIRED"}

    requested_id = str(student_id or "").strip().upper()
    authenticated_id = str(authenticated_student_id).strip().upper()

    if requested_id != authenticated_id:
        return {"success": False, "error": "ACCESS_DENIED"}

    try:
        requested_date = _validate_date(requested_due_date, "Requested due date")
        if requested_date <= date.today():
            return {
                "success": False,
                "error": "INVALID_DATE",
                "message": "The requested due date must be in the future.",
            }

        students = _read_students()
        student = _find_student_record(students, authenticated_id)
        current_due_date = str(student.get("due_date", "")).strip()

        if not current_due_date:
            return {
                "success": False,
                "error": "CURRENT_DUE_DATE_MISSING",
                "message": "The current due date is not available in the student record.",
            }

        _validate_date(current_due_date, "Current due date")

        request_id = f"FEE-{uuid4().hex[:10].upper()}"
        clean_reason = str(reason or "").strip()[:500]
        details = {
            "current_due_date": current_due_date,
            "requested_due_date": requested_date.isoformat(),
            "reason": clean_reason,
        }

        with _connect() as conn:
            conn.execute(
                """
                INSERT INTO approval_requests
                (request_id, student_id, current_due_date, requested_due_date,
                 reason, status, requested_at)
                VALUES (?, ?, ?, ?, ?, 'PENDING', ?)
                """,
                (
                    request_id,
                    authenticated_id,
                    current_due_date,
                    requested_date.isoformat(),
                    clean_reason,
                    _now(),
                ),
            )
            conn.execute(
                """
                INSERT INTO audit_log
                (actor_type, actor_id, action, request_id, student_id,
                 details, outcome, created_at)
                VALUES ('STUDENT', ?, 'REQUEST_DUE_DATE_CHANGE', ?, ?, ?, 'PENDING_APPROVAL', ?)
                """,
                (
                    authenticated_id,
                    request_id,
                    authenticated_id,
                    json.dumps(details, ensure_ascii=False),
                    _now(),
                ),
            )

        return {
            "success": True,
            "request_id": request_id,
            "status": "PENDING",
            "message": "Your request has been submitted for administrator approval. Your fee record has not been changed.",
            **details,
        }

    except (ValueError, FileNotFoundError, json.JSONDecodeError) as exc:
        return {"success": False, "error": "REQUEST_FAILED", "message": str(exc)}


def list_pending_due_date_requests(admin_username=None):
    """Return pending requests only to a registered administrator."""
    if not is_registered_admin(admin_username):
        return []
    initialize_approval_db()
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT request_id, student_id, current_due_date,
                   requested_due_date, reason, status, requested_at
            FROM approval_requests
            WHERE status = 'PENDING'
            ORDER BY requested_at ASC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def review_due_date_request(request_id, decision, admin_username, note=""):
    """
    Approve or reject a request. Call only from the authenticated admin UI.
    A rejection never changes students.json.
    """
    initialize_approval_db()

    if not is_registered_admin(admin_username):
        return {"success": False, "error": "ADMIN_AUTHORIZATION_REQUIRED"}

    decision = str(decision or "").strip().upper()
    if decision not in {"APPROVE", "REJECT"}:
        return {"success": False, "error": "INVALID_DECISION"}

    admin = str(admin_username).strip()
    note = str(note or "").strip()[:500]

    try:
        with _connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT * FROM approval_requests WHERE request_id = ?",
                (request_id,),
            ).fetchone()

            if row is None:
                conn.rollback()
                return {"success": False, "error": "REQUEST_NOT_FOUND"}

            if row["status"] != "PENDING":
                conn.rollback()
                return {
                    "success": False,
                    "error": "REQUEST_ALREADY_REVIEWED",
                    "status": row["status"],
                }

            student_id = row["student_id"]
            outcome = "REJECTED"

            if decision == "APPROVE":
                students = _read_students()
                student = _find_student_record(students, student_id)

                # Prevent overwriting a due date changed after this request was created.
                if str(student.get("due_date", "")).strip() != row["current_due_date"]:
                    conn.rollback()
                    return {
                        "success": False,
                        "error": "STUDENT_RECORD_CHANGED",
                        "message": "The current due date no longer matches this request. Please review the record before taking action.",
                    }

                student["due_date"] = row["requested_due_date"]
                _write_students_atomically(students)
                outcome = "APPROVED_AND_FEE_RECORD_UPDATED"

            new_status = "APPROVED" if decision == "APPROVE" else "REJECTED"
            conn.execute(
                """
                UPDATE approval_requests
                SET status = ?, reviewed_at = ?, reviewed_by = ?, decision_note = ?
                WHERE request_id = ? AND status = 'PENDING'
                """,
                (new_status, _now(), admin, note, request_id),
            )
            conn.execute(
                """
                INSERT INTO audit_log
                (actor_type, actor_id, action, request_id, student_id,
                 details, outcome, created_at)
                VALUES ('ADMIN', ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    admin,
                    f"{decision}_DUE_DATE_CHANGE",
                    request_id,
                    student_id,
                    json.dumps(
                        {
                            "current_due_date": row["current_due_date"],
                            "requested_due_date": row["requested_due_date"],
                            "student_reason": row["reason"],
                            "admin_review_note": note,
                        },
                        ensure_ascii=False,
                    ),
                    outcome,
                    _now(),
                ),
            )
            conn.commit()

        return {
            "success": True,
            "request_id": request_id,
            "status": new_status,
            "message": (
                "Request approved. The student's due date has been updated."
                if decision == "APPROVE"
                else "Request rejected. The student's fee record was not changed."
            ),
        }

    except (ValueError, FileNotFoundError, json.JSONDecodeError, OSError) as exc:
        return {"success": False, "error": "REVIEW_FAILED", "message": str(exc)}


def get_audit_log(limit=100, admin_username=None):
    """Return recent audit events only to a registered administrator."""
    if not is_registered_admin(admin_username):
        return []
    initialize_approval_db()
    safe_limit = max(1, min(int(limit), 500))
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT audit_id, actor_type, actor_id, action, request_id,
                   student_id, details, outcome, created_at
            FROM audit_log
            ORDER BY audit_id DESC
            LIMIT ?
            """,
            (safe_limit,),
        ).fetchall()

    results = []
    for row in rows:
        item = dict(row)
        try:
            item["details"] = json.loads(item["details"])
        except (TypeError, json.JSONDecodeError):
            pass
        results.append(item)
    return results
