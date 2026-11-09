
from copy import deepcopy
from uuid import uuid4

from pydantic import ValidationError

from models.lesson import Lesson, Scene
from services.lesson_validator import (
    validate_lesson,
    LessonValidationError,
)


class LessonCompilationError(Exception):
    """Raised when a lesson cannot be compiled."""


class LessonCompiler:
    """
    Combines a teaching plan and generated visual actions
    into a validated Lesson object.

    Simulates visual actions to generate a scene snapshot
    after every teaching step.
    """

    CREATION_TYPES = {
        "create_object",
        "draw_shape",
        "draw_line",
        "draw_arrow",
        "draw_path",
        "write_text",
        "write_equation",
    }

    OBJECT_TYPE_MAP = {
        "draw_line": "line",
        "draw_arrow": "arrow",
        "draw_path": "path",
        "write_text": "text",
        "write_equation": "equation",
    }

    def _load_initial_scene(self, initial_scene_data):
        """Validate and load the initial scene into compiler state."""

        try:
            initial_scene = Scene.model_validate(initial_scene_data)
        except ValidationError as error:
            raise LessonCompilationError(
                f"Invalid initial scene: {error}"
            ) from error

        scene_objects = {}

        for obj in initial_scene.objects:
            if obj.id in scene_objects:
                raise LessonCompilationError(
                    f"Duplicate initial object ID: '{obj.id}'."
                )

            scene_objects[obj.id] = obj.model_dump(mode="json")

        return scene_objects

    def _apply_action(self, scene_objects: dict, action: dict):
        action_type = action["type"]
        target_id = action.get("target_id")
        parameters = deepcopy(action.get("parameters", {}))

        if action_type == "wait":
            return

        if action_type in self.CREATION_TYPES:
            if not target_id:
                raise LessonCompilationError(
                    f"{action_type} requires a target_id."
                )

            if target_id in scene_objects:
                raise LessonCompilationError(
                    f"Object '{target_id}' already exists."
                )

            if action_type == "create_object":
                object_type = parameters.pop("object_type")
            elif action_type == "draw_shape":
                object_type = parameters.pop("shape")
            else:
                object_type = self.OBJECT_TYPE_MAP[action_type]

            scene_objects[target_id] = {
                "id": target_id,
                "type": object_type,
                "properties": parameters,
            }
            return

        if not target_id or target_id not in scene_objects:
            raise LessonCompilationError(
                f"{action_type} references missing object '{target_id}'."
            )

        properties = scene_objects[target_id]["properties"]

        if action_type == "move_object":
            properties["x"] = parameters["x"]
            properties["y"] = parameters["y"]

        elif action_type == "rotate_object":
            properties["angle"] = parameters["angle"]

        elif action_type == "transform_object":
            properties["scale_x"] = parameters["scale_x"]
            properties["scale_y"] = parameters["scale_y"]

        elif action_type == "highlight_object":
            properties["highlight_color"] = parameters["color"]

        elif action_type == "erase_object":
            del scene_objects[target_id]

        else:
            raise LessonCompilationError(
                f"Unsupported action type: {action_type}"
            )

    def compile(self, plan: dict) -> Lesson:
        if not isinstance(plan, dict):
            raise LessonCompilationError(
                "Lesson plan must be a dictionary."
            )

        try:
            steps = plan.get("steps")

            if not isinstance(steps, list) or not steps:
                raise LessonCompilationError(
                    "Lesson plan contains no teaching steps."
                )

            initial_scene_data = plan.get(
                "initial_scene",
                {"objects": []},
            )

            if not isinstance(initial_scene_data, dict):
                raise LessonCompilationError(
                    "Initial scene must be a dictionary."
                )

            scene_objects = self._load_initial_scene(
                initial_scene_data
            )

            compiled_steps = []

            for step in steps:
                if not isinstance(step, dict):
                    raise LessonCompilationError(
                        "Every teaching step must be a dictionary."
                    )

                teaching_events = step.get("teaching_events", [])
                compiled_events = []
                flattened_actions = []
                action_duration = 0.0

                if teaching_events:
                    if not isinstance(teaching_events, list):
                        raise LessonCompilationError(
                            f"Invalid teaching events in {step.get('id')}."
                        )

                    for event in teaching_events:
                        if not isinstance(event, dict) or not event.get("id"):
                            raise LessonCompilationError(
                                f"Every teaching event in {step.get('id')} needs an ID."
                            )

                        event_actions = event.get("visual_actions")
                        if not isinstance(event_actions, list) or not event_actions:
                            raise LessonCompilationError(
                                f"Event '{event.get('id')}' contains no visual actions."
                            )

                        event_duration = 0.0
                        for action in event_actions:
                            if not isinstance(action, dict):
                                raise LessonCompilationError(
                                    "Every event visual action must be a dictionary."
                                )
                            event_duration += action.get("duration", 0)
                            self._apply_action(scene_objects, action)
                            flattened_actions.append(deepcopy(action))

                        event_snapshot = {
                            "objects": deepcopy(list(scene_objects.values()))
                        }
                        event_duration = max(0.1, event_duration)
                        action_duration += event_duration

                        compiled_events.append({
                            "id": event["id"],
                            "explanation": event["explanation"],
                            "visual_actions": event_actions,
                            "expected_scene": event_snapshot,
                            "duration": event_duration,
                        })

                    for global_order, action in enumerate(flattened_actions):
                        action["order"] = global_order

                    actions = flattened_actions
                else:
                    actions = step.get("visual_actions")
                    if not isinstance(actions, list):
                        raise LessonCompilationError(
                            f"Invalid visual actions in {step.get('id')}."
                        )

                    for action in actions:
                        if not isinstance(action, dict):
                            raise LessonCompilationError(
                                "Every visual action must be a dictionary."
                            )
                        action_duration += action.get("duration", 0)
                        self._apply_action(scene_objects, action)

                step_duration = min(
                    300.0,
                    max(5.0, action_duration),
                )

                expected_scene = {
                    "objects": deepcopy(list(scene_objects.values()))
                }

                compiled_step = {
                    "id": step["id"],
                    "explanation": step["explanation"],
                    "equations": step.get("equations", []),
                    "visual_actions": actions,
                    "expected_scene": expected_scene,
                    "duration": step_duration,
                }
                if compiled_events:
                    compiled_step["teaching_events"] = compiled_events

                compiled_steps.append(compiled_step)

            lesson_data = {
                "id": str(uuid4()),
                "title": plan["title"],
                "subject": plan["subject"],
                "difficulty": plan["difficulty"],
                "objectives": plan["objectives"],
                "initial_scene": initial_scene_data,
                "steps": compiled_steps,
                "practice_questions": plan.get(
                    "practice_questions", []
                ),
                "version": 1,
            }

            lesson = validate_lesson(lesson_data)

            return lesson

        except LessonValidationError as error:
            raise LessonCompilationError(
                f"Lesson validation failed: {error}"
            ) from error

        except LessonCompilationError:
            raise

        except Exception as error:
            raise LessonCompilationError(
                f"Lesson compilation failed: {error}"
            ) from error
