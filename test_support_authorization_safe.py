
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools import support_tools


class SupportAuthorizationTests(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_ticket_file = (
            Path(self.temp_dir.name) / "test_support_tickets.json"
        )

        self.file_patcher = patch.object(
            support_tools, "TICKET_FILE", self.test_ticket_file
        )
        self.file_patcher.start()

    def tearDown(self):
        self.file_patcher.stop()
        self.temp_dir.cleanup()

    def test_create_own_support_ticket(self):
        result = support_tools.create_support_request(
            student_id="STU1001",
            authenticated_student_id="STU1001",
            issue_description="Test payment issue",
            category="Technical"
        )

        self.assertTrue(result.get("success"))
        self.assertEqual(
            result["ticket"]["student_id"], "STU1001"
        )

    def test_block_ticket_creation_for_another_student(self):
        result = support_tools.create_support_request(
            student_id="STU1002",
            authenticated_student_id="STU1001",
            issue_description="Unauthorized test",
            category="General"
        )

        self.assertFalse(result.get("success"))
        self.assertEqual(result.get("error"), "ACCESS_DENIED")

    def test_second_student_can_create_own_ticket(self):
        result = support_tools.create_support_request(
            student_id="STU1002",
            authenticated_student_id="STU1002",
            issue_description="Test library issue",
            category="General"
        )

        self.assertTrue(result.get("success"))
        self.assertEqual(
            result["ticket"]["student_id"], "STU1002"
        )

    def test_student_retrieves_only_own_tickets(self):
        support_tools.create_support_request(
            "STU1001", "First test issue", "STU1001"
        )
        support_tools.create_support_request(
            "STU1002", "Second test issue", "STU1002"
        )

        result = support_tools.get_student_support_requests(
            "STU1001"
        )

        self.assertTrue(result.get("success"))
        self.assertTrue(
            all(
                ticket["student_id"] == "STU1001"
                for ticket in result["tickets"]
            )
        )
        self.assertEqual(len(result["tickets"]), 1)

    def test_block_retrieval_without_authentication(self):
        result = support_tools.get_student_support_requests("")

        self.assertFalse(result.get("success"))
        self.assertEqual(
            result.get("error"), "AUTHENTICATION_REQUIRED"
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
