import json

from services.ai_provider import AIProvider


class LessonPlanningError(Exception):
    """Raised when lesson planning fails."""


class LessonPlanner:
    """
    Converts a student's question into a structured teaching plan.
    """

    MAX_GENERATION_ATTEMPTS = 2

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
            ],
            "teaching_events": [
                {
                    "id": "event_1",
                    "explanation": "One short, ordered explanation segment.",
                    "visual_goal": "What should appear while this segment is explained.",
                    "visual_requirements": [
                        "The exact handwritten text, equation part, or visual change for this segment"
                    ]
                }
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

Each teaching step must contain 2 to 4 ordered teaching_events. Each event must explain one small idea only; do not put the entire step explanation into one event. Events must follow the exact teaching order. Associate each event with only the text, equation part, or visual change that belongs to that explanation segment. Do not reveal later concepts in earlier events. The event explanations, in order, must cover the full teaching step without duplicating it.
Return between 3 and 6 teaching steps. This limit is mandatory: never return fewer than 3 or more than 6 steps. For a narrow question, still teach it in at least 3 distinct stages: (1) introduce the required idea or prerequisite, (2) explain the central principle with its visual demonstration, and (3) apply it in a worked example or explain its consequence. Do not combine these stages into one step.
Return between 3 and 5 practice questions.
Use an empty array when equations are not relevant.
Do not include Markdown or text outside the JSON.
"""

        base_user_prompt = f"""
Student question: {question}

Requested subject: {subject or "Identify the appropriate subject"}

Requested difficulty: {difficulty}

Create a complete teaching plan for this question.
"""

        last_error = None

        for attempt in range(self.MAX_GENERATION_ATTEMPTS):
            user_prompt = base_user_prompt

            if last_error is not None:
                user_prompt += f"""

Your previous response was rejected by the application validator:
{last_error}

Regenerate the complete lesson plan. Correct the validation error.
The previous response contained an invalid number of teaching steps; this is not acceptable.
Return 3 to 5 distinct, sequential teaching steps as the preferred target. The validator allows between 3 and 6 steps, but never return more than 6 (at most 6). For a narrow topic, split the explanation into foundation, core principle, and worked application or consequence. Each step must have its own teaching goal and 2 to 4 teaching events. Do not put the entire lesson into one step.
Do not omit required teaching content or return a partial plan.
Return the complete corrected JSON only.
"""

            try:
                response_text = self.ai_provider.generate_response(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.3,
                    max_tokens=8000,
                    response_format={"type": "json_object"},
                )
                plan = json.loads(response_text)
                self._validate_plan(plan)
                return plan

            except json.JSONDecodeError as error:
                last_error = LessonPlanningError("AI returned invalid JSON.")

            except LessonPlanningError as error:
                last_error = error

            except Exception as error:
                # A provider may reject a malformed structured completion before returning
                # text when JSON mode is enabled. Retry only this output-format
                # failure; unrelated provider errors must fail immediately.
                provider_error = str(error)
                if (
                    "json_validate_failed" in provider_error
                    or "Failed to generate JSON" in provider_error
                ):
                    last_error = LessonPlanningError(
                        "The provider rejected the previous completion because it was "
                        "not valid JSON. Regenerate the complete lesson plan "
                        "as strict JSON matching the required structure."
                    )
                    continue
                raise LessonPlanningError(
                    f"Lesson planning failed: {error}"
                ) from error

        raise LessonPlanningError(
            f"Lesson planning failed after {self.MAX_GENERATION_ATTEMPTS} attempts: "
            f"{last_error}"
        ) from last_error

    @staticmethod
    def _validate_plan(plan: dict) -> None:
        """Validate the structure and content of a generated lesson plan."""

        if not isinstance(plan, dict):
            raise LessonPlanningError(
                "Plan must be a JSON object."
            )

        # Practice questions are supplementary to the visual lesson. Some model
        # responses omit them despite the prompt; the Lesson model already defaults
        # this field to an empty list, so normalize omission instead of aborting the
        # entire whiteboard generation.
        plan.setdefault("practice_questions", [])

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

        if not 3 <= len(steps) <= 6:
            raise LessonPlanningError(
                f"The lesson must contain between 3 and 6 steps; received {len(steps)}."
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

            events = step.get("teaching_events")
            if not isinstance(events, list) or not 2 <= len(events) <= 4:
                raise LessonPlanningError(
                    "Every teaching step must contain between 2 and 4 teaching events."
                )

            event_ids = set()
            for event in events:
                if not isinstance(event, dict):
                    raise LessonPlanningError("Every teaching event must be an object.")

                for field in ["id", "explanation", "visual_goal"]:
                    if not isinstance(event.get(field), str) or not event[field].strip():
                        raise LessonPlanningError(
                            f"Every teaching event needs a non-empty {field}."
                        )

                if event["id"] in event_ids:
                    raise LessonPlanningError(
                        f"Duplicate teaching event ID: {event['id']}"
                    )
                event_ids.add(event["id"])

                requirements = event.get("visual_requirements")
                if not isinstance(requirements, list) or not requirements:
                    raise LessonPlanningError(
                        "Every teaching event needs visual_requirements."
                    )
                if any(not isinstance(item, str) or not item.strip() for item in requirements):
                    raise LessonPlanningError(
                        "Every event visual requirement must be a non-empty string."
                    )

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

        if not 0 <= len(questions) <= 5:
            raise LessonPlanningError(
                "The lesson may contain at most 5 practice questions."
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
