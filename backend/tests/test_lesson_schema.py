
import unittest
import copy

from models.lesson import Lesson
from services.lesson_validator import (
    validate_lesson,
    LessonValidationError,
)


class LessonSchemaTests(unittest.TestCase):

    def setUp(self):
        self.valid_lesson = {
            "id": "lesson_001",
            "title": "Introduction to Motion",
            "subject": "Physics",
            "difficulty": "beginner",
            "objectives": ["Understand basic motion"],
            "initial_scene": {
                "objects": [
                    {
                        "id": "object_1",
                        "type": "circle",
                        "properties": {
                            "x": 100,
                            "y": 100,
                            "radius": 20,
                        },
                    }
                ]
            },
            "steps": [
                {
                    "id": "step_1",
                    "explanation": "A moving object changes its position.",
                    "equations": ["speed = distance / time"],
                    "visual_actions": [
                        {
                            "id": "action_1",
                            "type": "move_object",
                            "target_id": "object_1",
                            "parameters": {"x": 200, "y": 100},
                            "duration": 1,
                            "easing": "ease_in_out",
                            "order": 0,
                        }
                    ],
                    "expected_scene": {
                        "objects": [
                            {
                                "id": "object_1",
                                "type": "circle",
                                "properties": {
                                    "x": 200,
                                    "y": 100,
                                    "radius": 20,
                                },
                            }
                        ]
                    },
                    "duration": 5,
                }
            ],
            "practice_questions": [
                {
                    "question": "What is speed?",
                    "answer": "Distance divided by time.",
                    "explanation": (
                        "Speed measures the distance travelled "
                        "per unit of time."
                    ),
                }
            ],
            "version": 1,
        }

    def test_valid_lesson(self):
        lesson = validate_lesson(self.valid_lesson)
        self.assertIsInstance(lesson, Lesson)

    def test_invalid_action_type(self):
        data = copy.deepcopy(self.valid_lesson)
        data["steps"][0]["visual_actions"][0]["type"] = "unknown_action"

        with self.assertRaises(LessonValidationError):
            validate_lesson(data)

    def test_duplicate_initial_object_ids(self):
        data = copy.deepcopy(self.valid_lesson)
        data["initial_scene"]["objects"] = [
            {"id": "same_id", "type": "circle"},
            {"id": "same_id", "type": "rectangle"},
        ]

        with self.assertRaises(LessonValidationError):
            validate_lesson(data)

    def test_create_then_move_object(self):
        data = copy.deepcopy(self.valid_lesson)
        data["initial_scene"]["objects"] = []

        data["steps"][0]["visual_actions"] = [
            {
                "id": "action_1",
                "type": "draw_shape",
                "target_id": "new_circle",
                "parameters": {
                    "shape": "circle",
                    "x": 100,
                    "y": 100,
                    "width": 60,
                    "height": 60,
                },
                "duration": 1,
                "order": 0,
            },
            {
                "id": "action_2",
                "type": "move_object",
                "target_id": "new_circle",
                "parameters": {
                    "x": 200,
                    "y": 100,
                },
                "duration": 1,
                "order": 1,
            },
        ]

        data["steps"][0]["expected_scene"] = {
            "objects": [
                {
                    "id": "new_circle",
                    "type": "circle",
                    "properties": {
                        "x": 200,
                        "y": 100,
                        "width": 60,
                        "height": 60,
                    },
                }
            ]
        }

        lesson = validate_lesson(data)
        self.assertIsInstance(lesson, Lesson)

    def test_move_nonexistent_object(self):
        data = copy.deepcopy(self.valid_lesson)
        data["steps"][0]["visual_actions"][0]["target_id"] = (
            "missing_object"
        )

        with self.assertRaises(LessonValidationError):
            validate_lesson(data)

    def test_duplicate_object_creation(self):
        data = copy.deepcopy(self.valid_lesson)
        data["initial_scene"]["objects"] = []

        data["steps"][0]["visual_actions"] = [
            {
                "id": "action_1",
                "type": "draw_shape",
                "target_id": "block_1",
                "parameters": {
                    "shape": "rectangle",
                    "x": 100,
                    "y": 100,
                    "width": 100,
                    "height": 80,
                },
                "duration": 1,
                "order": 0,
            },
            {
                "id": "action_2",
                "type": "draw_shape",
                "target_id": "block_1",
                "parameters": {
                    "shape": "circle",
                    "x": 200,
                    "y": 200,
                    "width": 60,
                    "height": 60,
                },
                "duration": 1,
                "order": 1,
            },
        ]

        with self.assertRaises(LessonValidationError):
            validate_lesson(data)

    def test_move_object_after_erasing(self):
        data = copy.deepcopy(self.valid_lesson)

        data["steps"][0]["visual_actions"] = [
            {
                "id": "action_1",
                "type": "erase_object",
                "target_id": "object_1",
                "duration": 0.5,
                "order": 0,
            },
            {
                "id": "action_2",
                "type": "move_object",
                "target_id": "object_1",
                "parameters": {
                    "x": 200,
                    "y": 100,
                },
                "duration": 1,
                "order": 1,
            },
        ]

        with self.assertRaises(LessonValidationError):
            validate_lesson(data)

    def test_erase_then_recreate_object(self):
        data = copy.deepcopy(self.valid_lesson)

        data["steps"][0]["visual_actions"] = [
            {
                "id": "action_1",
                "type": "erase_object",
                "target_id": "object_1",
                "duration": 0.5,
                "order": 0,
            },
            {
                "id": "action_2",
                "type": "draw_shape",
                "target_id": "object_1",
                "parameters": {
                    "shape": "rectangle",
                    "x": 100,
                    "y": 100,
                    "width": 120,
                    "height": 80,
                },
                "duration": 1,
                "order": 1,
            },
        ]

        data["steps"][0]["expected_scene"] = {
            "objects": [
                {
                    "id": "object_1",
                    "type": "rectangle",
                    "properties": {
                        "x": 100,
                        "y": 100,
                        "width": 120,
                        "height": 80,
                    },
                }
            ]
        }

        lesson = validate_lesson(data)
        self.assertIsInstance(lesson, Lesson)

    def test_reject_infinite_parameter(self):
        data = copy.deepcopy(self.valid_lesson)

        data["steps"][0]["visual_actions"][0]["parameters"] = {
            "x": float("inf"),
            "y": 100,
        }

        with self.assertRaises(LessonValidationError):
            validate_lesson(data)

    def test_duplicate_action_ids_across_steps(self):
        data = copy.deepcopy(self.valid_lesson)

        data["steps"].append(
            {
                "id": "step_2",
                "explanation": "Continue the lesson.",
                "equations": [],
                "visual_actions": [
                    {
                        "id": "action_1",
                        "type": "wait",
                        "parameters": {},
                        "duration": 0,
                        "order": 0,
                    }
                ],
                "expected_scene": {
                    "objects": [
                        {
                            "id": "object_1",
                            "type": "circle",
                            "properties": {
                                "x": 200,
                                "y": 100,
                                "radius": 20,
                            },
                        }
                    ]
                },
                "duration": 5,
            }
        )

        with self.assertRaises(LessonValidationError):
            validate_lesson(data)

    def test_accept_path_and_equation_initial_objects(self):
        data = {
            "id": "lesson_1",
            "title": "Test Lesson",
            "subject": "Physics",
            "difficulty": "beginner",
            "initial_scene": {
                "objects": [
                    {
                        "id": "path_1",
                        "type": "path",
                        "properties": {
                            "points": [[100, 100], [200, 200]]
                        },
                    },
                    {
                        "id": "equation_1",
                        "type": "equation",
                        "properties": {
                            "equation": "F = ma"
                        },
                    },
                ]
            },
            "steps": [
                {
                    "id": "step_1",
                    "explanation": "Test step",
                    "visual_actions": [],
                    "expected_scene": {
                        "objects": [
                            {
                                "id": "path_1",
                                "type": "path",
                                "properties": {
                                    "points": [[100, 100], [200, 200]]
                                },
                            },
                            {
                                "id": "equation_1",
                                "type": "equation",
                                "properties": {
                                    "equation": "F = ma"
                                },
                            },
                        ]
                    },
                }
            ],
        }

        lesson = validate_lesson(data)

        self.assertEqual(len(lesson.initial_scene.objects), 2)

    def test_reject_more_than_500_visual_actions(self):
        data = copy.deepcopy(self.valid_lesson)

        data["steps"][0]["visual_actions"] = [
            {
                "id": f"action_{i}",
                "type": "wait",
                "parameters": {},
                "duration": 0,
                "order": i,
            }
            for i in range(501)
        ]

        with self.assertRaises(LessonValidationError):
            validate_lesson(data)

    def test_reject_total_duration_over_3600_seconds(self):
        data = copy.deepcopy(self.valid_lesson)

        data["steps"][0]["visual_actions"] = [
            {
                "id": f"action_{i}",
                "type": "wait",
                "parameters": {},
                "duration": 60,
                "order": i,
            }
            for i in range(61)
        ]

        with self.assertRaises(LessonValidationError):
            validate_lesson(data)

    def test_accept_total_duration_of_exactly_3600_seconds(self):
        data = copy.deepcopy(self.valid_lesson)

        data["steps"][0]["visual_actions"] = [
            {
                "id": f"action_{i}",
                "type": "wait",
                "parameters": {},
                "duration": 60,
                "order": i,
            }
            for i in range(60)
        ]

        # Wait actions do not change the scene.
        # The original circle remains at x=100, y=100.
        data["steps"][0]["expected_scene"] = {
            "objects": [
                {
                    "id": "object_1",
                    "type": "circle",
                    "properties": {
                        "x": 100,
                        "y": 100,
                        "radius": 20,
                    },
                }
            ]
        }

        lesson = validate_lesson(data)
        self.assertIsInstance(lesson, Lesson)

    def test_reject_expected_scene_missing_object(self):
        data = copy.deepcopy(self.valid_lesson)
        data["steps"][0]["expected_scene"] = {"objects": []}

        with self.assertRaises(LessonValidationError):
            validate_lesson(data)

    def test_reject_duplicate_expected_scene_object_ids(self):
        data = copy.deepcopy(self.valid_lesson)

        obj = {
            "id": "object_1",
            "type": "circle",
            "properties": {
                "x": 200,
                "y": 100,
                "radius": 20,
            },
        }

        data["steps"][0]["expected_scene"] = {
            "objects": [obj, copy.deepcopy(obj)]
        }

        with self.assertRaises(LessonValidationError):
            validate_lesson(data)

    def test_reject_unsupported_expected_scene_object_type(self):
        data = copy.deepcopy(self.valid_lesson)

        data["steps"][0]["expected_scene"]["objects"][0]["type"] = (
            "unknown"
        )

        with self.assertRaises(LessonValidationError):
            validate_lesson(data)

    def test_reject_expected_scene_incorrect_position(self):
        data = copy.deepcopy(self.valid_lesson)

        data["steps"][0]["expected_scene"]["objects"][0]["properties"]["x"] = 900

        with self.assertRaises(LessonValidationError):
            validate_lesson(data)

    def test_reject_expected_scene_incorrect_dimensions(self):
        data = copy.deepcopy(self.valid_lesson)

        data["steps"][0]["expected_scene"]["objects"][0]["properties"]["radius"] = 50

        with self.assertRaises(LessonValidationError):
            validate_lesson(data)

    def test_reject_expected_scene_incorrect_transform(self):
        data = copy.deepcopy(self.valid_lesson)

        data["steps"][0]["visual_actions"].append({
            "id": "action_2",
            "type": "transform_object",
            "target_id": "object_1",
            "parameters": {
                "scale_x": 2,
                "scale_y": 3,
            },
            "duration": 1,
            "order": 1,
        })

        data["steps"][0]["expected_scene"]["objects"][0]["properties"].update({
            "scale_x": 4,
            "scale_y": 3,
        })

        with self.assertRaises(LessonValidationError):
            validate_lesson(data)


if __name__ == "__main__":
    unittest.main()
