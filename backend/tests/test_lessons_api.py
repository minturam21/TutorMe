
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

import database

from api.lessons import router
from services.lesson_planner import LessonPlanningError
from services.action_generator import ActionGenerationError
from services.lesson_compiler import LessonCompilationError


class FakePlanner:

    def create_plan(self, question, subject, difficulty):
        return {
            "title": "Introduction to Motion",
            "subject": "Physics",
            "topic": "Motion",
            "difficulty": "beginner",
            "objectives": ["Understand basic motion"],
            "steps": [
                {
                    "id": f"step_{i}",
                    "teaching_goal": "Understand motion",
                    "explanation": "Motion is a change in position over time.",
                    "key_concepts": ["Position", "Time"],
                    "equations": [],
                    "visual_goal": "Introduce motion",
                    "visual_requirements": ["Show a diagram"],
                }
                for i in range(1, 4)
            ],
            "practice_questions": [
                {
                    "question": "What is motion?",
                    "answer": "Change in position over time.",
                    "explanation": "Motion describes a change in position.",
                },
                {
                    "question": "What measures duration?",
                    "answer": "Time.",
                    "explanation": "Time measures duration.",
                },
                {
                    "question": "What describes location?",
                    "answer": "Position.",
                    "explanation": "Position describes where an object is.",
                },
            ],
        }


class FakeActionGenerator:

    def generate_actions(self, plan):
        for i, step in enumerate(plan["steps"], start=1):
            step["visual_actions"] = [
                {
                    "id": f"action_{i}",
                    "type": "wait",
                    "parameters": {},
                    "duration": 1,
                    "easing": "linear",
                    "order": 0,
                }
            ]

        return plan


class LessonsAPITests(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_tutorme.db"

        database.initialize_database(self.db_path)

        # Keep original database functions.
        original_save = database.save_lesson
        original_get = database.get_lesson
        original_list = database.get_lessons
        original_delete = database.delete_lesson

        # Preserve original getter for direct database verification.
        self.original_get = original_get

        # Redirect API database operations to temporary database.
        self.db_patches = [
            patch(
                "api.lessons.database.save_lesson",
                side_effect=lambda lesson, conversation_id=None:
                    original_save(
                        lesson,
                        conversation_id,
                        db_path=self.db_path,
                    ),
            ),
            patch(
                "api.lessons.database.get_lesson",
                side_effect=lambda lesson_id:
                    original_get(
                        lesson_id,
                        db_path=self.db_path,
                    ),
            ),
            patch(
                "api.lessons.database.get_lessons",
                side_effect=lambda conversation_id=None:
                    original_list(
                        conversation_id,
                        db_path=self.db_path,
                    ),
            ),
            patch(
                "api.lessons.database.delete_lesson",
                side_effect=lambda lesson_id:
                    original_delete(
                        lesson_id,
                        db_path=self.db_path,
                    ),
            ),
        ]

        for db_patch in self.db_patches:
            db_patch.start()
            self.addCleanup(db_patch.stop)

        app = FastAPI()
        app.include_router(router)

        self.client = TestClient(app)

    def tearDown(self):
        self.temp_dir.cleanup()

    def generate_lesson(self, conversation_id=None):

        with patch(
            "api.lessons.LessonPlanner",
            return_value=FakePlanner(),
        ), patch(
            "api.lessons.ActionGenerator",
            return_value=FakeActionGenerator(),
        ):

            response = self.client.post(
                "/lessons/generate",
                json={
                    "question": "Explain the basics of motion",
                    "subject": "Physics",
                    "difficulty": "beginner",
                    "conversation_id": conversation_id,
                },
            )

        return response

    # -------------------------
    # GENERATION TESTS
    # -------------------------

    def test_generate_lesson_endpoint(self):

        response = self.generate_lesson()

        self.assertEqual(response.status_code, 201)

        data = response.json()

        self.assertTrue(data["success"])
        self.assertEqual(
            data["lesson"]["title"],
            "Introduction to Motion",
        )
        self.assertEqual(len(data["lesson"]["steps"]), 3)

        self.assertEqual(
            data["lesson"]["steps"][0]["visual_actions"][0]["type"],
            "wait",
        )

        # Verify that generation also saved the lesson.
        lesson_id = data["lesson"]["id"]

        saved = self.original_get(
            lesson_id,
            db_path=self.db_path,
        )

        self.assertIsNotNone(saved)
        self.assertEqual(saved["title"], "Introduction to Motion")

    def test_planner_failure_returns_502(self):

        with patch("api.lessons.LessonPlanner") as planner:
            planner.return_value.create_plan.side_effect = (
                LessonPlanningError("Planning failed")
            )

            response = self.client.post(
                "/lessons/generate",
                json={"question": "Explain motion"},
            )

        self.assertEqual(response.status_code, 502)

    def test_action_generator_failure_returns_502(self):

        with patch("api.lessons.LessonPlanner") as planner, \
             patch("api.lessons.ActionGenerator") as generator:

            planner.return_value.create_plan.return_value = {
                "steps": []
            }

            generator.return_value.generate_actions.side_effect = (
                ActionGenerationError("Action generation failed")
            )

            response = self.client.post(
                "/lessons/generate",
                json={"question": "Explain motion"},
            )

        self.assertEqual(response.status_code, 502)

    def test_compiler_failure_returns_422(self):

        with patch("api.lessons.LessonPlanner") as planner, \
             patch("api.lessons.ActionGenerator") as generator, \
             patch("api.lessons.LessonCompiler") as compiler:

            planner.return_value.create_plan.return_value = {
                "steps": []
            }

            generator.return_value.generate_actions.return_value = {
                "steps": []
            }

            compiler.return_value.compile.side_effect = (
                LessonCompilationError("Invalid lesson")
            )

            response = self.client.post(
                "/lessons/generate",
                json={"question": "Explain motion"},
            )

        self.assertEqual(response.status_code, 422)

    def test_empty_question_returns_422(self):

        response = self.client.post(
            "/lessons/generate",
            json={"question": ""},
        )

        self.assertEqual(response.status_code, 422)

    def test_invalid_conversation_returns_404(self):

        response = self.generate_lesson(conversation_id=9999)

        self.assertEqual(response.status_code, 404)

    # -------------------------
    # RETRIEVAL TESTS
    # -------------------------

    def test_list_saved_lessons(self):

        self.generate_lesson()

        response = self.client.get("/lessons")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(
            response.json()[0]["title"],
            "Introduction to Motion",
        )

    def test_filter_lessons_by_conversation(self):

        first_conversation = database.create_conversation(
            "Physics",
            db_path=self.db_path,
        )

        second_conversation = database.create_conversation(
            "Mathematics",
            db_path=self.db_path,
        )

        self.generate_lesson(first_conversation)
        self.generate_lesson(second_conversation)

        response = self.client.get(
            f"/lessons?conversation_id={first_conversation}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(
            response.json()[0]["conversation_id"],
            first_conversation,
        )

    def test_retrieve_saved_lesson(self):

        generated = self.generate_lesson()
        lesson_id = generated.json()["lesson"]["id"]

        response = self.client.get(f"/lessons/{lesson_id}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["lesson"]["title"],
            "Introduction to Motion",
        )
        self.assertEqual(
            len(response.json()["lesson"]["steps"]),
            3,
        )

    def test_missing_lesson_returns_404(self):

        response = self.client.get("/lessons/nonexistent-lesson")

        self.assertEqual(response.status_code, 404)

    # -------------------------
    # DELETION TESTS
    # -------------------------

    def test_delete_saved_lesson(self):

        generated = self.generate_lesson()
        lesson_id = generated.json()["lesson"]["id"]

        response = self.client.delete(f"/lessons/{lesson_id}")

        self.assertEqual(response.status_code, 204)

        retrieve_response = self.client.get(
            f"/lessons/{lesson_id}"
        )

        self.assertEqual(retrieve_response.status_code, 404)

    def test_delete_missing_lesson_returns_404(self):

        response = self.client.delete(
            "/lessons/nonexistent-lesson"
        )

        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
