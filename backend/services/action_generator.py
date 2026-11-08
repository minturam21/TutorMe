
import copy
import json

from pydantic import ValidationError

from models.visual_action import VisualAction
from services.ai_provider import AIProvider


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
1. Generate actions for every teaching step.
2. Preserve all original teaching step IDs.
3. Use only the 13 supported action types.
4. Every action must have a unique ID across the entire lesson.
5. Every newly created object needs a target_id.
6. Prefix new object IDs with their teaching step ID.
7. Never create an object whose target_id is currently active.
8. Create objects before modifying them.
9. Never modify or erase nonexistent objects.
10. An object ID may be reused after that object has been erased.
11. Prefer a fresh step-prefixed object ID when creating a new object.
12. Keep actions in logical execution order.
13. Use numeric coordinates and dimensions.
14. Use short, meaningful action sequences.
15. Avoid decorative objects.
16. Never generate actions for student practice answers.
17. Every teaching step must contain at least one actual visual action.
18. A wait action may accompany visual actions but cannot be the only action.
19. Every teaching step MUST contain at least one write_text action.
20. The write_text action must contain a concise, meaningful teaching note
    derived from that step's explanation or key concepts.
21. Never copy the entire explanation paragraph onto the whiteboard.
22. Use short handwritten notes, definitions, or concept statements.
23. If a teaching step contains equations, generate a write_equation
    action for every equation in that step.
24. Preserve the mathematical meaning of every original equation.
25. Position notes and equations deliberately so they do not overlap
    diagrams, other text, or other equations.
26. Do not use draw_shape labels as a replacement for write_text actions.

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
Uses the same parameters as draw_line.

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
Order: integer starting at 0 within each step.

Return valid JSON only.

Required output format:

{
    "steps": [
        {
            "id": "step_1",
            "visual_actions": [
                {
                    "id": "action_1",
                    "type": "draw_shape",
                    "target_id": "step_1_block",
                    "parameters": {
                        "shape": "rectangle",
                        "x": 100,
                        "y": 100,
                        "width": 120,
                        "height": 80
                    },
                    "duration": 1.0,
                    "easing": "ease_in_out",
                    "order": 0
                }
            ]
        }
    ]
}

Include every original teaching step.
Do not add explanations or Markdown outside JSON.
"""

        user_prompt = f"""
Convert this teaching plan into whiteboard actions.

TEACHING PLAN:

{json.dumps(plan, ensure_ascii=False, indent=2)}

Generate actions for all teaching steps.
Preserve every original step ID.
Use the 2000 x 1400 coordinate system.
Follow every action parameter specification.

IMPORTANT:
The steps array must contain JSON objects only.
Never return strings, numbers, or nested arrays as teaching steps.
Each object must contain:
- id
- visual_actions

The id must exactly match its corresponding original teaching step ID.
"""

        try:
            response_text = self.ai_provider.generate_response(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
                max_tokens=8000,
                response_format={"type": "json_object"},
            )

            result = json.loads(response_text)

        except json.JSONDecodeError as error:
            raise ActionGenerationError(
                "AI returned invalid JSON."
            ) from error

        except Exception as error:
            raise ActionGenerationError(
                f"Action generation failed: {error}"
            ) from error

        if not isinstance(result, dict):
            raise ActionGenerationError(
                "AI response must be a JSON object."
            )

        generated_steps = result.get("steps")

        if not isinstance(generated_steps, list):
            raise ActionGenerationError(
                "AI response must contain a steps list."
            )

        original_step_ids = [step["id"] for step in steps]

        if any(not isinstance(step, dict) for step in generated_steps):
            raise ActionGenerationError(
                "Generated teaching steps must be objects."
            )

        generated_step_ids = [
            step.get("id") for step in generated_steps
        ]

        if generated_step_ids != original_step_ids:
            raise ActionGenerationError(
                "Generated step IDs do not match the original plan."
            )

        updated_plan = copy.deepcopy(plan)
        all_action_ids = set()

        try:
            for original_step, generated_step in zip(
                updated_plan["steps"],
                generated_steps,
            ):
                actions = generated_step.get("visual_actions")

                if not isinstance(actions, list):
                    raise ActionGenerationError(
                        f"Invalid visual_actions in step: "
                        f"{original_step['id']}"
                    )

                if not actions:
                    raise ActionGenerationError(
                        f"Step '{original_step['id']}' contains no visual actions."
                    )

                validated_actions = []

                for action_data in actions:
                    action = VisualAction.model_validate(action_data)

                    if action.id in all_action_ids:
                        raise ActionGenerationError(
                            f"Duplicate action ID: {action.id}"
                        )

                    all_action_ids.add(action.id)

                    validated_actions.append(
                        action.model_dump()
                    )

                if not any(
                    action["type"] != "wait"
                    for action in validated_actions
                ):
                    raise ActionGenerationError(
                        f"Step '{original_step['id']}' contains no actual visual action."
                    )

                # Every teaching step needs handwritten teaching content.
                handwritten_notes = [
                    action
                    for action in validated_actions
                    if action["type"] == "write_text"
                ]

                if not handwritten_notes:
                    raise ActionGenerationError(
                        f"Step '{original_step['id']}' has no handwritten teaching note."
                    )

                if not any(
                    action["parameters"].get("text", "").strip()
                    for action in handwritten_notes
                ):
                    raise ActionGenerationError(
                        f"Step '{original_step['id']}' has an empty handwritten note."
                    )

                # Every original equation must have an equation-writing action.
                original_equations = original_step.get("equations", [])

                if not isinstance(original_equations, list):
                    raise ActionGenerationError(
                        f"Step '{original_step['id']}' has invalid equations."
                    )

                equation_actions = [
                    action
                    for action in validated_actions
                    if action["type"] == "write_equation"
                ]

                if len(equation_actions) < len(original_equations):
                    raise ActionGenerationError(
                        f"Step '{original_step['id']}' is missing handwritten equation actions."
                    )

                if any(
                    not action["parameters"].get("equation", "").strip()
                    for action in equation_actions
                ):
                    raise ActionGenerationError(
                        f"Step '{original_step['id']}' contains an empty handwritten equation."
                    )

                original_step["visual_actions"] = validated_actions

        except ValidationError as error:
            raise ActionGenerationError(
                f"AI generated an invalid visual action: {error}"
            ) from error

        return updated_plan
