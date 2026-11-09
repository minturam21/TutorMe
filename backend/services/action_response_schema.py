"""Groq strict JSON Schema for whiteboard action responses.

This transport schema constrains JSON shape. VisualAction/Pydantic remains
responsible for validating action-specific parameter semantics.
"""

ACTION_TYPES = [
    "create_object", "draw_shape", "draw_line", "draw_arrow", "draw_path",
    "write_text", "write_equation", "move_object", "rotate_object",
    "transform_object", "highlight_object", "erase_object", "wait",
]

PARAMETER_PROPERTIES = {
    "object_type": {"type": ["string", "null"]},
    "shape": {"type": ["string", "null"]},
    "x": {"type": ["number", "null"]},
    "y": {"type": ["number", "null"]},
    "width": {"type": ["number", "null"]},
    "height": {"type": ["number", "null"]},
    "label": {"type": ["string", "null"]},
    "start_x": {"type": ["number", "null"]},
    "start_y": {"type": ["number", "null"]},
    "end_x": {"type": ["number", "null"]},
    "end_y": {"type": ["number", "null"]},
    "points": {
        "type": ["array", "null"],
        "items": {
            "type": "array",
            "items": {"type": "number"},
        },
    },
    "closed": {"type": ["boolean", "null"]},
    "text": {"type": ["string", "null"]},
    "equation": {"type": ["string", "null"]},
    "angle": {"type": ["number", "null"]},
    "scale_x": {"type": ["number", "null"]},
    "scale_y": {"type": ["number", "null"]},
    "color": {"type": ["string", "null"]},
}

PARAMETER_KEYS = list(PARAMETER_PROPERTIES)

ACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "type": {"type": "string", "enum": ACTION_TYPES},
        "target_id": {"type": ["string", "null"]},
        "parameters": {
            "type": "object",
            "properties": PARAMETER_PROPERTIES,
            "required": PARAMETER_KEYS,
            "additionalProperties": False,
        },
        "duration": {"type": "number"},
        "easing": {
            "type": "string",
            "enum": ["linear", "ease_in", "ease_out", "ease_in_out"],
        },
        "order": {"type": "integer"},
    },
    "required": [
        "id", "type", "target_id", "parameters", "duration", "easing", "order"
    ],
    "additionalProperties": False,
}

EVENT_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "visual_actions": {"type": "array", "items": ACTION_SCHEMA},
    },
    "required": ["id", "visual_actions"],
    "additionalProperties": False,
}

STEP_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "teaching_events": {"type": "array", "items": EVENT_SCHEMA},
    },
    "required": ["id", "teaching_events"],
    "additionalProperties": False,
}

ACTION_RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "tutorme_whiteboard_actions",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "steps": {"type": "array", "items": STEP_SCHEMA},
            },
            "required": ["steps"],
            "additionalProperties": False,
        },
    },
}
