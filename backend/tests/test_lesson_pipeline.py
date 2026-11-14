
import json
import unittest

from services.lesson_planner import LessonPlanner
from services.action_generator import ActionGenerator
from services.lesson_compiler import LessonCompiler


class FakeAIProvider:
    def __init__(self, response):
        self.response = response

    def generate_response(self, **kwargs):
        return self.response


class LessonPipelineTests(unittest.TestCase):

    def setUp(self):
        self.plan_response = {
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
                    "visual_goal": "Introduce the concept",
                    "visual_requirements": ["Show a diagram"],
                    "teaching_events": [
                        {
                            "id": f"event_{i}_1",
                            "explanation": "Introduce the idea of position.",
                            "visual_goal": "Write the word position.",
                            "visual_requirements": ["Handwrite the word Position"],
                        },
                        {
                            "id": f"event_{i}_2",
                            "explanation": "Explain that position changes over time.",
                            "visual_goal": "Show a moving object.",
                            "visual_requirements": ["Draw an object and its changed position"],
                        },
                    ],
                }
                for i in range(1, 4)
            ],
            "practice_questions": [
                {
                    "question": "What is motion?",
                    "answer": "Change in position over time.",
                    "explanation": "An object is in motion when its position changes.",
                },
                {
                    "question": "What measures duration?",
                    "answer": "Time.",
                    "explanation": "Time measures the duration of an event.",
                },
                {
                    "question": "What describes an object's location?",
                    "answer": "Position.",
                    "explanation": "Position describes where an object is.",
                },
            ],
        }

        self.action_response = {
            "steps": [
                {
                    "id": f"step_{i}",
                    "teaching_events": [
                        {
                            "id": f"event_{i}_1",
                            "visual_actions": [
                                {
                                    "id": f"note_{i}",
                                    "type": "write_text",
                                    "target_id": f"step_{i}_note",
                                    "parameters": {
                                        "text": "Motion is a change in position",
                                        "x": 100,
                                        "y": 100,
                                    },
                                    "duration": 2,
                                    "easing": "linear",
                                    "order": 0,
                                }
                            ],
                        },
                        {
                            "id": f"event_{i}_2",
                            "visual_actions": [
                                {
                                    "id": f"diagram_{i}",
                                    "type": "draw_shape",
                                    "target_id": f"step_{i}_circle",
                                    "parameters": {
                                        "shape": "circle",
                                        "x": 300,
                                        "y": 200,
                                        "width": 60,
                                        "height": 60,
                                    },
                                    "duration": 1,
                                    "easing": "linear",
                                    "order": 0,
                                }
                            ],
                        },
                    ],
                }
                for i in range(1, 4)
            ]
        }

    def test_complete_lesson_pipeline(self):
        # Step 1: Generate teaching plan
        planner = LessonPlanner(
            FakeAIProvider(json.dumps(self.plan_response))
        )

        plan = planner.create_plan(
            question="Explain the basics of motion",
            subject="Physics",
            difficulty="beginner",
        )

        self.assertEqual(len(plan["steps"]), 3)

        # Step 2: Generate visual actions
        action_generator = ActionGenerator(
            FakeAIProvider(json.dumps(self.action_response))
        )

        plan_with_actions = action_generator.generate_actions(plan)

        self.assertEqual(
            len(plan_with_actions["steps"]),
            3,
        )

        # Step 3: Compile and validate lesson
        compiler = LessonCompiler()
        lesson = compiler.compile(plan_with_actions)

        # Step 4: Verify final lesson
        self.assertEqual(
            lesson.title,
            "Introduction to Motion",
        )

        self.assertEqual(len(lesson.steps), 3)

        for step_index, step in enumerate(lesson.steps):
            action_types = [
                action.type
                for action in step.visual_actions
            ]

            self.assertIn("write_text", action_types)
            self.assertIn("draw_shape", action_types)

            self.assertEqual(len(step.visual_actions), 2)
            self.assertEqual(len(step.teaching_events), 2)

            first_event_objects = step.teaching_events[0].expected_scene.objects
            second_event_objects = step.teaching_events[1].expected_scene.objects

            # The board persists across steps. The first event adds this
            # step's note without removing earlier notes or diagrams.
            self.assertEqual(
                sum(obj.type == "text" for obj in first_event_objects),
                step_index + 1,
            )
            self.assertEqual(
                sum(obj.type == "circle" for obj in first_event_objects),
                step_index,
            )

            # The second event adds this step's circle while preserving
            # everything already visible from prior events and steps.
            self.assertEqual(
                sum(obj.type == "text" for obj in second_event_objects),
                step_index + 1,
            )
            self.assertEqual(
                sum(obj.type == "circle" for obj in second_event_objects),
                step_index + 1,
            )

            scene_types = [
                scene_object.type
                for scene_object in step.expected_scene.objects
            ]

            self.assertIn("text", scene_types)
            self.assertIn("circle", scene_types)


if __name__ == "__main__":
    unittest.main()
