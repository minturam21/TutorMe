
import logging
import sqlite3

from fastapi import APIRouter, HTTPException, Query, Response, status

import database

from models.schemas import (
    LessonGenerationRequest,
    LessonGenerationResponse,
    LessonSummary,
    SavedLessonResponse,
)

from services.lesson_planner import (
    LessonPlanner,
    LessonPlanningError,
)

from services.action_generator import (
    ActionGenerator,
    ActionGenerationError,
)

from services.lesson_compiler import (
    LessonCompiler,
    LessonCompilationError,
)


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/lessons",
    tags=["Lessons"],
)


# -------------------------
# GENERATE AND SAVE LESSON
# -------------------------

@router.post(
    "/generate",
    response_model=LessonGenerationResponse,
    status_code=status.HTTP_201_CREATED,
)
def generate_lesson(request: LessonGenerationRequest):

    try:
        # Step 1: Generate teaching plan
        planner = LessonPlanner()

        plan = planner.create_plan(
            question=request.question,
            subject=request.subject,
            difficulty=request.difficulty,
        )

        # Step 2: Generate visual actions
        action_generator = ActionGenerator()

        plan_with_actions = action_generator.generate_actions(
            plan
        )

        # Step 3: Compile and validate lesson
        compiler = LessonCompiler()

        lesson = compiler.compile(plan_with_actions)

        # Step 4: Save validated lesson
        database.save_lesson(
            lesson,
            conversation_id=request.conversation_id,
        )

        # Step 5: Return completed lesson
        return LessonGenerationResponse(
            success=True,
            lesson=lesson,
            message="Lesson generated and saved successfully.",
        )

    except (
        LessonPlanningError,
        ActionGenerationError,
    ) as error:

        raise HTTPException(
            status_code=502,
            detail=f"AI generation failed: {error}",
        ) from error

    except LessonCompilationError as error:

        raise HTTPException(
            status_code=422,
            detail=f"Lesson validation failed: {error}",
        ) from error

    except sqlite3.IntegrityError as error:

        logger.warning(
            "Lesson could not be saved because of a database constraint."
        )

        raise HTTPException(
            status_code=404,
            detail="The specified conversation does not exist.",
        ) from error

    except Exception as error:

        logger.exception("Unexpected lesson generation error.")

        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while generating the lesson.",
        ) from error


# -------------------------
# LIST SAVED LESSONS
# -------------------------

@router.get(
    "",
    response_model=list[LessonSummary],
)
def list_lessons(
    conversation_id: int | None = Query(default=None, ge=1),
):

    try:
        return database.get_lessons(
            conversation_id=conversation_id
        )

    except Exception as error:

        logger.exception("Could not retrieve saved lessons.")

        raise HTTPException(
            status_code=500,
            detail="Could not retrieve saved lessons.",
        ) from error


# -------------------------
# GET SINGLE LESSON
# -------------------------

@router.get(
    "/{lesson_id}",
    response_model=SavedLessonResponse,
)
def retrieve_lesson(lesson_id: str):

    try:
        lesson = database.get_lesson(lesson_id)

        if lesson is None:
            raise HTTPException(
                status_code=404,
                detail="Lesson not found.",
            )

        return lesson

    except HTTPException:
        raise

    except Exception as error:

        logger.exception("Could not retrieve lesson %s.", lesson_id)

        raise HTTPException(
            status_code=500,
            detail="Could not retrieve the requested lesson.",
        ) from error


# -------------------------
# DELETE SAVED LESSON
# -------------------------

@router.delete(
    "/{lesson_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_lesson(lesson_id: str):

    try:
        deleted = database.delete_lesson(lesson_id)

        if deleted == 0:
            raise HTTPException(
                status_code=404,
                detail="Lesson not found.",
            )

        return Response(status_code=status.HTTP_204_NO_CONTENT)

    except HTTPException:
        raise

    except Exception as error:

        logger.exception("Could not delete lesson %s.", lesson_id)

        raise HTTPException(
            status_code=500,
            detail="Could not delete the requested lesson.",
        ) from error
