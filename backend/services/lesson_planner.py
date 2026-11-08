
import json

from services.ai_provider import AIProvider


class LessonPlanningError(Exception):
    """Raised when lesson planning fails."""


class LessonPlanner:
    """
    Converts a student's question into a structured teaching plan.
    """

    def __init__(self, ai_provider: AIProvider | None = None):
        self.ai_provider = ai_provider or AIProvider()

    def create_plan(
        self,
        question: str,
        subject: str | None = None,
        difficulty: str = "beginner",
    ) -> dict:

        if not isinstance(question, str) or not question.strip():
            raise LessonPlanningError("Question cannot be empty.")

        system_prompt = """
You are an expert educational lesson planner.

Your task is to convert a student's question into a structured,
step-by-step teaching plan for an interactive visual whiteboard.

Teaching requirements:
1. Explain concepts in a logical sequence.
2. Start with prerequisites when necessary.
3. Break complicated topics into small teaching steps.
4. Give each step one clear teaching goal.
5. Include useful equations when relevant.
6. Describe what should be demonstrated visually.
7. Use subject-appropriate visual demonstrations.
8. Avoid unnecessary steps and repetitive explanations.
9. Adapt the difficulty to the student's requested level.
10. Do not generate drawing code or executable instructions.
11. Include 3 to 5 relevant practice questions.
12. Questions must test understanding, not just memorization.
13. Include answers and short explanations for practice questions.

Return valid JSON only, using this structure:

{
    "title": "Lesson title",
    "subject": "Subject name",
    "topic": "Specific topic",
    "difficulty": "beginner",
    "objectives": [
        "Learning objective"
    ],
    "steps": [
        {
            "id": "step_1",
            "teaching_goal": "What the student should understand",
            "explanation": "Clear teaching explanation",
            "key_concepts": [
                "Important concept"
            ],
            "equations": [
                "Relevant equation"
            ],
            "visual_goal": "What the whiteboard should demonstrate",
            "visual_requirements": [
                "Describe the required visual elements"
            ]
        }
    ],
    "practice_questions": [
        {
            "question": "Practice question",
            "answer": "Correct answer",
            "explanation": "Why this answer is correct"
        }
    ]
}

Return between 3 and 8 teaching steps.
Return between 3 and 5 practice questions.
Use an empty array when equations are not relevant.
Do not include Markdown or text outside the JSON.
"""

        user_prompt = f"""
Student question: {question}

Requested subject: {subject or "Identify the appropriate subject"}

Requested difficulty: {difficulty}

Create a complete teaching plan for this question.
"""

        try:
            response_text = self.ai_provider.generate_response(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
                max_tokens=6000,
                response_format={"type": "json_object"},
            )

            plan = json.loads(response_text)

        except json.JSONDecodeError as error:
            raise LessonPlanningError(
                "AI returned invalid JSON."
            ) from error

        except Exception as error:
            raise LessonPlanningError(
                f"Lesson planning failed: {error}"
            ) from error

        self._validate_plan(plan)

        return plan

    @staticmethod
    def _validate_plan(plan: dict) -> None:
        """Validate the structure and content of a generated lesson plan."""

        if not isinstance(plan, dict):
            raise LessonPlanningError(
                "Plan must be a JSON object."
            )

        required_fields = [
            "title",
            "subject",
            "topic",
            "difficulty",
            "objectives",
            "steps",
            "practice_questions",
        ]

        for field in required_fields:
            if field not in plan:
                raise LessonPlanningError(
                    f"Missing required plan field: {field}"
                )

        # Validate basic lesson information.
        for field in ["title", "subject", "topic", "difficulty"]:
            if not isinstance(plan[field], str) or not plan[field].strip():
                raise LessonPlanningError(
                    f"{field} must be a non-empty string."
                )

        # Validate learning objectives.
        objectives = plan["objectives"]

        if not isinstance(objectives, list) or not objectives:
            raise LessonPlanningError(
                "Objectives must be a non-empty list."
            )

        for objective in objectives:
            if not isinstance(objective, str) or not objective.strip():
                raise LessonPlanningError(
                    "Every learning objective must be a non-empty string."
                )

        # Validate teaching steps.
        steps = plan["steps"]

        if not isinstance(steps, list):
            raise LessonPlanningError(
                "Steps must be a list."
            )

        if not 3 <= len(steps) <= 8:
            raise LessonPlanningError(
                "The lesson must contain between 3 and 8 steps."
            )

        step_ids = set()

        step_text_fields = [
            "id",
            "teaching_goal",
            "explanation",
            "visual_goal",
        ]

        step_list_fields = [
            "key_concepts",
            "equations",
            "visual_requirements",
        ]

        for step in steps:

            if not isinstance(step, dict):
                raise LessonPlanningError(
                    "Every teaching step must be an object."
                )

            for field in step_text_fields:
                if field not in step:
                    raise LessonPlanningError(
                        f"Missing field '{field}' in a teaching step."
                    )

                if not isinstance(step[field], str) or not step[field].strip():
                    raise LessonPlanningError(
                        f"Step field '{field}' must be a non-empty string."
                    )

            if step["id"] in step_ids:
                raise LessonPlanningError(
                    f"Duplicate teaching step ID: {step['id']}"
                )

            step_ids.add(step["id"])

            for field in step_list_fields:

                if field not in step:
                    raise LessonPlanningError(
                        f"Missing field '{field}' in a teaching step."
                    )

                values = step[field]

                if not isinstance(values, list):
                    raise LessonPlanningError(
                        f"{field} must be a list."
                    )

                for value in values:
                    if not isinstance(value, str) or not value.strip():
                        raise LessonPlanningError(
                            f"Every item in {field} must be a non-empty string."
                        )

        # Validate practice questions.
        questions = plan["practice_questions"]

        if not isinstance(questions, list):
            raise LessonPlanningError(
                "Practice questions must be a list."
            )

        if not 3 <= len(questions) <= 5:
            raise LessonPlanningError(
                "The lesson must contain between 3 and 5 practice questions."
            )

        for item in questions:

            if not isinstance(item, dict):
                raise LessonPlanningError(
                    "Every practice question must be an object."
                )

            for field in ["question", "answer", "explanation"]:
                if not isinstance(item.get(field), str) or not item[field].strip():
                    raise LessonPlanningError(
                        f"Every practice question needs a valid {field}."
                    )
