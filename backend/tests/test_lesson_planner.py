import json
import unittest
from unittest.mock import Mock

from services.lesson_planner import (
    LessonPlanner,
    LessonPlanningError,
)


class LessonPlannerTests(unittest.TestCase):

    def create_valid_plan(self, step_count):
        steps = []

        for i in range(step_count):
            steps.append({
                "id": f"step_{i + 1}",
                "teaching_goal": "Understand the concept",
                "explanation": "A simple explanation.",
                "key_concepts": ["Concept"],
                "equations": [],
                "visual_goal": "Show the concept",
                "visual_requirements": ["Draw a diagram"],
                "teaching_events": [
                    {
                        "id": f"event_{i + 1}_1",
                        "explanation": "Introduce the concept.",
                        "visual_goal": "Write the concept name.",
                        "visual_requirements": ["Handwrite the concept name"],
                    },
                    {
                        "id": f"event_{i + 1}_2",
                        "explanation": "Explain its effect.",
                        "visual_goal": "Draw the related visual.",
                        "visual_requirements": ["Draw the related visual"],
                    },
                ],
            })

        return {
            "title": "Test Lesson",
            "subject": "Physics",
            "topic": "Motion",
            "difficulty": "beginner",
            "objectives": ["Understand motion"],
            "steps": steps,
            "practice_questions": [
                {
                    "question": "What is speed?",
                    "answer": "Distance divided by time.",
                    "explanation": "Speed measures distance per unit time.",
                },
                {
                    "question": "What is distance?",
                    "answer": "Length travelled.",
                    "explanation": "Distance measures how far an object travels.",
                },
                {
                    "question": "What is time?",
                    "answer": "Duration of an event.",
                    "explanation": "Time measures how long something takes.",
                },
            ],
        }

    def create_planner(self, responses):
        provider = Mock()
        provider.generate_response.side_effect = [
            json.dumps(response) if isinstance(response, dict) else response
            for response in responses
        ]
        return LessonPlanner(ai_provider=provider), provider

    def test_accept_minimum_three_steps(self):
        plan = self.create_valid_plan(3)
        LessonPlanner._validate_plan(plan)

    def test_accept_maximum_six_steps(self):
        plan = self.create_valid_plan(6)
        LessonPlanner._validate_plan(plan)

    def test_accept_plan_when_optional_practice_questions_are_omitted(self):
        plan = self.create_valid_plan(3)
        del plan["practice_questions"]

        LessonPlanner._validate_plan(plan)
        self.assertEqual(plan["practice_questions"], [])

    def test_step_count_error_reports_actual_allowed_range_and_count(self):
        plan = self.create_valid_plan(2)

        with self.assertRaisesRegex(
            LessonPlanningError,
            "between 3 and 6 steps; received 2",
        ):
            LessonPlanner._validate_plan(plan)

    def test_reject_fewer_than_three_steps(self):
        plan = self.create_valid_plan(2)

        with self.assertRaises(LessonPlanningError):
            LessonPlanner._validate_plan(plan)

    def test_reject_more_than_six_steps(self):
        plan = self.create_valid_plan(7)

        with self.assertRaises(LessonPlanningError):
            LessonPlanner._validate_plan(plan)

    def test_accept_fewer_than_three_optional_questions(self):
        plan = self.create_valid_plan(3)
        plan["practice_questions"] = plan["practice_questions"][:2]

        LessonPlanner._validate_plan(plan)
        self.assertEqual(len(plan["practice_questions"]), 2)

    def test_reject_more_than_five_questions(self):
        plan = self.create_valid_plan(3)
        plan["practice_questions"] *= 2

        with self.assertRaises(LessonPlanningError):
            LessonPlanner._validate_plan(plan)

    def test_retries_when_ai_returns_too_many_steps_then_recovers(self):
        invalid_plan = self.create_valid_plan(10)
        valid_plan = self.create_valid_plan(4)
        planner, provider = self.create_planner([invalid_plan, valid_plan])

        result = planner.create_plan("How does gravity work?")

        self.assertEqual(len(result["steps"]), 4)
        self.assertEqual(provider.generate_response.call_count, 2)
        retry_messages = provider.generate_response.call_args_list[1].kwargs["messages"]
        self.assertIn("received 10", retry_messages[1]["content"])
        self.assertIn("at most 6", retry_messages[1]["content"])

    def test_fails_clearly_when_retry_still_has_invalid_step_count(self):
        planner, provider = self.create_planner([
            self.create_valid_plan(10),
            self.create_valid_plan(8),
        ])

        with self.assertRaisesRegex(
            LessonPlanningError,
            "failed after 2 attempts.*received 8",
        ):
            planner.create_plan("How does gravity work?")

        self.assertEqual(provider.generate_response.call_count, 2)

    def test_does_not_retry_provider_errors(self):
        provider = Mock()
        provider.generate_response.side_effect = RuntimeError("provider unavailable")
        planner = LessonPlanner(ai_provider=provider)

        with self.assertRaisesRegex(
            LessonPlanningError,
            "Lesson planning failed: provider unavailable",
        ):
            planner.create_plan("How does gravity work?")

        self.assertEqual(provider.generate_response.call_count, 1)


if __name__ == "__main__":
    unittest.main()
