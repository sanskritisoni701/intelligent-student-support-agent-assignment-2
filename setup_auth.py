
import json
from pathlib import Path
from getpass import getpass

from auth.auth_manager import (
    initialize_auth_db,
    register_student
)

BASE_DIR = Path(__file__).resolve().parent
STUDENT_FILE = BASE_DIR / "data" / "students.json"


def get_registered_student_ids():
    with open(STUDENT_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)

    return {
        student["student_id"].upper()
        for student in data["students"]
    }


def main():
    initialize_auth_db()

    valid_ids = get_registered_student_ids()

    print("\n=== Student Account Setup ===")
    print("Available sample student IDs:")

    for student_id in sorted(valid_ids):
        print("-", student_id)

    student_id = input("\nEnter Student ID: ").strip().upper()

    if student_id not in valid_ids:
        print("Error: Student ID does not exist.")
        return

    password = getpass("Create password (minimum 8 characters): ")
    confirm_password = getpass("Confirm password: ")

    if password != confirm_password:
        print("Error: Passwords do not match.")
        return

    result = register_student(student_id, password)

    print("\nRegistration result:")
    print(result["message"])


if __name__ == "__main__":
    main()
