import tempfile
import unittest
from pathlib import Path

from memory import memory_manager


class MemoryAuthorizationTests(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

        # Use a temporary database instead of the real memory.db
        memory_manager.DB_FILE = (
            Path(self.temp_dir.name) / "test_memory.db"
        )

        memory_manager.initialize_memory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_save_own_memory(self):
        result = memory_manager.save_memory(
            "STU1001", "learning_preference",
            "Practical examples", "STU1001"
        )
        self.assertTrue(result.get("success"))

    def test_second_student_save_own_memory(self):
        result = memory_manager.save_memory(
            "STU1002", "learning_preference",
            "Visual explanations", "STU1002"
        )
        self.assertTrue(result.get("success"))

    def test_block_unauthorized_memory_saving(self):
        result = memory_manager.save_memory(
            "STU1002", "programme",
            "Unauthorized memory", "STU1001"
        )
        self.assertEqual(result.get("error"), "ACCESS_DENIED")

    def test_retrieve_own_memory(self):
        memory_manager.save_memory(
            "STU1001", "learning_preference",
            "Practical examples", "STU1001"
        )
        result = memory_manager.get_memories(
            "STU1001", "STU1001"
        )
        self.assertEqual(
            result.get("learning_preference"),
            "Practical examples"
        )

    def test_block_unauthorized_memory_retrieval(self):
        result = memory_manager.get_memories(
            "STU1002", "STU1001"
        )
        self.assertEqual(result.get("error"), "ACCESS_DENIED")

    def test_block_unauthorized_memory_deletion(self):
        memory_manager.save_memory(
            "STU1002", "learning_preference",
            "Visual explanations", "STU1002"
        )

        result = memory_manager.clear_memories(
            "STU1002", "STU1001"
        )
        self.assertEqual(result.get("error"), "ACCESS_DENIED")

        remaining = memory_manager.get_memories(
            "STU1002", "STU1002"
        )
        self.assertEqual(
            remaining.get("learning_preference"),
            "Visual explanations"
        )

    def test_block_access_without_authentication(self):
        result = memory_manager.get_memories("STU1001", "")
        self.assertEqual(
            result.get("error"),
            "AUTHENTICATION_REQUIRED"
        )

    def test_students_memories_are_separate(self):
        memory_manager.save_memory(
            "STU1001", "learning_preference",
            "Practical examples", "STU1001"
        )
        memory_manager.save_memory(
            "STU1002", "learning_preference",
            "Visual explanations", "STU1002"
        )

        first = memory_manager.get_memories(
            "STU1001", "STU1001"
        )
        second = memory_manager.get_memories(
            "STU1002", "STU1002"
        )

        self.assertEqual(
            first.get("learning_preference"),
            "Practical examples"
        )
        self.assertEqual(
            second.get("learning_preference"),
            "Visual explanations"
        )

    def test_student_can_clear_own_memory(self):
        memory_manager.save_memory(
            "STU1001", "learning_preference",
            "Temporary preference", "STU1001"
        )

        result = memory_manager.clear_memories(
            "STU1001", "STU1001"
        )
        self.assertTrue(result.get("success"))

        remaining = memory_manager.get_memories(
            "STU1001", "STU1001"
        )
        self.assertEqual(remaining, {})


if __name__ == "__main__":
    unittest.main(verbosity=2)