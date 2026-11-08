
import tempfile
import unittest
from pathlib import Path

import database


class DatabaseTests(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_tutorme.db"

        database.initialize_database(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def create_sample_lesson(self):
        return {
            "id": "lesson-001",
            "title": "Newton's Laws",
            "subject": "Physics",
            "difficulty": "beginner",
            "version": 1,
            "steps": [
                {
                    "id": "step-1",
                    "explanation": "First law",
                    "visual_actions": []
                }
            ]
        }

    def test_initialize_database(self):
        with database.get_connection(self.db_path) as connection:
            rows = connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()

        tables = {row["name"] for row in rows}

        self.assertTrue({"conversations", "messages", "lessons"}.issubset(tables))

    def test_save_and_retrieve_lesson(self):
        lesson = self.create_sample_lesson()

        database.save_lesson(lesson, db_path=self.db_path)

        result = database.get_lesson(
            "lesson-001", db_path=self.db_path
        )

        self.assertIsNotNone(result)
        self.assertEqual(result["lesson"]["title"], "Newton's Laws")
        self.assertEqual(result["subject"], "Physics")

    def test_save_lesson_with_conversation(self):
        conversation_id = database.create_conversation(
            "Physics", db_path=self.db_path
        )

        database.save_lesson(
            self.create_sample_lesson(),
            conversation_id=conversation_id,
            db_path=self.db_path
        )

        result = database.get_lesson(
            "lesson-001", db_path=self.db_path
        )

        self.assertEqual(result["conversation_id"], conversation_id)

    def test_list_lessons(self):
        database.save_lesson(
            self.create_sample_lesson(),
            db_path=self.db_path
        )

        lessons = database.get_lessons(db_path=self.db_path)

        self.assertEqual(len(lessons), 1)
        self.assertEqual(lessons[0]["id"], "lesson-001")

    def test_filter_lessons_by_conversation(self):
        first = database.create_conversation(
            "Physics", db_path=self.db_path
        )
        second = database.create_conversation(
            "Maths", db_path=self.db_path
        )

        lesson1 = self.create_sample_lesson()

        lesson2 = self.create_sample_lesson()
        lesson2["id"] = "lesson-002"
        lesson2["title"] = "Algebra"

        database.save_lesson(
            lesson1, first, db_path=self.db_path
        )

        database.save_lesson(
            lesson2, second, db_path=self.db_path
        )

        results = database.get_lessons(
            conversation_id=first,
            db_path=self.db_path
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], "lesson-001")

    def test_delete_lesson(self):
        database.save_lesson(
            self.create_sample_lesson(),
            db_path=self.db_path
        )

        deleted = database.delete_lesson(
            "lesson-001", db_path=self.db_path
        )

        self.assertEqual(deleted, 1)

        result = database.get_lesson(
            "lesson-001", db_path=self.db_path
        )

        self.assertIsNone(result)

    def test_deleting_conversation_preserves_lesson(self):
        conversation_id = database.create_conversation(
            "Physics", db_path=self.db_path
        )

        database.save_lesson(
            self.create_sample_lesson(),
            conversation_id,
            db_path=self.db_path
        )

        database.delete_conversation(
            conversation_id, db_path=self.db_path
        )

        result = database.get_lesson(
            "lesson-001", db_path=self.db_path
        )

        self.assertIsNotNone(result)
        self.assertIsNone(result["conversation_id"])

    def test_existing_chat_history_still_works(self):
        conversation_id = database.create_conversation(
            "Test conversation", db_path=self.db_path
        )

        database.save_message(
            conversation_id, "user", "Hello",
            db_path=self.db_path
        )

        database.save_message(
            conversation_id, "assistant", "Hi there",
            db_path=self.db_path
        )

        messages = database.get_messages(
            conversation_id, db_path=self.db_path
        )

        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["content"], "Hello")
        self.assertEqual(messages[1]["content"], "Hi there")

    def test_invalid_lesson_is_rejected(self):
        with self.assertRaises(ValueError):
            database.save_lesson(
                {"id": "invalid"},
                db_path=self.db_path
            )


if __name__ == "__main__":
    unittest.main()
