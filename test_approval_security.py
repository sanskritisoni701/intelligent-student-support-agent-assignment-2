import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools import approval_tools


class ApprovalWorkflowSecurityTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.data_dir = self.root / "data"
        self.data_dir.mkdir()
        self.db_path = self.data_dir / "approvals.db"
        self.students_file = self.data_dir / "students.json"
        self.students_file.write_text(
            json.dumps({
                "students": [
                    {
                        "student_id": "STU1001",
                        "due_date": "2099-11-15",
                        "fee_status": "Partially Paid"
                    },
                    {
                        "student_id": "STU1002",
                        "due_date": "2099-11-20",
                        "fee_status": "Partially Paid"
                    }
                ]
            }),
            encoding="utf-8"
        )

        self.db_patch = patch.object(approval_tools, "DB_PATH", self.db_path)
        self.students_patch = patch.object(
            approval_tools, "STUDENTS_FILE", self.students_file
        )
        self.data_patch = patch.object(approval_tools, "DATA_DIR", self.data_dir)
        self.admin_check_patch = patch.object(
            approval_tools, "is_registered_admin",
            side_effect=lambda username: username == "test_admin"
        )
        self.db_patch.start()
        self.students_patch.start()
        self.data_patch.start()
        self.admin_check_patch.start()
        approval_tools.initialize_approval_db()

    def tearDown(self):
        self.db_patch.stop()
        self.students_patch.stop()
        self.data_patch.stop()
        self.admin_check_patch.stop()
        self.temp_dir.cleanup()

    def read_student_due_date(self, student_id):
        data = json.loads(self.students_file.read_text(encoding="utf-8"))
        return next(
            student["due_date"]
            for student in data["students"]
            if student["student_id"] == student_id
        )

    def create_request(self, student_id="STU1001", authenticated_id=None):
        authenticated_id = authenticated_id or student_id
        return approval_tools.create_due_date_change_request(
            student_id=student_id,
            requested_due_date="2099-12-01",
            reason="Automated test reason",
            authenticated_student_id=authenticated_id,
        )

    def test_student_cannot_create_request_for_another_student(self):
        result = self.create_request(
            student_id="STU1002",
            authenticated_id="STU1001"
        )
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "ACCESS_DENIED")
        self.assertEqual(self.read_student_due_date("STU1002"), "2099-11-20")

    def test_review_requires_nonempty_admin_identity(self):
        request = self.create_request()
        self.assertTrue(request["success"])

        result = approval_tools.review_due_date_request(
            request_id=request["request_id"],
            decision="APPROVE",
            admin_username=""
        )
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "ADMIN_AUTHORIZATION_REQUIRED")

        # A non-empty but unregistered username must also be rejected.
        unregistered = approval_tools.review_due_date_request(
            request_id=request["request_id"],
            decision="APPROVE",
            admin_username="not_a_registered_admin"
        )
        self.assertFalse(unregistered["success"])
        self.assertEqual(unregistered["error"], "ADMIN_AUTHORIZATION_REQUIRED")
        self.assertEqual(self.read_student_due_date("STU1001"), "2099-11-15")

    def test_request_cannot_be_reviewed_twice(self):
        request = self.create_request()
        self.assertTrue(request["success"])

        first = approval_tools.review_due_date_request(
            request_id=request["request_id"],
            decision="REJECT",
            admin_username="test_admin"
        )
        self.assertTrue(first["success"])
        self.assertEqual(first["status"], "REJECTED")

        second = approval_tools.review_due_date_request(
            request_id=request["request_id"],
            decision="APPROVE",
            admin_username="test_admin"
        )
        self.assertFalse(second["success"])
        self.assertEqual(second["error"], "REQUEST_ALREADY_REVIEWED")
        self.assertEqual(self.read_student_due_date("STU1001"), "2099-11-15")

    def test_approved_request_updates_only_its_student_record(self):
        request = self.create_request()
        self.assertTrue(request["success"])

        result = approval_tools.review_due_date_request(
            request_id=request["request_id"],
            decision="APPROVE",
            admin_username="test_admin"
        )
        self.assertTrue(result["success"])
        self.assertEqual(self.read_student_due_date("STU1001"), "2099-12-01")
        self.assertEqual(self.read_student_due_date("STU1002"), "2099-11-20")

    def test_rejected_request_does_not_change_due_date(self):
        request = self.create_request()
        self.assertTrue(request["success"])

        result = approval_tools.review_due_date_request(
            request_id=request["request_id"],
            decision="REJECT",
            admin_username="test_admin"
        )
        self.assertTrue(result["success"])
        self.assertEqual(self.read_student_due_date("STU1001"), "2099-11-15")


if __name__ == "__main__":
    unittest.main(verbosity=2)
