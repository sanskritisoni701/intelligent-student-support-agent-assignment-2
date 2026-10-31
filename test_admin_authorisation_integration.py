import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from auth import auth_manager
from tools import approval_tools


class AdminAuthorizationIntegrationTests(unittest.TestCase):
    """Exercise approval authorization against a real temporary auth database."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.data_dir = self.root / "data"
        self.data_dir.mkdir()

        self.auth_db = self.data_dir / "auth.db"
        self.approval_db = self.data_dir / "approvals.db"
        self.students_file = self.data_dir / "students.json"

        self.students_file.write_text(
            json.dumps({
                "students": [{
                    "student_id": "STU1001",
                    "due_date": "2099-11-15",
                    "fee_status": "Partially Paid",
                    "total_fees": 250000,
                    "paid_amount": 150000,
                    "pending_amount": 100000
                }]
            }, indent=2),
            encoding="utf-8",
        )

        self.patches = [
            patch.object(auth_manager, "AUTH_DB", self.auth_db),
            patch.object(approval_tools, "DATA_DIR", self.data_dir),
            patch.object(approval_tools, "DB_PATH", self.approval_db),
            patch.object(approval_tools, "STUDENTS_FILE", self.students_file),
        ]
        for item in self.patches:
            item.start()
            self.addCleanup(item.stop)

        auth_manager.initialize_auth_db()
        approval_tools.initialize_approval_db()

        registered = auth_manager.register_admin(
            "integration_admin",
            "IntegrationAdmin!2026",
        )
        self.assertTrue(registered["success"], registered)

        request = approval_tools.create_due_date_change_request(
            student_id="STU1001",
            requested_due_date="2099-12-01",
            authenticated_student_id="STU1001",
            reason="Integration test request",
        )
        self.assertTrue(request["success"], request)
        self.request_id = request["request_id"]

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_registered_admin_can_list_pending_requests(self):
        requests = approval_tools.list_pending_due_date_requests(
            admin_username="integration_admin"
        )
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0]["request_id"], self.request_id)

    def test_unregistered_username_cannot_list_pending_requests(self):
        requests = approval_tools.list_pending_due_date_requests(
            admin_username="not_a_real_admin"
        )
        self.assertEqual(requests, [])

    def test_unregistered_username_cannot_review_request(self):
        result = approval_tools.review_due_date_request(
            request_id=self.request_id,
            decision="REJECT",
            admin_username="not_a_real_admin",
        )
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "ADMIN_AUTHORIZATION_REQUIRED")

    def test_unregistered_username_cannot_read_audit_log(self):
        entries = approval_tools.get_audit_log(
            limit=100,
            admin_username="not_a_real_admin",
        )
        self.assertEqual(entries, [])

    def test_registered_admin_can_review_request(self):
        result = approval_tools.review_due_date_request(
            request_id=self.request_id,
            decision="REJECT",
            admin_username="integration_admin",
            note="Rejected in integration test",
        )
        self.assertTrue(result["success"], result)
        self.assertEqual(result["status"], "REJECTED")


if __name__ == "__main__":
    unittest.main(verbosity=2)
