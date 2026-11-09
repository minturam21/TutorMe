
import json
import unittest

from services.action_generator import (
    ActionGenerator,
    ActionGenerationError,
)


class FakeAIProvider:
    def __init__(self, response):
        self.response = response

    def generate_response(self, **kwargs):
        return self.response


class ActionGeneratorTests(unittest.TestCase):

    def setUp(self):
        self.plan = {
            "title": "Test Lesson",
            "steps": [
                {
                    "id": "step_1",
                    "explanation": "Test explanation",
                    "equations": [],
                    "teaching_events": [{"id": "event_1", "explanation": "Test segment"}],
                }
            ],
        }

    def make_action(
        self,
        action_id,
        action_type,
        order,
        parameters=None,
        target_id=None,
    ):
        return {
            "id": action_id,
            "type": action_type,
            "target_id": target_id,
            "parameters": parameters or {},
            "duration": 1,
            "easing": "linear",
            "order": order,
        }

    def make_handwritten_note(self, action_id="action_note", order=0):
        return self.make_action(
            action_id,
            "write_text",
            order,
            {
                "text": "Force causes acceleration",
                "x": 100,
                "y": 100,
            },
            target_id="step_1_note",
        )

    def make_circle(self, action_id="action_circle", order=1):
        return self.make_action(
            action_id,
            "draw_shape",
            order,
            {
                "shape": "circle",
                "x": 300,
                "y": 200,
                "width": 60,
                "height": 60,
            },
            target_id="step_1_circle",
        )

    def make_equation(self, action_id="action_equation", order=2):
        return self.make_action(
            action_id,
            "write_equation",
            order,
            {
                "equation": "F = ma",
                "x": 100,
                "y": 200,
            },
            target_id="step_1_equation",
        )

    def generate(self, actions):
        response = {
            "steps": [
                {
                    "id": "step_1",
                    "teaching_events": [{"id": "event_1", "visual_actions": actions}],
                }
            ]
        }

        generator = ActionGenerator(
            FakeAIProvider(json.dumps(response))
        )

        return generator.generate_actions(self.plan)

    def test_accept_valid_generated_action(self):
        result = self.generate([
            self.make_handwritten_note(),
            self.make_circle(),
        ])

        self.assertEqual(
            len(result["steps"][0]["visual_actions"]),
            2,
        )

        self.assertEqual(
            result["steps"][0]["visual_actions"][0]["type"],
            "write_text",
        )

    def test_accept_wait_alongside_visual_action(self):
        result = self.generate([
            self.make_action("action_1", "wait", 0),
            self.make_handwritten_note("action_2", 1),
            self.make_circle("action_3", 2),
        ])

        self.assertEqual(
            len(result["steps"][0]["visual_actions"]),
            3,
        )

    def test_reject_empty_visual_actions(self):
        with self.assertRaises(ActionGenerationError):
            self.generate([])

    def test_reject_wait_only_visual_actions(self):
        with self.assertRaises(ActionGenerationError):
            self.generate([
                self.make_action("action_1", "wait", 0),
                self.make_action("action_2", "wait", 1),
            ])

    def test_reject_missing_handwritten_note(self):
        with self.assertRaises(ActionGenerationError):
            self.generate([
                self.make_circle(),
            ])

    def test_reject_empty_handwritten_note(self):
        with self.assertRaises(ActionGenerationError):
            self.generate([
                self.make_action(
                    "action_1",
                    "write_text",
                    0,
                    {
                        "text": "   ",
                        "x": 100,
                        "y": 100,
                    },
                    target_id="step_1_note",
                ),
                self.make_circle(),
            ])

    def test_accept_handwritten_equation(self):
        self.plan["steps"][0]["equations"] = ["F = ma"]

        result = self.generate([
            self.make_handwritten_note(),
            self.make_equation(),
        ])

        self.assertEqual(
            len(result["steps"][0]["visual_actions"]),
            2,
        )

    def test_reject_missing_handwritten_equation(self):
        self.plan["steps"][0]["equations"] = ["F = ma"]

        with self.assertRaises(ActionGenerationError):
            self.generate([
                self.make_handwritten_note(),
                self.make_circle(),
            ])

    def test_reject_empty_handwritten_equation(self):
        self.plan["steps"][0]["equations"] = ["F = ma"]

        with self.assertRaises(ActionGenerationError):
            self.generate([
                self.make_handwritten_note(),
                self.make_action(
                    "action_2",
                    "write_equation",
                    1,
                    {
                        "equation": "   ",
                        "x": 100,
                        "y": 200,
                    },
                    target_id="step_1_equation",
                ),
            ])

    def test_reject_invalid_json(self):
        generator = ActionGenerator(
            FakeAIProvider("This is not JSON")
        )

        with self.assertRaises(ActionGenerationError):
            generator.generate_actions(self.plan)

    def test_reject_mismatched_step_ids(self):
        response = {
            "steps": [
                {
                    "id": "wrong_step",
                    "visual_actions": [],
                }
            ]
        }

        generator = ActionGenerator(
            FakeAIProvider(json.dumps(response))
        )

        with self.assertRaises(ActionGenerationError):
            generator.generate_actions(self.plan)

    def test_reject_duplicate_action_ids(self):
        with self.assertRaises(ActionGenerationError):
            self.generate([
                self.make_action("action_1", "wait", 0),
                self.make_action("action_1", "wait", 1),
            ])

    def test_reject_invalid_action_parameters(self):
        with self.assertRaises(ActionGenerationError):
            self.generate([
                self.make_action(
                    "action_1",
                    "write_text",
                    0,
                    {
                        "text": "Hello",
                        "x": 2500,
                        "y": 100,
                    },
                    target_id="step_1_note",
                ),
                self.make_circle(),
            ])

    def test_reject_empty_steps(self):
        invalid_plan = {
            "title": "Empty Lesson",
            "steps": [],
        }

        generator = ActionGenerator(
            FakeAIProvider("{}")
        )

        with self.assertRaises(ActionGenerationError):
            generator.generate_actions(invalid_plan)


    def test_action_order_is_assigned_by_array_position(self):
        note = self.make_handwritten_note()
        circle = self.make_circle()

        # Simulate the AI omitting order and supplying an incorrect order.
        note.pop("order")
        circle["order"] = 99

        result = self.generate([note, circle])

        actions = result["steps"][0]["visual_actions"]

        self.assertEqual(
            [action["order"] for action in actions],
            [0, 1],
        )

    def test_reject_non_dictionary_action(self):
        with self.assertRaises(ActionGenerationError):
            self.generate([
                None,
                self.make_handwritten_note(),
            ])



if __name__ == "__main__":
    unittest.main()
