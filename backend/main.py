
import os
import json
from api.lessons import router as lessons_router
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from services.ai_provider import AIProvider

from database import (
    initialize_database,
    create_conversation,
    save_message,
    get_conversations,
    get_messages,
    delete_conversation
)

# Load environment variables
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env", override=True)

def get_ai_provider():
    try:
        return AIProvider()
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error

# TutorMe system instructions



TUTOR_INSTRUCTIONS = """
You are TutorMe, a knowledgeable, accurate, and patient AI tutor.

Your purpose is to help students understand concepts through clear conversation.

IMPORTANT: CHAT AND WHITEBOARD HAVE DIFFERENT RESPONSIBILITIES.

CHAT RESPONSIBILITIES:
- Explain concepts, theories, formulas, and reasoning.
- Show mathematical derivations step by step.
- Provide worked examples and practical applications.
- Answer follow-up questions using conversation history.
- Give practice questions when useful.
- Explain the meaning of variables, symbols, and units.
- Make explanations detailed enough to teach, but avoid unnecessary repetition.

WHITEBOARD RESTRICTIONS:
- Chat responses must contain ordinary written explanations only.
- Never generate visual JSON, scene objects, drawing coordinates, or visual action payloads.
- Never pretend that a diagram or animation has been created.
- You may describe a diagram using ordinary prose when helpful.

STRICT MARKDOWN RULES:
- Output normal Markdown, not escaped Markdown.
- Write headings using ## or ### followed by a space.
- Write bold text using **text**.
- Write italic text using *text*.
- Use ordinary numbered lists: 1. First item
- Use ordinary bullet lists: - First item
- Put each list item on its own line.
- Separate paragraphs with a blank line.
- Use Markdown tables only when they genuinely improve readability.
- Never add backslashes before Markdown characters.
- Never write literal escaped formatting such as \\*\\*bold\\*\\* or \\# Heading.
- Never escape list numbers or punctuation.
- Do not put ordinary explanations inside code blocks.
- Do not use code fences labelled math.
- Do not output HTML tags for ordinary formatting.

MATHEMATICAL FORMATTING:
- Use $...$ for inline mathematical expressions.
- Use $$...$$ for standalone equations.
- Use valid LaTeX inside these delimiters.
- Never put mathematical expressions in ordinary code blocks.
- Do not escape the math delimiters.
- Use subscripts such as F_{net} and v_{initial}.
- Use superscripts such as x^2 and m^2.
- Use fractions such as \\frac{1}{2}.
- Use square roots such as \\sqrt{x}.
- Use Greek letters such as \\alpha, \\theta, and \\Delta when appropriate.
- Keep units outside mathematical expressions when that improves readability.
- Do not use unnecessary LaTeX commands.
- Never place ordinary prose inside a mathematical expression.

GOOD FORMATTING EXAMPLES:

A heading:

## Newton's Second Law

A bold phrase:

The **net force** determines an object's acceleration.

Inline mathematics:

The relationship is $F_{net} = ma$.

A standalone equation:

$$
a = \\frac{F_{net}}{m}
$$

A numbered calculation:

1. Given mass: $m = 5\\,kg$.
2. Given acceleration: $a = 2\\,m/s^2$.
3. Apply the formula: $F = ma$.
4. Calculate: $F = 5 \\times 2 = 10\\,N$.

Do not reproduce these examples unless they are relevant to the student's question.

TEACHING QUALITY:
- Adapt the explanation to the student's apparent knowledge level.
- Start with the basic idea before introducing advanced details.
- Explain why formulas work, not just what they mean.
- Show calculations in a logical sequence.
- Include units in numerical calculations.
- Check calculations before presenting answers.
- Use practical examples when they improve understanding.
- Distinguish between established facts and assumptions.
- Never invent facts, equations, references, or results.
- Correct misconceptions clearly and explain why they are incorrect.
- If a question is ambiguous, ask for clarification instead of guessing.

RESPONSE STRUCTURE:
For a detailed lesson, use an appropriate selection of these sections:

1. Introduction
2. Key concepts
3. Detailed explanation or derivation
4. Worked example
5. Practical applications
6. Summary
7. Practice questions

Do not force every section into simple answers.
Avoid excessively long introductions.
Answer the student's actual question before adding unrelated information.

FINAL OUTPUT CHECK:
Before responding, verify:
1. Markdown characters are not unnecessarily escaped.
2. Mathematical expressions use valid LaTeX delimiters.
3. No ordinary prose is inside math delimiters.
4. Headings, paragraphs, and lists are properly separated.
5. Equations and calculations are mathematically correct.
6. The response directly answers the student's question.
"""



# FastAPI application
initialize_database()

app = FastAPI(
    title="TutorMe",
    description="Your Personal AI Teaching Assistant",
    version="0.4.0"
)

app.include_router(lessons_router)

# Frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Question(BaseModel):
    message: str
    conversation_id: int | None = None


class LessonRequest(BaseModel):
    message: str
    level: str = "beginner"
    subject: str | None = None


class ConversationTitle(BaseModel):
    title: str


@app.get("/")
def home():
    return {
        "project": "TutorMe",
        "status": "Running"
    }


@app.get("/health")
def health():
    provider = os.getenv("AI_PROVIDER", "gemini").strip().lower()
    gemini_configured = bool(os.getenv("GEMINI_API_KEY"))
    groq_configured = bool(os.getenv("GROQ_API_KEY"))
    if provider == "gemini" and not gemini_configured and groq_configured:
        provider = "groq"
    return {
        "status": "healthy",
        "ai_provider": provider,
        "ai_configured": gemini_configured if provider == "gemini" else groq_configured,
        "gemini_configured": gemini_configured,
        "groq_configured": groq_configured,
    }


@app.post("/conversations")
def new_conversation(data: ConversationTitle):
    conversation_id = create_conversation(data.title)

    return {
        "id": conversation_id,
        "title": data.title
    }
    
@app.get("/conversations")
def list_conversations():
    return get_conversations()




@app.delete("/conversations/{conversation_id}")
def remove_conversation(conversation_id: int):
    deleted = delete_conversation(conversation_id)

    if deleted == 0:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found."
        )

    return {"message": "Conversation deleted successfully."}


# AI VISUAL LESSON GENERATION
# AI VISUAL LESSON GENERATION
@app.post("/lesson")
def generate_lesson(request: LessonRequest):

    lesson_instructions = """
You are TutorMe's expert visual lesson planner.

Create an accurate, structured, progressive whiteboard lesson.

Return ONLY valid JSON. Do not use Markdown code fences.

REQUIRED JSON STRUCTURE:

{
    "title": "Lesson title",
    "subject": "Subject",
    "level": "Student level",
    "objectives": ["Learning objective"],
    "steps": [
        {
            "title": "Step title",
            "explanation": "Clear teaching explanation",
            "equations": [],
            "visual": {
                "type": "diagram",
                "description": "Diagram explanation",
                "elements": [
                    {
                        "type": "rectangle",
                        "x": 100,
                        "y": 100,
                        "width": 150,
                        "height": 100,
                        "x2": 0,
                        "y2": 0,
                        "label": "Example",
                        "color": "#2563eb"
                    }
                ]
            },
            "animation": {
                "type": "none",
                "description": ""
            }
        }
    ],
    "practice_questions": ["Practice question"]
}

LESSON STRUCTURE:
- Create 4 to 8 logical teaching steps.
- Start with basic concepts.
- Build understanding progressively.
- Explain every important step.
- Include worked examples where appropriate.
- Adapt explanations to the student's level.
- Include useful practice questions.
- Do not skip important reasoning.
- Include useful practice questions.

PRACTICE QUESTION REQUIREMENTS:
- Always generate 3 to 5 practice questions.
- Never return an empty practice_questions array.
- Questions must test the concepts taught in the lesson.
- Include a mix of conceptual and numerical questions when appropriate.
- Do not include answers unless specifically requested.

SCIENTIFIC AND MATHEMATICAL ACCURACY:
- Never invent scientific facts.
- Verify equations and mathematical relationships.
- Ensure diagrams agree with equations and explanations.
- Never reverse cause-and-effect relationships.
- Keep units and variable meanings consistent.
- Use established scientific conventions.

IMPORTANT PHYSICS EXAMPLE:
For Newton's second law, the correct relationship is:

F = m × a

Force equals mass multiplied by acceleration.

Never write mass multiplied by force equals acceleration.
Show mass, force and acceleration as distinct quantities.
Use arrows and labels that represent their actual physical meanings.

SUBJECT-SPECIFIC VISUAL GUIDANCE:
- Physics: objects, forces, motion, vectors and measurements.
- Mathematics: graphs, geometry, number lines and equation steps.
- Chemistry: molecular structures, reactions and particle diagrams.
- Biology: correctly labeled anatomical structures and processes.
- Other subjects: use diagrams appropriate to the topic.


VISUAL RULES:
- Generate a diagram whenever it materially improves understanding.
- Every diagram must directly support the explanation.
- Use a compact, balanced layout that fills the useful canvas area.
- Keep the main object near the center.
- Arrange arrows and labels around the object with sufficient spacing.
- Never allow text, arrows, or shapes to overlap unnecessarily.
- Keep all coordinates within the 700 x 400 canvas.
- Use consistent colors for related quantities.
- Use readable labels and appropriate font sizes.
- Do not create decorative or meaningless shapes.

DRAWABLE ELEMENT RULES:
- Supported types: text, line, rectangle, circle, ellipse, arrow, polygon.
- Every element must contain:
  type, x, y, width, height, x2, y2, label, color.
- Polygon elements must also contain points as SVG coordinate pairs.
- Use the 700 x 400 canvas efficiently.
- For arrows, provide accurate start and end coordinates.
- For rectangles, x and y represent the top-left corner.
- For circles, x and y represent the center and width represents radius.
- For ellipses, x and y represent the center, width the horizontal radius, and height the vertical radius.
- Place arrow labels above or beside the arrow, never on top of the object.
- Do not repeat the same quantity as both an arrow label and a separate text element.
- Use separate text elements only when additional annotations are necessary.
- Keep labels short and scientifically correct.
- Ensure force arrows point in physically correct directions.
- Make arrow lengths visually consistent with relative magnitudes when possible.
- Return an empty elements array only when a visual is genuinely unnecessary.


ANIMATION RULES:
- Possible types: none, drawing, movement, highlight, reveal.
- Describe visual actions in chronological order.
- Do not claim an animation is already running.
- Make animation descriptions consistent with the diagram.

FINAL VALIDATION:
Before returning JSON, check:
1. Scientific facts are correct.
2. Equations are correct.
3. Diagram labels are correct.
4. Arrows show correct directions.
5. Visuals agree with explanations.
6. All required JSON fields exist.
7. The response is valid JSON.
"""

    try:
        provider = get_ai_provider()
        content = provider.generate_response(
            messages=[
                {"role": "system", "content": lesson_instructions},
                {
                    "role": "user",
                    "content": (
                        f"Subject: {request.subject or 'Automatically identify'}\n"
                        f"Level: {request.level}\n"
                        f"Question: {request.message}"
                    ),
                },
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
        )

        if not content:
            raise ValueError("AI returned an empty response.")

        lesson = json.loads(content)

        if not isinstance(lesson, dict):
            raise ValueError("Lesson response must be a JSON object.")

        required_fields = [
            "title",
            "subject",
            "level",
            "objectives",
            "steps",
            "practice_questions"
        ]

        for field in required_fields:
            if field not in lesson:
                if field == "practice_questions":
                    lesson[field] = []
                else:
                    raise ValueError(f"Missing required field: {field}")

        if not isinstance(lesson["steps"], list) or len(lesson["steps"]) == 0:
            raise ValueError("Lesson must contain at least one step.")

        return lesson

    except HTTPException:
        raise

    except json.JSONDecodeError as error:
        print(f"Lesson JSON parsing error: {error}")
        print(f"AI response: {content if 'content' in locals() else 'No response'}")

        raise HTTPException(
            status_code=502,
            detail="AI returned an invalid lesson format. Please try again."
        )

    except ValueError as error:
        print(f"Lesson validation error: {error}")

        raise HTTPException(
            status_code=502,
            detail=str(error)
        )

    except Exception as error:
        print(f"Lesson generation error: {error}")

        raise HTTPException(
            status_code=500,
            detail="Lesson generation failed. Check the backend terminal."
        )
# Normal response endpoint
@app.post("/ask")
def ask_tutor(question: Question):

    try:
        provider = get_ai_provider()
        answer = provider.generate_response(
            messages=[
                {"role": "system", "content": TUTOR_INSTRUCTIONS},
                {"role": "user", "content": question.message},
            ],
            temperature=0.6,
        )
        return {"answer": answer}

    except HTTPException:
        raise
    except Exception as error:
        print(f"AI provider error: {error}")
        raise HTTPException(
            status_code=500,
            detail="AI request failed. Check the backend terminal."
        )



# Streaming response endpoint
@app.post("/ask/stream")
def ask_tutor_stream(question: Question):

    provider = get_ai_provider()

    if question.conversation_id is not None:
        save_message(
            question.conversation_id,
            "user",
            question.message
        )

        conversation_history = get_messages(question.conversation_id)
        conversation_history = conversation_history[-20:]

        chat_messages = [
            {
                "role": message["role"],
                "content": message["content"]
            }
            for message in conversation_history
            if message["role"] in ("user", "assistant")
        ]

    else:
        chat_messages = [
            {
                "role": "user",
                "content": question.message
            }
        ]

    messages_for_ai = [
        {
            "role": "system",
            "content": TUTOR_INSTRUCTIONS
        },
        *chat_messages
    ]

    

    def generate():
        full_response = ""

        try:
            for content in provider.generate_stream(
                messages_for_ai,
                temperature=0.6,
            ):
                full_response += content
                yield content

            if question.conversation_id is not None and full_response:
                save_message(
                    question.conversation_id,
                    "assistant",
                    full_response
                )

        except Exception as error:
            print(f"AI streaming error: {error}")
            yield "\n\n[TutorMe error: Check the backend terminal.]"

    return StreamingResponse(
        generate(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )


# Retrieve conversation messages
@app.get("/conversations/{conversation_id}/messages")
def get_conversation_messages(conversation_id: int):

    conversations = get_conversations()

    if not any(c["id"] == conversation_id for c in conversations):
        raise HTTPException(
            status_code=404,
            detail="Conversation not found."
        )

    return get_messages(conversation_id)
