
import hashlib
import hmac
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
AUTH_DB = BASE_DIR / "data" / "auth.db"

HASH_NAME = "sha256"
ITERATIONS = 600_000
SALT_SIZE = 16


@contextmanager
def get_connection():
    """
    Yield a SQLite connection and always close it.

    sqlite3.Connection's built-in context manager handles transactions,
    but does not close the connection. This wrapper handles both transaction
    completion and connection cleanup.
    """
    AUTH_DB.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(AUTH_DB)
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_auth_db():
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS student_accounts (
                student_id TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS admin_accounts (
                username TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


def hash_password(password, salt):
    return hashlib.pbkdf2_hmac(
        HASH_NAME,
        password.encode("utf-8"),
        salt,
        ITERATIONS
    )


def register_student(student_id, password):
    student_id = student_id.strip().upper()

    if not student_id or not password:
        return {"success": False, "message": "Student ID and password are required."}

    if len(password) < 8:
        return {"success": False, "message": "Password must contain at least 8 characters."}

    salt = os.urandom(SALT_SIZE)
    password_hash = hash_password(password, salt)

    try:
        with get_connection() as connection:
            connection.execute("""
                INSERT INTO student_accounts
                (student_id, password_hash, salt)
                VALUES (?, ?, ?)
            """, (student_id, password_hash.hex(), salt.hex()))

        return {"success": True, "message": "Student registered successfully."}

    except sqlite3.IntegrityError:
        return {"success": False, "message": "Student account already exists."}


def authenticate_student(student_id, password):
    student_id = student_id.strip().upper()

    with get_connection() as connection:
        row = connection.execute("""
            SELECT password_hash, salt
            FROM student_accounts
            WHERE student_id = ?
        """, (student_id,)).fetchone()

    if not row:
        return {"success": False, "message": "Invalid Student ID or password."}

    stored_hash, stored_salt = row
    entered_hash = hash_password(password, bytes.fromhex(stored_salt))

    if hmac.compare_digest(entered_hash.hex(), stored_hash):
        return {"success": True, "student_id": student_id}

    return {"success": False, "message": "Invalid Student ID or password."}


def register_admin(username, password):
    username = username.strip()

    if not username or not password:
        return {"success": False, "message": "Username and password are required."}

    if len(password) < 12:
        return {"success": False, "message": "Admin password must contain at least 12 characters."}

    salt = os.urandom(SALT_SIZE)
    password_hash = hash_password(password, salt)

    try:
        with get_connection() as connection:
            connection.execute("""
                INSERT INTO admin_accounts
                (username, password_hash, salt)
                VALUES (?, ?, ?)
            """, (username, password_hash.hex(), salt.hex()))

        return {"success": True, "message": "Administrator account created."}

    except sqlite3.IntegrityError:
        return {"success": False, "message": "Administrator username already exists."}


def authenticate_admin(username, password):
    username = username.strip()

    with get_connection() as connection:
        row = connection.execute("""
            SELECT password_hash, salt
            FROM admin_accounts
            WHERE username = ?
        """, (username,)).fetchone()

    if not row:
        return {"success": False, "message": "Invalid administrator username or password."}

    stored_hash, stored_salt = row
    entered_hash = hash_password(password, bytes.fromhex(stored_salt))

    if hmac.compare_digest(entered_hash.hex(), stored_hash):
        return {"success": True, "username": username}

    return {"success": False, "message": "Invalid administrator username or password."}

def is_registered_admin(username):
    """Return True only when username exists in the administrator account table."""
    clean_username = str(username or "").strip()
    if not clean_username:
        return False

    initialize_auth_db()
    with get_connection() as connection:
        row = connection.execute(
            "SELECT 1 FROM admin_accounts WHERE username = ?",
            (clean_username,),
        ).fetchone()

    return row is not None

