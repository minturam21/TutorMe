
from typing import Any

from pydantic import BaseModel, Field

from .visual_action import VisualAction


class SceneObject(BaseModel):
    id: str = Field(..., min_length=1)
    type: str
    properties: dict[str, Any] = Field(default_factory=dict)


class Scene(BaseModel):
    objects: list[SceneObject] = Field(default_factory=list)


class PracticeQuestion(BaseModel):
    question: str = Field(..., min_length=1)
    answer: str = Field(..., min_length=1)
    explanation: str = Field(..., min_length=1)


class TeachingEvent(BaseModel):
    """One synchronized explanation-and-whiteboard event."""

    id: str = Field(..., min_length=1)
    explanation: str = Field(..., min_length=1)
    visual_actions: list[VisualAction] = Field(default_factory=list)
    duration: float = Field(default=1.0, gt=0, le=300)


class TeachingStep(BaseModel):
    id: str = Field(..., min_length=1)
    explanation: str
    equations: list[str] = Field(default_factory=list)
    visual_actions: list[VisualAction] = Field(default_factory=list)
    teaching_events: list[TeachingEvent] = Field(default_factory=list)
    expected_scene: Scene = Field(default_factory=Scene)
    duration: float = Field(default=5.0, gt=0, le=300)


class Lesson(BaseModel):
    id: str = Field(..., min_length=1)
    title: str
    subject: str
    difficulty: str
    objectives: list[str] = Field(default_factory=list)
    initial_scene: Scene = Field(default_factory=Scene)
    steps: list[TeachingStep] = Field(..., min_length=1)
    practice_questions: list[PracticeQuestion] = Field(default_factory=list)
    version: int = Field(default=1, ge=1)
