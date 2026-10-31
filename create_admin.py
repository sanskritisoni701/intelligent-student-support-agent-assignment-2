
from getpass import getpass

from auth.auth_manager import (
    initialize_auth_db,
    register_admin
)

def main():
    initialize_auth_db()

    print("\n=== Administrator Account Setup ===")

    username = input("Enter admin username: ").strip()
    password = getpass("Enter admin password (minimum 12 characters): ")
    confirm_password = getpass("Confirm admin password: ")

    if password != confirm_password:
        print("Passwords do not match. Please try again.")
        return

    result = register_admin(username, password)
    print(result["message"])


if __name__ == "__main__":
    main()
