
import json
import uuid
from pathlib import Path
from datetime import datetime, timezone


# Location where support tickets will be stored
TICKET_FILE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "support_tickets.json"
)


def create_support_request(
    student_id: str,
    issue_description: str,
    authenticated_student_id: str,
    category: str = "General"
):
    """
    Create a support ticket only for the authenticated student.
    """

    # Authentication check
    if not authenticated_student_id:
        return {
            "success": False,
            "error": "AUTHENTICATION_REQUIRED",
            "message": "Please log in before creating a support request."
        }

    requested_id = student_id.strip().upper()
    authenticated_id = authenticated_student_id.strip().upper()

    # Ownership check
    if requested_id != authenticated_id:
        return {
            "success": False,
            "error": "ACCESS_DENIED",
            "message": "You cannot create a support request for another student."
        }

    try:
        if not issue_description.strip():
            return {
                "success": False,
                "message": "Issue description is required."
            }

        # Create a unique ticket
        ticket = {
            "ticket_id": "TKT-" + uuid.uuid4().hex[:8].upper(),
            "student_id": authenticated_id,
            "category": category.strip(),
            "description": issue_description.strip(),
            "status": "Open",
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        # Read existing tickets
        if TICKET_FILE.exists():
            with open(TICKET_FILE, "r", encoding="utf-8") as file:
                tickets = json.load(file)
        else:
            tickets = []

        # Add new ticket
        tickets.append(ticket)

        # Save updated tickets
        with open(TICKET_FILE, "w", encoding="utf-8") as file:
            json.dump(tickets, file, indent=4)

        return {
            "success": True,
            "message": "Support request created successfully.",
            "ticket": ticket
        }

    except (OSError, json.JSONDecodeError) as error:
        return {
            "success": False,
            "message": f"Unable to create support request: {error}"
        }


def get_student_support_requests(
    authenticated_student_id: str
):
    """
    Retrieve only the support tickets belonging to
    the authenticated student.
    """

    if not authenticated_student_id:
        return {
            "success": False,
            "error": "AUTHENTICATION_REQUIRED",
            "message": "Please log in to view support requests."
        }

    try:
        if not TICKET_FILE.exists():
            return {
                "success": True,
                "tickets": []
            }

        with open(TICKET_FILE, "r", encoding="utf-8") as file:
            tickets = json.load(file)

        if not isinstance(tickets, list):
            return {
                "success": False,
                "message": "Support ticket database has an invalid format."
            }

        # Return only tickets owned by the authenticated student
        student_tickets = [
            ticket for ticket in tickets
            if ticket.get("student_id", "").strip().upper()
            == authenticated_student_id.strip().upper()
        ]

        return {
            "success": True,
            "tickets": student_tickets
        }

    except (OSError, json.JSONDecodeError) as error:
        return {
            "success": False,
            "message": f"Unable to retrieve support requests: {error}"
        }
