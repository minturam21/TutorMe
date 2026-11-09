
import copy
import json

from pydantic import ValidationError

from models.visual_action import VisualAction
from services.ai_provider import AIProvider
from services.action_response_schema import ACTION_RESPONSE_FORMAT


class ActionGenerationError(Exception):
    """Raised when visual action generation fails."""


class ActionGenerator:
    """
    Converts a structured teaching plan into validated whiteboard actions.
    """

    def __init__(self, ai_provider: AIProvider | None = None):
        self.ai_provider = ai_provider or AIProvider()

    def generate_actions(self, plan: dict) -> dict:

        if not isinstance(plan, dict):
            raise ActionGenerationError("Plan must be a dictionary.")

        steps = plan.get("steps")

        if not isinstance(steps, list) or not steps:
            raise ActionGenerationError(
                "Plan must contain at least one teaching step."
            )

        for step in steps:
            if not isinstance(step, dict) or not step.get("id"):
                raise ActionGenerationError(
                    "Every teaching step must have an ID."
                )

        system_prompt = """
You are an expert educational whiteboard action generator.

Convert teaching plans into structured visual actions.

IMPORTANT:
You generate JSON instructions only.
Never generate executable code.

WHITEBOARD COORDINATE SYSTEM:
- Logical width: 2000
- Logical height: 1400
- x coordinates: 0 to 2000
- y coordinates: 0 to 1400
- Coordinates must be numeric.
- Never use coordinates outside these boundaries.

GENERAL RULES:
1. Generate concise actions separately for every teaching event.
2. Preserve all original teaching step and event IDs.
3. Use only the 13 supported action types.
4. Every action ID must be unique across the lesson.
5. EVERY creation action (create_object, draw_shape, draw_line, draw_arrow, draw_path, write_text, write_equation) MUST include its own non-empty top-level target_id.
6. Prefix new object IDs with their teaching step ID.
7. Never create an object whose target_id is currently active.
8. Create objects before modifying them.
9. Never modify or erase nonexistent objects.
10. An object ID may be reused after that object has been erased.
11. Prefer a fresh step-prefixed object ID when creating a new object.
12. Keep actions in logical execution order.
13. Use numeric coordinates and dimensions.
14. Use concise, meaningful action sequences.
15. Avoid decorative objects.
16. Never generate actions for student practice answers.
17. Generate a separate visual_actions list for EACH teaching event.
18. Each event's actions represent only its explained concept; never reveal later content early.
19. Never reveal content belonging to a later event early.
20. Every event must contain at least one non-wait visual action.
21. Every teaching step MUST contain at least one non-empty write_text action across its events; equations and diagram labels do not replace this handwritten teaching note.
22. Put a write_text action in the event introducing the corresponding term or definition. The note must be a short, relevant label, definition fragment, or key takeaway for that step.
23. Never copy an entire step explanation paragraph onto the board at once.
24. For every equation listed in a teaching step's equations array, generate a corresponding write_equation action. Do not omit any listed equation.
25. Put each equation action in the event that explains that equation. If a step has no listed equations, do not invent one.
26. Preserve the mathematical meaning of every original equation.
27. Position content deliberately to avoid overlap.
28. Do not use draw_shape labels as a replacement for write_text actions.

SUPPORTED ACTION TYPES AND PARAMETERS:

1. create_object
{
    "object_type": "rectangle",
    "x": 100,
    "y": 100,
    "width": 120,
    "height": 80
}

Supported object_type:
rectangle, circle, ellipse, line, arrow, polygon, text.

2. draw_shape
{
    "shape": "rectangle",
    "x": 100,
    "y": 100,
    "width": 120,
    "height": 80,
    "label": "Block"
}

Supported shapes:
rectangle, circle, ellipse, polygon.

For circles, width and height represent diameter.

3. draw_line
{
    "start_x": 100,
    "start_y": 100,
    "end_x": 300,
    "end_y": 100
}

4. draw_arrow
Uses the same parameters as draw_line. It MUST include a top-level target_id, e.g. "target_id": "step_1_force_arrow".

5. draw_path
{
    "points": [[100, 100], [200, 150], [300, 100]],
    "closed": false
}

6. write_text
{
    "text": "Force",
    "x": 100,
    "y": 100
}

7. write_equation
{
    "equation": "F = ma",
    "x": 100,
    "y": 100
}

8. move_object
{
    "x": 300,
    "y": 200
}

9. rotate_object
{
    "angle": 45
}

10. transform_object
{
    "scale_x": 1.5,
    "scale_y": 1.5
}

11. highlight_object
{
    "color": "#FFFF00"
}

12. erase_object
Parameters: {}

13. wait
Parameters: {}

TARGET ID RULES:

- Creation actions require a new target_id.
- Modification actions require an existing target_id.
- wait does not require a target_id.

ACTION METADATA:

Every action must contain:
- id
- type
- target_id when required
- parameters
- duration
- easing
- order

Duration: 0 to 60 seconds.
Easing: linear, ease_in, ease_out, ease_in_out.
Order: integer starting at 0 within each event.

Return valid JSON only.

Required output format:

{
    "steps": [
        {
            "id": "step_1",
            "teaching_events": [
                {
                    "id": "event_1",
                    "visual_actions": [
                        {
                            "id": "action_1",
                            "type": "write_text",
                            "target_id": "step_1_force_note",
                            "parameters": {"text": "Force", "x": 100, "y": 100},
                            "duration": 1.0,
                            "easing": "ease_in_out",
                            "order": 0
                        }
                    ]
                }
            ]
        }
    ]
}

Include every original teaching step.
Do not add explanations or Markdown outside JSON.
"""

        user_prompt = f"""
Convert this plan into concise whiteboard actions.

PLAN:

{json.dumps(plan, ensure_ascii=False, separators=(',', ':'))}

Generate actions for every event in every teaching step.
The original plan contains exactly {len(steps)} teaching steps. Return exactly {len(steps)} step objects: neither fewer nor more.
Preserve every original step ID and teaching event ID exactly as written in the plan.
Return all steps and events in the exact original order. Do not merge steps, omit steps, split steps, or stop early.
Use the 2000 x 1400 coordinate system.
Follow every action parameter specification.
All dimensions such as width, height, and scale factors must be strictly greater than zero. Never emit zero or negative dimensions.

IMPORTANT:
The steps array must contain JSON objects only.
Never return strings, numbers, or nested arrays as teaching steps.
Each object must contain:
- id
- teaching_events, each containing id and visual_actions

Before finishing, verify that the output step count equals {len(steps)} and that every original step ID appears exactly once.
"""

        # Allow two corrective retries for recoverable model-output defects.
        # Invalid actions are never accepted merely to make generation pass.
        max_attempts = 3
        last_error = None
        result = None
        generated_steps = None

        for attempt in range(max_attempts):
            retry_prompt = user_prompt
            if last_error is not None:
                retry_prompt += f"""

Your previous response was rejected:
{last_error}

Regenerate the COMPLETE visual-action JSON for the original plan.
Correct the reported problem precisely. Every step must contain at least one non-empty
write_text action across its events, even when the step contains equations or diagrams.
EVERY creation action (create_object, draw_shape, draw_line, draw_arrow, draw_path,
write_text, write_equation) must have its own non-empty top-level target_id. Never put target_id inside parameters.
For draw_arrow, use a unique step-prefixed ID such as step_1_force_arrow.
The plan contains exactly {len(steps)} teaching steps. Return exactly {len(steps)}
step objects, preserving every original step
ID and every teaching event ID in order. Do not omit, merge, split, or summarize
any step or event. Return JSON only.
"""
            try:
                response_text = self.ai_provider.generate_response(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": retry_prompt},
                    ],
                    temperature=0.2,
                    max_tokens=6000,
                    response_format=ACTION_RESPONSE_FORMAT,
                )
                result = json.loads(response_text)
            except json.JSONDecodeError as error:
                raise ActionGenerationError("AI returned invalid JSON.") from error
            except Exception as error:
                # A provider can reject a malformed structured completion before returning
                # text when JSON mode is enabled. Treat only this output-format
                # failure as recoverable; authentication, rate-limit, network,
                # and other provider errors must fail immediately.
                provider_error = str(error)
                if (
                    "json_validate_failed" in provider_error
                    or "Failed to generate JSON" in provider_error
                ):
                    last_error = (
                        "The provider rejected the previous completion because it was "
                        "not valid JSON. Regenerate the complete response as "
                        "strict JSON matching the required structure."
                    )
                    continue
                raise ActionGenerationError(
                    f"Action generation failed: {error}"
                ) from error

            if not isinstance(result, dict):
                raise ActionGenerationError("AI response must be a JSON object.")

            generated_steps = result.get("steps")
            if not isinstance(generated_steps, list):
                raise ActionGenerationError("AI response must contain a steps list.")

            if any(not isinstance(step, dict) for step in generated_steps):
                raise ActionGenerationError("Generated teaching steps must be objects.")

            if len(generated_steps) != len(steps):
                last_error = (
                    f"Generated {len(generated_steps)} teaching steps, "
                    f"but the original plan contains {len(steps)}."
                )
                continue

            # Step and event identity/order are part of the plan contract.
            # Never relabel generated content to make a mismatched response
            # appear valid: doing so can attach one concept's actions to another.
            identity_error = None
            for step_index, (original_step, generated_step) in enumerate(
                zip(steps, generated_steps)
            ):
                expected_step_id = original_step["id"]
                actual_step_id = generated_step.get("id")
                if actual_step_id != expected_step_id:
                    identity_error = (
                        f"Generated step at position {step_index} has ID "
                        f"'{actual_step_id}', expected '{expected_step_id}'."
                    )
                    break

                original_events = original_step.get("teaching_events")
                generated_events = generated_step.get("teaching_events")
                if not isinstance(original_events, list) or not isinstance(generated_events, list):
                    identity_error = (
                        f"Step '{expected_step_id}' must contain teaching_events lists."
                    )
                    break
                if len(generated_events) != len(original_events):
                    identity_error = (
                        f"Step '{expected_step_id}' generated {len(generated_events)} "
                        f"events, but the plan contains {len(original_events)}."
                    )
                    break

                for event_index, (original_event, generated_event) in enumerate(
                    zip(original_events, generated_events)
                ):
                    expected_event_id = original_event.get("id")
                    actual_event_id = (
                        generated_event.get("id")
                        if isinstance(generated_event, dict)
                        else None
                    )
                    if actual_event_id != expected_event_id:
                        identity_error = (
                            f"Step '{expected_step_id}' event at position {event_index} "
                            f"has ID '{actual_event_id}', expected '{expected_event_id}'."
                        )
                        break
                if identity_error:
                    break

            if identity_error:
                last_error = identity_error
                continue

            # Validate each action before accepting this generation attempt.
            # Invalid model output gets one corrective retry, just like an
            # incomplete step list, instead of failing the whole lesson later.
            invalid_action_error = None
            for step_data in generated_steps:
                events = step_data.get("teaching_events")
                if not isinstance(events, list):
                    continue
                for event_data in events:
                    if not isinstance(event_data, dict):
                        continue
                    actions = event_data.get("visual_actions")
                    if not isinstance(actions, list):
                        continue
                    for action_data in actions:
                        if not isinstance(action_data, dict):
                            continue
                        candidate = {**action_data, "order": 0}
                        # Strict JSON Schema requires every parameter key; null
                        # placeholders are transport-only and must not reach
                        # the action-specific Pydantic models (extra=forbid).
                        if isinstance(candidate.get("parameters"), dict):
                            candidate["parameters"] = {
                                key: value
                                for key, value in candidate["parameters"].items()
                                if value is not None
                            }
                        try:
                            VisualAction.model_validate(candidate)
                        except ValidationError as error:
                            action_id = action_data.get("id", "<missing>")
                            action_type = action_data.get("type", "<missing>")
                            details = "; ".join(
                                f"{'.'.join(str(part) for part in item['loc'])}: {item['msg']}"
                                for item in error.errors()
                            )
                            invalid_action_error = (
                                f"Action '{action_id}' (type '{action_type}') "
                                f"has invalid parameters: {details}"
                            )
                            break
                    if invalid_action_error:
                        break
                if invalid_action_error:
                    break

            if invalid_action_error is None:
                # Check required handwritten content before accepting a response.
                # These semantic failures must trigger the corrective retry too.
                for original_step, generated_step in zip(steps, generated_steps):
                    expected_equations = original_step.get("equations", [])
                    generated_events = generated_step.get("teaching_events", [])
                    equation_count = 0
                    for event_data in generated_events:
                        if not isinstance(event_data, dict):
                            continue
                        actions = event_data.get("visual_actions", [])
                        if not isinstance(actions, list):
                            continue
                        equation_count += sum(
                            1 for action in actions
                            if isinstance(action, dict)
                            and action.get("type") == "write_equation"
                            and isinstance(action.get("parameters"), dict)
                            and isinstance(action["parameters"].get("equation"), str)
                            and action["parameters"]["equation"].strip()
                        )
                    if not isinstance(expected_equations, list):
                        invalid_action_error = (
                            f"Step '{original_step['id']}' has invalid equations."
                        )
                        break
                    if equation_count < len(expected_equations):
                        invalid_action_error = (
                            f"Step '{original_step['id']}' is missing handwritten "
                            f"equation actions: expected at least {len(expected_equations)}, "
                            f"received {equation_count}."
                        )
                        break

                    has_handwritten_note = any(
                        isinstance(action, dict)
                        and action.get("type") == "write_text"
                        and isinstance(action.get("parameters"), dict)
                        and isinstance(action["parameters"].get("text"), str)
                        and action["parameters"]["text"].strip()
                        for event_data in generated_events
                        if isinstance(event_data, dict)
                        for action in event_data.get("visual_actions", [])
                        if isinstance(event_data.get("visual_actions", []), list)
                    )
                    if not has_handwritten_note:
                        invalid_action_error = (
                            f"Step '{original_step['id']}' has no handwritten teaching note. "
                            "Add at least one non-empty write_text action to one of its events."
                        )
                        break

            if invalid_action_error:
                last_error = invalid_action_error
                continue

            break
        else:
            raise ActionGenerationError(
                f"Action generation failed after {max_attempts} attempts: {last_error}"
            )

        # Identity and order were checked before accepting the response.

        updated_plan = copy.deepcopy(plan)
        all_action_ids = set()

        try:
            for original_step, generated_step in zip(updated_plan["steps"], generated_steps):
                original_events = original_step.get("teaching_events")
                generated_events = generated_step.get("teaching_events")
                if not isinstance(original_events, list) or not original_events:
                    raise ActionGenerationError(f"Step '{original_step['id']}' has no teaching events.")
                if not isinstance(generated_events, list):
                    raise ActionGenerationError(f"Invalid teaching_events in step '{original_step['id']}'.")

                expected_ids = [event["id"] for event in original_events]
                actual_ids = [event.get("id") if isinstance(event, dict) else None for event in generated_events]
                if actual_ids != expected_ids:
                    raise ActionGenerationError(f"Generated event IDs do not match the plan in step '{original_step['id']}'.")

                flattened_actions = []
                has_handwritten_note = False
                equation_actions = []

                for original_event, generated_event in zip(original_events, generated_events):
                    actions = generated_event.get("visual_actions")
                    if not isinstance(actions, list) or not actions:
                        raise ActionGenerationError(f"Event '{original_event['id']}' contains no visual actions.")

                    validated_actions = []
                    for action_index, action_data in enumerate(actions):
                        if not isinstance(action_data, dict):
                            raise ActionGenerationError(
                                f"Invalid action in event '{original_event['id']}'."
                            )

                        # The action's position in the event is authoritative.
                        # Do not rely on the AI to provide a required sequence field.
                        action_data = {**action_data, "order": action_index}
                        if isinstance(action_data.get("parameters"), dict):
                            action_data["parameters"] = {
                                key: value
                                for key, value in action_data["parameters"].items()
                                if value is not None
                            }
                        action = VisualAction.model_validate(action_data)
                        if action.id in all_action_ids:
                            raise ActionGenerationError(f"Duplicate action ID: {action.id}")
                        all_action_ids.add(action.id)
                        validated_actions.append(action.model_dump())

                    if not any(action["type"] != "wait" for action in validated_actions):
                        raise ActionGenerationError(f"Event '{original_event['id']}' contains no actual visual action.")

                    if any(action["type"] == "write_text" and action["parameters"].get("text", "").strip() for action in validated_actions):
                        has_handwritten_note = True

                    equation_actions.extend(action for action in validated_actions if action["type"] == "write_equation")
                    original_event["visual_actions"] = validated_actions
                    flattened_actions.extend(copy.deepcopy(validated_actions))

                if not has_handwritten_note:
                    raise ActionGenerationError(f"Step '{original_step['id']}' has no handwritten teaching note.")

                original_equations = original_step.get("equations", [])
                if not isinstance(original_equations, list):
                    raise ActionGenerationError(f"Step '{original_step['id']}' has invalid equations.")
                if len(equation_actions) < len(original_equations):
                    raise ActionGenerationError(f"Step '{original_step['id']}' is missing handwritten equation actions.")
                if any(not action["parameters"].get("equation", "").strip() for action in equation_actions):
                    raise ActionGenerationError(f"Step '{original_step['id']}' contains an empty handwritten equation.")

                # The legacy step-level list has one shared order namespace.
                # Preserve event-local order values in teaching_events.
                for global_order, action in enumerate(flattened_actions):
                    action["order"] = global_order

                original_step["visual_actions"] = flattened_actions

        except ValidationError as error:
            raise ActionGenerationError(f"AI generated an invalid visual action: {error}") from error

        return updated_plan
