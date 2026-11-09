
import json
import unittest

from services.action_generator import (
    ActionGenerator,
    ActionGenerationError,
)
from services.action_response_schema import PARAMETER_KEYS


class FakeAIProvider:
    def __init__(self, response):
        self.response = response

    def generate_response(self, **kwargs):
        return self.response


class SequenceAIProvider:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def generate_response(self, **kwargs):
        self.calls.append(kwargs)
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


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

    def test_uses_strict_json_schema_contract_and_strips_null_parameters(self):
        note = self.make_handwritten_note()
        note["parameters"] = {
            key: None for key in PARAMETER_KEYS
        } | {
            "text": "Force",
            "x": 100,
            "y": 100,
        }
        response = json.dumps({
            "steps": [{
                "id": "step_1",
                "teaching_events": [{
                    "id": "event_1",
                    "visual_actions": [note],
                }],
            }]
        })
        provider = SequenceAIProvider([response])

        result = ActionGenerator(provider).generate_actions(self.plan)

        response_format = provider.calls[0]["response_format"]
        self.assertEqual(response_format["type"], "json_schema")
        self.assertTrue(response_format["json_schema"]["strict"])
        self.assertEqual(
            response_format["json_schema"]["schema"]["required"],
            ["steps"],
        )
        self.assertEqual(
            result["steps"][0]["visual_actions"][0]["parameters"],
            {"text": "Force", "x": 100, "y": 100},
        )
        self.assertEqual(
            set(response_format["json_schema"]["schema"]["properties"]["steps"]["items"]
                ["properties"]["teaching_events"]["items"]["properties"]["visual_actions"]
                ["items"]["properties"]["parameters"]["required"]),
            set(PARAMETER_KEYS),
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

    def test_retries_when_step_equation_action_is_missing_then_recovers(self):
        self.plan["steps"][0]["equations"] = ["F = ma"]

        def response(actions):
            return json.dumps({
                "steps": [{
                    "id": "step_1",
                    "teaching_events": [{
                        "id": "event_1",
                        "visual_actions": actions,
                    }],
                }]
            })

        missing_equation = response([
            self.make_handwritten_note(),
            self.make_circle(),
        ])
        complete = response([
            self.make_handwritten_note(),
            self.make_circle(),
            self.make_equation(),
        ])
        provider = SequenceAIProvider([missing_equation, complete])

        result = ActionGenerator(provider).generate_actions(self.plan)

        self.assertEqual(len(provider.calls), 2)
        self.assertIn("missing handwritten equation actions", provider.calls[1]["messages"][1]["content"])
        self.assertEqual(
            sum(action["type"] == "write_equation" for action in result["steps"][0]["visual_actions"]),
            1,
        )

    def test_retries_when_draw_shape_target_id_is_missing_then_recovers(self):
        missing_target = self.make_circle()
        missing_target.pop("target_id")

        def response(actions):
            return json.dumps({
                "steps": [{
                    "id": "step_1",
                    "teaching_events": [{
                        "id": "event_1",
                        "visual_actions": actions,
                    }],
                }]
            })

        invalid_response = response([
            self.make_handwritten_note(),
            missing_target,
        ])
        valid_response = response([
            self.make_handwritten_note(),
            self.make_circle(),
        ])
        provider = SequenceAIProvider([invalid_response, valid_response])

        result = ActionGenerator(provider).generate_actions(self.plan)

        self.assertEqual(len(provider.calls), 2)
        self.assertIn(
            "draw_shape requires a target_id",
            provider.calls[1]["messages"][1]["content"],
        )
        self.assertEqual(
            result["steps"][0]["visual_actions"][1]["target_id"],
            "step_1_circle",
        )

    def test_retries_draw_arrow_missing_target_id_twice_then_recovers(self):
        arrow = self.make_action(
            "action_arrow", "draw_arrow", 1,
            {"start_x": 300, "start_y": 200, "end_x": 500, "end_y": 200},
            target_id="step_1_force_arrow",
        )
        invalid_arrow = dict(arrow)
        invalid_arrow.pop("target_id")

        def response(arrow_action):
            return json.dumps({"steps": [{
                "id": "step_1",
                "teaching_events": [{
                    "id": "event_1",
                    "visual_actions": [self.make_handwritten_note(), arrow_action],
                }],
            }]})

        provider = SequenceAIProvider([
            response(invalid_arrow), response(invalid_arrow), response(arrow),
        ])
        result = ActionGenerator(provider).generate_actions(self.plan)

        self.assertEqual(len(provider.calls), 3)
        self.assertIn("draw_arrow requires a target_id", provider.calls[1]["messages"][1]["content"])
        self.assertIn("top-level target_id", provider.calls[2]["messages"][1]["content"])
        self.assertEqual(result["steps"][0]["visual_actions"][1]["target_id"], "step_1_force_arrow")

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

    def test_retries_reordered_steps_instead_of_relabeling_them(self):
        plan = self.make_two_step_plan()
        reordered = {
            "steps": [
                self.make_generated_step("step_2", "event_2", "action_2"),
                self.make_generated_step("step_1", "event_1", "action_1"),
            ]
        }
        valid = {
            "steps": [
                self.make_generated_step("step_1", "event_1", "action_1"),
                self.make_generated_step("step_2", "event_2", "action_2"),
            ]
        }
        provider = SequenceAIProvider([json.dumps(reordered), json.dumps(valid)])

        result = ActionGenerator(provider).generate_actions(plan)

        self.assertEqual(len(provider.calls), 2)
        self.assertEqual(
            [step["id"] for step in result["steps"]],
            ["step_1", "step_2"],
        )
        self.assertIn("expected 'step_1'", provider.calls[1]["messages"][1]["content"])

    def test_retries_reordered_events_instead_of_relabeling_them(self):
        plan = self.make_two_step_plan()
        plan["steps"][0]["teaching_events"].append(
            {"id": "event_1b", "explanation": "Second segment"}
        )
        reordered_step = self.make_generated_step("step_1", "event_1b", "action_1b")
        reordered_step["teaching_events"].append({
            "id": "event_1",
            "visual_actions": [
                self.make_action(
                    "action_1",
                    "write_text",
                    0,
                    {"text": "First segment", "x": 100, "y": 100},
                    target_id="step_1_note",
                )
            ],
        })
        valid_step = self.make_generated_step("step_1", "event_1", "action_1")
        valid_step["teaching_events"].append({
            "id": "event_1b",
            "visual_actions": [
                self.make_action(
                    "action_1b",
                    "write_text",
                    0,
                    {"text": "Second segment", "x": 100, "y": 200},
                    target_id="step_1_note_2",
                )
            ],
        })
        second_step = self.make_generated_step("step_2", "event_2", "action_2")
        provider = SequenceAIProvider([
            json.dumps({"steps": [reordered_step, second_step]}),
            json.dumps({"steps": [valid_step, second_step]}),
        ])

        result = ActionGenerator(provider).generate_actions(plan)

        self.assertEqual(len(provider.calls), 2)
        self.assertEqual(
            [event["id"] for event in result["steps"][0]["teaching_events"]],
            ["event_1", "event_1b"],
        )
        self.assertIn("expected 'event_1'", provider.calls[1]["messages"][1]["content"])

    def test_fails_after_retry_when_step_ids_remain_mismatched(self):
        plan = self.make_two_step_plan()
        mismatched = json.dumps({
            "steps": [
                self.make_generated_step("wrong_step", "event_1", "action_1"),
                self.make_generated_step("step_2", "event_2", "action_2"),
            ]
        })
        provider = SequenceAIProvider([mismatched, mismatched, mismatched])

        with self.assertRaisesRegex(
            ActionGenerationError,
            "failed after 3 attempts.*expected 'step_1'",
        ):
            ActionGenerator(provider).generate_actions(plan)

        self.assertEqual(len(provider.calls), 3)

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


    def make_two_step_plan(self):
        return {
            "title": "Two-step retry lesson",
            "steps": [
                {
                    "id": "step_1",
                    "explanation": "First explanation",
                    "equations": [],
                    "teaching_events": [
                        {"id": "event_1", "explanation": "First segment"}
                    ],
                },
                {
                    "id": "step_2",
                    "explanation": "Second explanation",
                    "equations": [],
                    "teaching_events": [
                        {"id": "event_2", "explanation": "Second segment"}
                    ],
                },
            ],
        }

    def make_generated_step(self, step_id, event_id, action_id):
        return {
            "id": step_id,
            "teaching_events": [
                {
                    "id": event_id,
                    "visual_actions": [
                        self.make_action(
                            action_id,
                            "write_text",
                            0,
                            {
                                "text": f"Teaching note for {step_id}",
                                "x": 100,
                                "y": 100,
                            },
                            target_id=f"{step_id}_note",
                        )
                    ],
                }
            ],
        }

    def test_retries_incomplete_action_generation_and_recovers(self):
        plan = self.make_two_step_plan()
        incomplete_response = {
            "steps": [
                self.make_generated_step("step_1", "event_1", "action_1")
            ]
        }
        complete_response = {
            "steps": [
                self.make_generated_step("step_1", "event_1", "action_1"),
                self.make_generated_step("step_2", "event_2", "action_2"),
            ]
        }
        provider = SequenceAIProvider([
            json.dumps(incomplete_response),
            json.dumps(complete_response),
        ])

        result = ActionGenerator(provider).generate_actions(plan)

        self.assertEqual(len(provider.calls), 2)
        self.assertEqual(len(result["steps"]), 2)
        self.assertIn(
            "Generated 1 teaching steps",
            provider.calls[1]["messages"][1]["content"],
        )

    def test_fails_after_retry_still_returns_wrong_step_count(self):
        plan = self.make_two_step_plan()
        incomplete_response = json.dumps({
            "steps": [
                self.make_generated_step("step_1", "event_1", "action_1")
            ]
        })
        provider = SequenceAIProvider([
            incomplete_response,
            incomplete_response,
            incomplete_response,
        ])

        with self.assertRaisesRegex(
            ActionGenerationError,
            "failed after 3 attempts",
        ):
            ActionGenerator(provider).generate_actions(plan)

        self.assertEqual(len(provider.calls), 3)

    def test_retries_groq_json_validation_failure_and_recovers(self):
        valid_response = json.dumps({
            "steps": [{
                "id": "step_1",
                "teaching_events": [{
                    "id": "event_1",
                    "visual_actions": [
                        self.make_handwritten_note(),
                        self.make_circle(),
                    ],
                }],
            }]
        })
        provider = SequenceAIProvider([
            RuntimeError(
                "Groq API request failed: Error code: 400 "
                "json_validate_failed: Failed to generate JSON"
            ),
            valid_response,
        ])

        result = ActionGenerator(provider).generate_actions(self.plan)

        self.assertEqual(len(provider.calls), 2)
        self.assertEqual(len(result["steps"]), 1)
        self.assertIn(
            "not valid JSON",
            provider.calls[1]["messages"][1]["content"],
        )

    def test_fails_after_retry_when_groq_json_validation_keeps_failing(self):
        provider_error = RuntimeError(
            "Groq API request failed: Error code: 400 "
            "json_validate_failed: Failed to generate JSON"
        )
        provider = SequenceAIProvider([provider_error, provider_error, provider_error])

        with self.assertRaisesRegex(
            ActionGenerationError,
            "failed after 3 attempts.*not valid JSON",
        ):
            ActionGenerator(provider).generate_actions(self.plan)

        self.assertEqual(len(provider.calls), 3)


    def test_does_not_retry_action_generation_provider_errors(self):
        provider = SequenceAIProvider([
            RuntimeError("Mock provider failure"),
            json.dumps({"steps": []}),
        ])

        with self.assertRaisesRegex(
            ActionGenerationError,
            "Mock provider failure",
        ):
            ActionGenerator(provider).generate_actions(self.plan)

        self.assertEqual(len(provider.calls), 1)


    def make_single_step_response_with_height(self, height):
        circle = self.make_circle("action_circle", 1)
        circle["parameters"]["height"] = height
        return json.dumps({
            "steps": [{
                "id": "step_1",
                "teaching_events": [{
                    "id": "event_1",
                    "visual_actions": [
                        self.make_handwritten_note(),
                        circle,
                    ],
                }],
            }]
        })

    def test_retries_invalid_action_dimensions_and_recovers(self):
        provider = SequenceAIProvider([
            self.make_single_step_response_with_height(0),
            self.make_single_step_response_with_height(20),
        ])

        result = ActionGenerator(provider).generate_actions(self.plan)

        self.assertEqual(len(provider.calls), 2)
        self.assertEqual(
            result["steps"][0]["visual_actions"][1]["parameters"]["height"],
            20,
        )
        self.assertIn(
            "height",
            provider.calls[1]["messages"][1]["content"],
        )

    def test_fails_after_retry_with_invalid_action_dimensions(self):
        invalid_response = self.make_single_step_response_with_height(0)
        provider = SequenceAIProvider([invalid_response, invalid_response, invalid_response])

        with self.assertRaisesRegex(
            ActionGenerationError,
            "failed after 3 attempts.*height",
        ):
            ActionGenerator(provider).generate_actions(self.plan)

        self.assertEqual(len(provider.calls), 3)



if __name__ == "__main__":
    unittest.main()
