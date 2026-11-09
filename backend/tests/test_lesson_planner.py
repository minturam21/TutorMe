import unittest

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

    def test_accept_minimum_three_steps(self):
        plan = self.create_valid_plan(3)
        LessonPlanner._validate_plan(plan)

    def test_accept_maximum_six_steps(self):
        plan = self.create_valid_plan(6)
        LessonPlanner._validate_plan(plan)

    def test_reject_fewer_than_three_steps(self):
        plan = self.create_valid_plan(2)

        with self.assertRaises(LessonPlanningError):
            LessonPlanner._validate_plan(plan)

    def test_reject_more_than_six_steps(self):
        plan = self.create_valid_plan(7)

        with self.assertRaises(LessonPlanningError):
            LessonPlanner._validate_plan(plan)

    def test_reject_fewer_than_three_questions(self):
        plan = self.create_valid_plan(3)
        plan["practice_questions"] = plan["practice_questions"][:2]

        with self.assertRaises(LessonPlanningError):
            LessonPlanner._validate_plan(plan)

    def test_reject_more_than_five_questions(self):
        plan = self.create_valid_plan(3)
        plan["practice_questions"] *= 2

        with self.assertRaises(LessonPlanningError):
            LessonPlanner._validate_plan(plan)

if __name__ == "__main__":
    unittest.main()
    