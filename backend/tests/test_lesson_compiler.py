
import unittest

from services.lesson_compiler import (
    LessonCompiler,
    LessonCompilationError,
)


class LessonCompilerTests(unittest.TestCase):

    def setUp(self):
        self.compiler = LessonCompiler()

    def compile_single_action(self, action, initial_scene=None):
        plan = {
            "title": "Test Lesson",
            "subject": "Physics",
            "difficulty": "beginner",
            "objectives": ["Test visual action"],
            "steps": [
                {
                    "id": "step_1",
                    "explanation": "Test visual action.",
                    "visual_actions": [action],
                }
            ],
        }

        if initial_scene is not None:
            plan["initial_scene"] = initial_scene

        return self.compiler.compile(plan)

    def test_scene_snapshot_tracks_created_and_moved_objects(self):
        plan = {
            "title": "Test Lesson",
            "subject": "Physics",
            "difficulty": "beginner",
            "objectives": ["Understand object movement"],
            "steps": [
                {
                    "id": "step_1",
                    "explanation": "Create a circle.",
                    "visual_actions": [
                        {
                            "id": "action_1",
                            "type": "draw_shape",
                            "target_id": "circle_1",
                            "parameters": {
                                "shape": "circle",
                                "x": 100,
                                "y": 100,
                                "width": 60,
                                "height": 60,
                            },
                            "duration": 1,
                            "order": 0,
                        }
                    ],
                },
                {
                    "id": "step_2",
                    "explanation": "Move the circle.",
                    "visual_actions": [
                        {
                            "id": "action_2",
                            "type": "move_object",
                            "target_id": "circle_1",
                            "parameters": {
                                "x": 300,
                                "y": 200,
                            },
                            "duration": 1,
                            "order": 0,
                        }
                    ],
                },
            ],
        }

        lesson = self.compiler.compile(plan)

        first_scene = lesson.steps[0].expected_scene
        second_scene = lesson.steps[1].expected_scene

        self.assertEqual(len(first_scene.objects), 1)
        self.assertEqual(first_scene.objects[0].id, "circle_1")
        self.assertEqual(first_scene.objects[0].properties["x"], 100)

        self.assertEqual(len(second_scene.objects), 1)
        self.assertEqual(second_scene.objects[0].id, "circle_1")
        self.assertEqual(second_scene.objects[0].properties["x"], 300)
        self.assertEqual(second_scene.objects[0].properties["y"], 200)

    def test_erased_object_is_removed_from_snapshot(self):
        plan = {
            "title": "Test Erase",
            "subject": "Physics",
            "difficulty": "beginner",
            "objectives": ["Understand object removal"],
            "steps": [
                {
                    "id": "step_1",
                    "explanation": "Create a rectangle.",
                    "visual_actions": [
                        {
                            "id": "action_1",
                            "type": "draw_shape",
                            "target_id": "rectangle_1",
                            "parameters": {
                                "shape": "rectangle",
                                "x": 100,
                                "y": 100,
                                "width": 100,
                                "height": 60,
                            },
                            "duration": 1,
                            "order": 0,
                        }
                    ],
                },
                {
                    "id": "step_2",
                    "explanation": "Erase the rectangle.",
                    "visual_actions": [
                        {
                            "id": "action_2",
                            "type": "erase_object",
                            "target_id": "rectangle_1",
                            "parameters": {},
                            "duration": 1,
                            "order": 0,
                        }
                    ],
                },
            ],
        }

        lesson = self.compiler.compile(plan)

        self.assertEqual(len(lesson.steps[0].expected_scene.objects), 1)
        self.assertEqual(len(lesson.steps[1].expected_scene.objects), 0)

    def test_rotation_scaling_and_highlighting(self):
        plan = {
            "title": "Test Object Transformations",
            "subject": "Physics",
            "difficulty": "beginner",
            "objectives": ["Understand object transformations"],
            "steps": [
                {
                    "id": "step_1",
                    "explanation": "Create and transform a circle.",
                    "visual_actions": [
                        {
                            "id": "action_1",
                            "type": "draw_shape",
                            "target_id": "circle_1",
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
                            "type": "rotate_object",
                            "target_id": "circle_1",
                            "parameters": {"angle": 45},
                            "duration": 1,
                            "order": 1,
                        },
                        {
                            "id": "action_3",
                            "type": "transform_object",
                            "target_id": "circle_1",
                            "parameters": {
                                "scale_x": 1.5,
                                "scale_y": 2.0,
                            },
                            "duration": 1,
                            "order": 2,
                        },
                        {
                            "id": "action_4",
                            "type": "highlight_object",
                            "target_id": "circle_1",
                            "parameters": {"color": "#FF0000"},
                            "duration": 1,
                            "order": 3,
                        },
                    ],
                }
            ],
        }

        lesson = self.compiler.compile(plan)

        scene = lesson.steps[0].expected_scene
        self.assertEqual(len(scene.objects), 1)

        properties = scene.objects[0].properties

        self.assertEqual(properties["angle"], 45)
        self.assertEqual(properties["scale_x"], 1.5)
        self.assertEqual(properties["scale_y"], 2.0)
        self.assertEqual(properties["highlight_color"], "#FF0000")

    def test_create_object(self):
        lesson = self.compile_single_action({
            "id": "action_1",
            "type": "create_object",
            "target_id": "object_1",
            "parameters": {
                "object_type": "rectangle",
                "x": 100,
                "y": 100,
                "width": 120,
                "height": 80,
            },
            "duration": 1,
            "order": 0,
        })

        obj = lesson.steps[0].expected_scene.objects[0]

        self.assertEqual(obj.type, "rectangle")
        self.assertEqual(obj.properties["width"], 120)

    def test_draw_line(self):
        lesson = self.compile_single_action({
            "id": "action_1",
            "type": "draw_line",
            "target_id": "line_1",
            "parameters": {
                "start_x": 100,
                "start_y": 100,
                "end_x": 300,
                "end_y": 200,
            },
            "duration": 1,
            "order": 0,
        })

        obj = lesson.steps[0].expected_scene.objects[0]

        self.assertEqual(obj.type, "line")
        self.assertEqual(obj.properties["end_x"], 300)

    def test_draw_arrow(self):
        lesson = self.compile_single_action({
            "id": "action_1",
            "type": "draw_arrow",
            "target_id": "arrow_1",
            "parameters": {
                "start_x": 100,
                "start_y": 100,
                "end_x": 300,
                "end_y": 100,
            },
            "duration": 1,
            "order": 0,
        })

        obj = lesson.steps[0].expected_scene.objects[0]

        self.assertEqual(obj.type, "arrow")
        self.assertEqual(obj.properties["end_x"], 300)

    def test_draw_path(self):
        lesson = self.compile_single_action({
            "id": "action_1",
            "type": "draw_path",
            "target_id": "path_1",
            "parameters": {
                "points": [[100, 100], [200, 150], [300, 100]],
                "closed": False,
            },
            "duration": 1,
            "order": 0,
        })

        obj = lesson.steps[0].expected_scene.objects[0]

        self.assertEqual(obj.type, "path")
        self.assertEqual(len(obj.properties["points"]), 3)

    def test_write_text(self):
        lesson = self.compile_single_action({
            "id": "action_1",
            "type": "write_text",
            "target_id": "text_1",
            "parameters": {
                "text": "Force",
                "x": 100,
                "y": 100,
            },
            "duration": 1,
            "order": 0,
        })

        obj = lesson.steps[0].expected_scene.objects[0]

        self.assertEqual(obj.type, "text")
        self.assertEqual(obj.properties["text"], "Force")

    def test_write_equation(self):
        lesson = self.compile_single_action({
            "id": "action_1",
            "type": "write_equation",
            "target_id": "equation_1",
            "parameters": {
                "equation": "F = ma",
                "x": 100,
                "y": 100,
            },
            "duration": 1,
            "order": 0,
        })

        obj = lesson.steps[0].expected_scene.objects[0]

        self.assertEqual(obj.type, "equation")
        self.assertEqual(obj.properties["equation"], "F = ma")

    def test_move_nonexistent_object_rejected(self):
        with self.assertRaises(LessonCompilationError):
            self.compile_single_action({
                "id": "action_1",
                "type": "move_object",
                "target_id": "missing_object",
                "parameters": {"x": 200, "y": 200},
                "duration": 1,
                "order": 0,
            })

    def test_erase_nonexistent_object_rejected(self):
        with self.assertRaises(LessonCompilationError):
            self.compile_single_action({
                "id": "action_1",
                "type": "erase_object",
                "target_id": "missing_object",
                "parameters": {},
                "duration": 1,
                "order": 0,
            })

    def test_duplicate_active_object_creation_rejected(self):
        plan = {
            "title": "Duplicate Object Test",
            "subject": "Physics",
            "difficulty": "beginner",
            "objectives": ["Test duplicate objects"],
            "steps": [
                {
                    "id": "step_1",
                    "explanation": "Create duplicate objects.",
                    "visual_actions": [
                        {
                            "id": "action_1",
                            "type": "draw_shape",
                            "target_id": "circle_1",
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
                            "type": "draw_shape",
                            "target_id": "circle_1",
                            "parameters": {
                                "shape": "rectangle",
                                "x": 200,
                                "y": 200,
                                "width": 100,
                                "height": 80,
                            },
                            "duration": 1,
                            "order": 1,
                        },
                    ],
                }
            ],
        }

        with self.assertRaises(LessonCompilationError):
            self.compiler.compile(plan)

    def test_unsupported_action_rejected(self):
        plan = {
            "title": "Unsupported Action Test",
            "subject": "Physics",
            "difficulty": "beginner",
            "objectives": ["Test unsupported actions"],
            "steps": [
                {
                    "id": "step_1",
                    "explanation": "Create an object.",
                    "visual_actions": [
                        {
                            "id": "action_1",
                            "type": "draw_shape",
                            "target_id": "circle_1",
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
                            "type": "unsupported_action",
                            "target_id": "circle_1",
                            "parameters": {},
                            "duration": 1,
                            "order": 1,
                        },
                    ],
                }
            ],
        }

        with self.assertRaises(LessonCompilationError):
            self.compiler.compile(plan)

    def test_erase_and_recreate_object_across_steps(self):
        plan = {
            "title": "Erase and Recreate Test",
            "subject": "Physics",
            "difficulty": "beginner",
            "objectives": ["Test object lifecycle"],
            "steps": [
                {
                    "id": "step_1",
                    "explanation": "Create a circle.",
                    "visual_actions": [
                        {
                            "id": "action_1",
                            "type": "draw_shape",
                            "target_id": "object_1",
                            "parameters": {
                                "shape": "circle",
                                "x": 100,
                                "y": 100,
                                "width": 60,
                                "height": 60,
                            },
                            "duration": 1,
                            "order": 0,
                        }
                    ],
                },
                {
                    "id": "step_2",
                    "explanation": "Erase the circle.",
                    "visual_actions": [
                        {
                            "id": "action_2",
                            "type": "erase_object",
                            "target_id": "object_1",
                            "parameters": {},
                            "duration": 1,
                            "order": 0,
                        }
                    ],
                },
                {
                    "id": "step_3",
                    "explanation": "Create a rectangle using the same ID.",
                    "visual_actions": [
                        {
                            "id": "action_3",
                            "type": "draw_shape",
                            "target_id": "object_1",
                            "parameters": {
                                "shape": "rectangle",
                                "x": 300,
                                "y": 200,
                                "width": 100,
                                "height": 80,
                            },
                            "duration": 1,
                            "order": 0,
                        }
                    ],
                },
            ],
        }

        lesson = self.compiler.compile(plan)

        first_scene = lesson.steps[0].expected_scene
        second_scene = lesson.steps[1].expected_scene
        third_scene = lesson.steps[2].expected_scene

        self.assertEqual(len(first_scene.objects), 1)
        self.assertEqual(first_scene.objects[0].type, "circle")

        self.assertEqual(len(second_scene.objects), 0)

        self.assertEqual(len(third_scene.objects), 1)
        self.assertEqual(third_scene.objects[0].id, "object_1")
        self.assertEqual(third_scene.objects[0].type, "rectangle")
        self.assertEqual(third_scene.objects[0].properties["x"], 300)

    # Initial scene tests

    def test_initial_scene_objects_are_preserved(self):
        initial_scene = {
            "objects": [
                {
                    "id": "circle_1",
                    "type": "circle",
                    "properties": {
                        "x": 100,
                        "y": 100,
                        "radius": 30,
                    },
                }
            ]
        }

        lesson = self.compile_single_action(
            {
                "id": "action_1",
                "type": "wait",
                "parameters": {},
                "duration": 1,
                "order": 0,
            },
            initial_scene=initial_scene,
        )

        self.assertEqual(len(lesson.initial_scene.objects), 1)
        self.assertEqual(
            lesson.initial_scene.objects[0].id,
            "circle_1",
        )
        self.assertEqual(
            lesson.steps[0].expected_scene.objects[0].id,
            "circle_1",
        )

    def test_initial_scene_object_can_be_moved(self):
        initial_scene = {
            "objects": [
                {
                    "id": "circle_1",
                    "type": "circle",
                    "properties": {
                        "x": 100,
                        "y": 100,
                        "radius": 30,
                    },
                }
            ]
        }

        lesson = self.compile_single_action(
            {
                "id": "action_1",
                "type": "move_object",
                "target_id": "circle_1",
                "parameters": {
                    "x": 300,
                    "y": 200,
                },
                "duration": 1,
                "order": 0,
            },
            initial_scene=initial_scene,
        )

        obj = lesson.steps[0].expected_scene.objects[0]

        self.assertEqual(obj.id, "circle_1")
        self.assertEqual(obj.properties["x"], 300)
        self.assertEqual(obj.properties["y"], 200)

    def test_duplicate_initial_object_ids_rejected(self):
        initial_scene = {
            "objects": [
                {
                    "id": "object_1",
                    "type": "circle",
                    "properties": {},
                },
                {
                    "id": "object_1",
                    "type": "rectangle",
                    "properties": {},
                },
            ]
        }

        with self.assertRaises(LessonCompilationError):
            self.compile_single_action(
                {
                    "id": "action_1",
                    "type": "wait",
                    "parameters": {},
                    "duration": 1,
                    "order": 0,
                },
                initial_scene=initial_scene,
            )

    def test_unsupported_initial_object_type_rejected(self):
        initial_scene = {
            "objects": [
                {
                    "id": "object_1",
                    "type": "unknown_type",
                    "properties": {},
                }
            ]
        }

        with self.assertRaises(LessonCompilationError):
            self.compile_single_action(
                {
                    "id": "action_1",
                    "type": "wait",
                    "parameters": {},
                    "duration": 1,
                    "order": 0,
                },
                initial_scene=initial_scene,
            )

    def test_invalid_initial_scene_rejected(self):
        initial_scene = {
            "objects": "not_a_list"
        }

        with self.assertRaises(LessonCompilationError):
            self.compile_single_action(
                {
                    "id": "action_1",
                    "type": "wait",
                    "parameters": {},
                    "duration": 1,
                    "order": 0,
                },
                initial_scene=initial_scene,
            )


if __name__ == "__main__":
    unittest.main()
