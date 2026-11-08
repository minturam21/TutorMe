
from services.lesson_planner import LessonPlanner
from services.action_generator import ActionGenerator
from services.lesson_compiler import LessonCompiler


def main():
    question = "Explain Newton's three laws of motion with examples."

    print("\n1. Generating teaching plan using real Groq API...")

    planner = LessonPlanner()
    plan = planner.create_plan(
        question=question,
        subject="Physics",
        difficulty="beginner",
    )

    print("Teaching plan generated successfully.")
    print("Title:", plan["title"])
    print("Steps:", len(plan["steps"]))

    print("\n2. Generating visual actions using real Groq API...")

    action_generator = ActionGenerator()
    plan_with_actions = action_generator.generate_actions(plan)

    total_actions = sum(
        len(step["visual_actions"])
        for step in plan_with_actions["steps"]
    )

    print("Visual actions generated successfully.")
    print("Total visual actions:", total_actions)

    print("\n3. Compiling and validating lesson...")

    compiler = LessonCompiler()
    lesson = compiler.compile(plan_with_actions)

    print("Lesson compiled and validated successfully.")

    print("\n========== FINAL RESULT ==========")
    print("Lesson ID:", lesson.id)
    print("Title:", lesson.title)
    print("Subject:", lesson.subject)
    print("Teaching steps:", len(lesson.steps))
    print("Practice questions:", len(lesson.practice_questions))
    print(
        "Visual actions:",
        sum(len(step.visual_actions) for step in lesson.steps),
    )

    print("\nAction summary:")

    for index, step in enumerate(lesson.steps, start=1):
        action_types = [
            action.type for action in step.visual_actions
        ]

        print(f"Step {index}: {action_types}")

    print("\nREAL GROQ INTEGRATION TEST PASSED.")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("\nREAL GROQ INTEGRATION TEST FAILED.")
        print("Error:", error)
