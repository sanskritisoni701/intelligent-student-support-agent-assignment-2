
from contextlib import contextmanager
import sqlite3
from pathlib import Path


# Locate the memory database
DB_FILE = (
    Path(__file__).resolve().parent / "memory.db"
)


# Information categories that can be remembered
ALLOWED_CATEGORIES = {
    "programme",
    "preferred_language",
    "response_preference",
    "learning_preference"
}


@contextmanager
def get_connection():
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_FILE)

    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


# 1. Initialize the database
def initialize_memory():

    with get_connection() as connection:

        connection.execute("""
            CREATE TABLE IF NOT EXISTS student_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                category TEXT NOT NULL,
                value TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(student_id, category)
            )
        """)


# 2. Verify student ownership
def verify_student_access(
    student_id,
    authenticated_student_id
):
    if not authenticated_student_id:
        return {
            "success": False,
            "error": "AUTHENTICATION_REQUIRED",
            "message": "Please log in to access your saved memory."
        }

    requested_id = student_id.strip().upper()
    authenticated_id = authenticated_student_id.strip().upper()

    if requested_id != authenticated_id:
        return {
            "success": False,
            "error": "ACCESS_DENIED",
            "message": "You cannot access another student's memory."
        }

    return None


# 3. Save useful information
def save_memory(
    student_id,
    category,
    value,
    authenticated_student_id
):

    access_error = verify_student_access(
        student_id,
        authenticated_student_id
    )

    if access_error:
        return access_error

    if category not in ALLOWED_CATEGORIES:
        return {
            "success": False,
            "message": "This information category cannot be stored."
        }

    if not isinstance(value, str) or not value.strip():
        return {
            "success": False,
            "message": "Memory value cannot be empty."
        }

    if len(value) > 200:
        return {
            "success": False,
            "message": "Memory value is too long."
        }

    authenticated_id = authenticated_student_id.strip().upper()

    try:
        with get_connection() as connection:

            connection.execute("""
                INSERT INTO student_memory
                (student_id, category, value)
                VALUES (?, ?, ?)

                ON CONFLICT(student_id, category)
                DO UPDATE SET value = excluded.value
            """, (
                authenticated_id,
                category,
                value.strip()
            ))

        return {
            "success": True,
            "message": "Memory saved successfully."
        }

    except sqlite3.Error:
        return {
            "success": False,
            "message": "Unable to save memory."
        }


# 4. Retrieve saved information
def get_memories(
    student_id,
    authenticated_student_id
):

    access_error = verify_student_access(
        student_id,
        authenticated_student_id
    )

    if access_error:
        return access_error

    authenticated_id = authenticated_student_id.strip().upper()

    try:
        with get_connection() as connection:

            cursor = connection.execute("""
                SELECT category, value
                FROM student_memory
                WHERE student_id = ?
            """, (authenticated_id,))

            records = cursor.fetchall()

        return {
            category: value
            for category, value in records
        }

    except sqlite3.Error:
        return {
            "success": False,
            "message": "Unable to retrieve saved memory."
        }


# 5. Clear a student's saved memory
def clear_memories(
    student_id,
    authenticated_student_id
):

    access_error = verify_student_access(
        student_id,
        authenticated_student_id
    )

    if access_error:
        return access_error

    authenticated_id = authenticated_student_id.strip().upper()

    try:
        with get_connection() as connection:

            connection.execute("""
                DELETE FROM student_memory
                WHERE student_id = ?
            """, (authenticated_id,))

        return {
            "success": True,
            "message": "Your saved memory has been cleared."
        }

    except sqlite3.Error:
        return {
            "success": False,
            "message": "Unable to clear saved memory."
        }


# Initialize database when this module is loaded
initialize_memory()
