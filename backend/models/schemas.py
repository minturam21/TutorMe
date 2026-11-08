
from pydantic import BaseModel, Field

from .lesson import Lesson


class LessonGenerationRequest(BaseModel):
    """Request sent by the frontend to generate a new lesson."""

    question: str = Field(..., min_length=1, max_length=5000)
    subject: str | None = None
    difficulty: str = "beginner"
    conversation_id: int | None = None


class LessonGenerationResponse(BaseModel):
    """Response returned after lesson generation."""

    success: bool
    lesson: Lesson
    message: str = "Lesson generated successfully."


class LessonSummary(BaseModel):
    """Metadata for a saved lesson."""

    id: str
    conversation_id: int | None = None
    title: str
    subject: str
    difficulty: str
    version: int
    created_at: str
    updated_at: str


class SavedLessonResponse(BaseModel):
    """Complete saved lesson with database metadata."""

    id: str
    conversation_id: int | None = None
    title: str
    subject: str
    difficulty: str
    version: int
    created_at: str
    updated_at: str
    lesson: Lesson
