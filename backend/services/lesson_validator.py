
from math import isfinite
from typing import Any

from pydantic import ValidationError

from models.lesson import Lesson


class LessonValidationError(Exception):
    """Raised when a generated lesson fails validation."""


SUPPORTED_OBJECT_TYPES = {
    "rectangle",
    "circle",
    "ellipse",
    "line",
    "arrow",
    "polygon",
    "text",
    "path",
    "equation",
}

CREATION_ACTIONS = {
    "create_object",
    "draw_shape",
    "draw_line",
    "draw_arrow",
    "draw_path",
    "write_text",
    "write_equation",
}

EXISTING_OBJECT_ACTIONS = {
    "move_object",
    "rotate_object",
    "transform_object",
    "highlight_object",
    "erase_object",
}

OBJECT_TYPE_MAP = {
    "draw_line": "line",
    "draw_arrow": "arrow",
    "draw_path": "path",
    "write_text": "text",
    "write_equation": "equation",
}

MAX_TOTAL_ACTIONS = 500
MAX_TOTAL_DURATION = 3600


def validate_parameters(value: Any, path: str = "parameters") -> None:
    """Reject unsupported values, NaN and infinity."""

    if isinstance(value, bool) or value is None or isinstance(value, str):
        return

    if isinstance(value, (int, float)):
        if not isfinite(value):
            raise LessonValidationError(
                f"Invalid numeric value at {path}."
            )
        return

    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            validate_parameters(item, f"{path}[{index}]")
        return

    if isinstance(value, dict):
        for key, item in value.items():
            validate_parameters(item, f"{path}.{key}")
        return

    raise LessonValidationError(
        f"Unsupported parameter value at {path}."
    )


def validate_scene(scene, scene_name: str) -> set:
    """Validate scene objects and return their IDs."""

    object_ids = set()

    for obj in scene.objects:
        if obj.id in object_ids:
            raise LessonValidationError(
                f"Duplicate object ID in {scene_name}: {obj.id}"
            )

        if obj.type not in SUPPORTED_OBJECT_TYPES:
            raise LessonValidationError(
                f"Unsupported object type in {scene_name}: {obj.type}"
            )

        object_ids.add(obj.id)

        validate_parameters(
            obj.properties,
            f"{scene_name}.{obj.id}.properties"
        )

    return object_ids


def scene_to_state(scene) -> dict:
    """Convert a Pydantic scene into a JSON-compatible state dictionary."""

    return {
        obj.id: obj.model_dump(mode="json")
        for obj in scene.objects
    }


def apply_action_to_state(scene_state: dict, action) -> None:
    """Apply one validated visual action to the simulated scene."""

    action_type = action.type
    target_id = action.target_id

    if action_type == "wait":
        return

    parameters = action.model_dump(mode="json")["parameters"]

    if action_type in CREATION_ACTIONS:

        if action_type == "create_object":
            object_type = parameters.pop("object_type")

        elif action_type == "draw_shape":
            object_type = parameters.pop("shape")

        else:
            object_type = OBJECT_TYPE_MAP[action_type]

        scene_state[target_id] = {
            "id": target_id,
            "type": object_type,
            "properties": parameters,
        }
        return

    if action_type == "move_object":
        scene_state[target_id]["properties"]["x"] = parameters["x"]
        scene_state[target_id]["properties"]["y"] = parameters["y"]

    elif action_type == "rotate_object":
        scene_state[target_id]["properties"]["angle"] = parameters["angle"]

    elif action_type == "transform_object":
        scene_state[target_id]["properties"]["scale_x"] = (
            parameters["scale_x"]
        )
        scene_state[target_id]["properties"]["scale_y"] = (
            parameters["scale_y"]
        )

    elif action_type == "highlight_object":
        scene_state[target_id]["properties"]["highlight_color"] = (
            parameters["color"]
        )

    elif action_type == "erase_object":
        del scene_state[target_id]


def validate_expected_scene(
    expected_scene,
    simulated_state: dict,
    step_id: str,
) -> None:
    """Check that the expected snapshot exactly matches simulated state."""

    validate_scene(
        expected_scene,
        f"expected_scene in step {step_id}"
    )

    expected_state = scene_to_state(expected_scene)

    if set(expected_state) != set(simulated_state):
        raise LessonValidationError(
            f"Expected scene in step {step_id} has different object IDs "
            "from the simulated scene."
        )

    for object_id, expected_object in expected_state.items():

        actual_object = simulated_state[object_id]

        if expected_object != actual_object:
            raise LessonValidationError(
                f"Expected scene in step {step_id} has incorrect "
                f"properties or type for object '{object_id}'."
            )


def validate_lesson(data: dict) -> Lesson:
    """Validate lesson structure, actions and complete scene consistency."""

    try:
        lesson = Lesson.model_validate(data)
    except ValidationError as error:
        raise LessonValidationError(
            f"Invalid lesson structure: {error}"
        ) from error

    if not lesson.title.strip():
        raise LessonValidationError("Lesson title cannot be empty.")

    if not lesson.subject.strip():
        raise LessonValidationError("Lesson subject cannot be empty.")

    validate_scene(
        lesson.initial_scene,
        "initial_scene"
    )

    # Start simulation from the initial scene.
    simulated_state = scene_to_state(lesson.initial_scene)

    total_actions = 0
    total_duration = 0.0
    action_ids = set()

    for step in lesson.steps:

        orders = [action.order for action in step.visual_actions]

        if len(orders) != len(set(orders)):
            raise LessonValidationError(
                f"Duplicate action order in step: {step.id}"
            )

        if orders != sorted(orders):
            raise LessonValidationError(
                f"Actions are not ordered correctly in step: {step.id}"
            )

        for action in step.visual_actions:

            if action.id in action_ids:
                raise LessonValidationError(
                    f"Duplicate action ID: {action.id}"
                )

            action_ids.add(action.id)

            total_actions += 1
            total_duration += action.duration

            if total_actions > MAX_TOTAL_ACTIONS:
                raise LessonValidationError(
                    "Lesson exceeds the maximum of 500 visual actions."
                )

            if total_duration > MAX_TOTAL_DURATION:
                raise LessonValidationError(
                    "Lesson exceeds the maximum total animation duration."
                )

            validate_parameters(
                action.parameters,
                f"action.{action.id}.parameters"
            )

            target_id = action.target_id

            if action.type == "wait":
                apply_action_to_state(simulated_state, action)
                continue

            if action.type in CREATION_ACTIONS:

                if not target_id:
                    raise LessonValidationError(
                        f"Creation action {action.id} requires a target_id."
                    )

                if target_id in simulated_state:
                    raise LessonValidationError(
                        f"Object ID already exists: {target_id}. "
                        "Erase the object before creating it again."
                    )

            elif action.type in EXISTING_OBJECT_ACTIONS:

                if not target_id:
                    raise LessonValidationError(
                        f"Action {action.id} requires a target_id."
                    )

                if target_id not in simulated_state:
                    raise LessonValidationError(
                        f"Action {action.id} references an object "
                        f"that does not exist: {target_id}"
                    )

            apply_action_to_state(simulated_state, action)

        validate_expected_scene(
            step.expected_scene,
            simulated_state,
            step.id,
        )

    return lesson
