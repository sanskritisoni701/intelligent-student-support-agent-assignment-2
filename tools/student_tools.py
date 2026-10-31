
import json
from pathlib import Path


DATA_FILE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "students.json"
)


def get_student_fee_status(
    student_id: str,
    authenticated_student_id: str
):
    """
    Retrieve fee information only for the authenticated student.
    """

    if not authenticated_student_id:
        return {
            "success": False,
            "error": "AUTHENTICATION_REQUIRED",
            "message": "Please log in to access your fee information."
        }

    # Normalize both identities
    requested_id = student_id.strip().upper()
    authenticated_id = authenticated_student_id.strip().upper()

    # Enforce ownership before accessing the database
    if requested_id != authenticated_id:
        return {
            "success": False,
            "error": "ACCESS_DENIED",
            "message": "You are not authorized to access this student record."
        }

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        for student in data["students"]:

            if student["student_id"].upper() == authenticated_id:

                return {
                    "success": True,
                    "student_id": student["student_id"],
                    "name": student["name"],
                    "fee_status": student["fee_status"],
                    "total_fees": student["total_fees"],
                    "paid_amount": student["paid_amount"],
                    "pending_amount": student["pending_amount"],
                    "due_date": student["due_date"]
                }

        return {
            "success": False,
            "error": "RECORD_NOT_FOUND",
            "message": "Student record not found."
        }

    except FileNotFoundError:
        return {
            "success": False,
            "error": "DATABASE_UNAVAILABLE",
            "message": "Student database is unavailable."
        }

    except (json.JSONDecodeError, KeyError) as error:
        return {
            "success": False,
            "error": "DATABASE_ERROR",
            "message": f"Student database error: {error}"
        }
