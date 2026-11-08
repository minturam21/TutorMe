
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


# All drawing coordinates use a 2000 x 1400 canvas.

CanvasX = Annotated[float, Field(ge=0, le=2000)]
CanvasY = Annotated[float, Field(ge=0, le=1400)]


class ParameterBase(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CreateObjectParameters(ParameterBase):
    object_type: Literal[
        "rectangle", "circle", "ellipse",
        "line", "arrow", "polygon", "text"
    ]
    x: CanvasX
    y: CanvasY
    width: float = Field(gt=0, le=2000)
    height: float = Field(gt=0, le=1400)

    @model_validator(mode="after")
    def check_canvas_bounds(self):
        if self.x + self.width > 2000:
            raise ValueError("Object exceeds the canvas width.")
        if self.y + self.height > 1400:
            raise ValueError("Object exceeds the canvas height.")
        return self


class DrawShapeParameters(ParameterBase):
    shape: Literal["rectangle", "circle", "ellipse", "polygon"]
    x: CanvasX
    y: CanvasY
    width: float = Field(gt=0, le=2000)
    height: float = Field(gt=0, le=1400)
    label: str | None = None

    @model_validator(mode="after")
    def check_canvas_bounds(self):
        if self.x + self.width > 2000:
            raise ValueError("Shape exceeds the canvas width.")
        if self.y + self.height > 1400:
            raise ValueError("Shape exceeds the canvas height.")
        return self


class DrawLineParameters(ParameterBase):
    start_x: CanvasX
    start_y: CanvasY
    end_x: CanvasX
    end_y: CanvasY


class DrawArrowParameters(DrawLineParameters):
    pass


class DrawPathParameters(ParameterBase):
    points: list[tuple[CanvasX, CanvasY]] = Field(
        min_length=2,
        max_length=500,
    )
    closed: bool = False


class WriteTextParameters(ParameterBase):
    text: str = Field(min_length=1)
    x: CanvasX
    y: CanvasY


class WriteEquationParameters(ParameterBase):
    equation: str = Field(min_length=1)
    x: CanvasX
    y: CanvasY


class MoveObjectParameters(ParameterBase):
    x: CanvasX
    y: CanvasY


class RotateObjectParameters(ParameterBase):
    angle: float


class TransformObjectParameters(ParameterBase):
    scale_x: float = Field(gt=0, le=10)
    scale_y: float = Field(gt=0, le=10)


class HighlightObjectParameters(ParameterBase):
    color: str = "#FFFF00"


class EraseObjectParameters(ParameterBase):
    pass


class WaitParameters(ParameterBase):
    pass
