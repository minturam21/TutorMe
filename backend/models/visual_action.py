
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from .visual_parameters import (
    CreateObjectParameters,
    DrawShapeParameters,
    DrawLineParameters,
    DrawArrowParameters,
    DrawPathParameters,
    WriteTextParameters,
    WriteEquationParameters,
    MoveObjectParameters,
    RotateObjectParameters,
    TransformObjectParameters,
    HighlightObjectParameters,
    EraseObjectParameters,
    WaitParameters,
)


PARAMETER_MODELS = {
    "create_object": CreateObjectParameters,
    "draw_shape": DrawShapeParameters,
    "draw_line": DrawLineParameters,
    "draw_arrow": DrawArrowParameters,
    "draw_path": DrawPathParameters,
    "write_text": WriteTextParameters,
    "write_equation": WriteEquationParameters,
    "move_object": MoveObjectParameters,
    "rotate_object": RotateObjectParameters,
    "transform_object": TransformObjectParameters,
    "highlight_object": HighlightObjectParameters,
    "erase_object": EraseObjectParameters,
    "wait": WaitParameters,
}


class VisualAction(BaseModel):
    """
    A single validated instruction for the frontend whiteboard engine.
    """

    id: str = Field(..., min_length=1)

    type: Literal[
        "create_object",
        "draw_shape",
        "draw_line",
        "draw_arrow",
        "draw_path",
        "write_text",
        "write_equation",
        "move_object",
        "rotate_object",
        "transform_object",
        "highlight_object",
        "erase_object",
        "wait",
    ]

    target_id: str | None = None

    parameters: dict[str, Any] = Field(default_factory=dict)

    duration: float = Field(default=0.5, ge=0, le=60)

    easing: Literal[
        "linear",
        "ease_in",
        "ease_out",
        "ease_in_out",
    ] = "ease_in_out"

    order: int = Field(..., ge=0)

    @model_validator(mode="after")
    def validate_parameters(self):
        parameter_model = PARAMETER_MODELS[self.type]

        validated_parameters = parameter_model.model_validate(
            self.parameters
        )

        self.parameters = validated_parameters.model_dump(
            exclude_none=True
        )

        return self
