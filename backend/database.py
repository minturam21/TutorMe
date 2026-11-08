
import json
import sqlite3
from pathlib import Path
from contextlib import contextmanager

# Database location
BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "tutorme.db"


# -------------------------
# DATABASE CONNECTION
# -------------------------

@contextmanager
def get_connection(db_path=DATABASE_PATH):
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    try:
        yield connection
        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


# -------------------------
# DATABASE INITIALIZATION
# -------------------------

def initialize_database(db_path=DATABASE_PATH):

    with get_connection(db_path) as connection:

        connection.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id)
                    REFERENCES conversations(id)
                    ON DELETE CASCADE
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS lessons (
                id TEXT PRIMARY KEY,
                conversation_id INTEGER,
                title TEXT NOT NULL,
                subject TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                lesson_json TEXT NOT NULL,
                version INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id)
                    REFERENCES conversations(id)
                    ON DELETE SET NULL
            )
        """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_lessons_conversation
            ON lessons(conversation_id)
        """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_lessons_created
            ON lessons(created_at DESC)
        """)


# -------------------------
# CONVERSATION FUNCTIONS
# -------------------------

def create_conversation(title, db_path=DATABASE_PATH):

    with get_connection(db_path) as connection:

        cursor = connection.execute(
            "INSERT INTO conversations (title) VALUES (?)",
            (title,)
        )

        return cursor.lastrowid


def save_message(conversation_id, role, content, db_path=DATABASE_PATH):

    with get_connection(db_path) as connection:

        connection.execute(
            """
            INSERT INTO messages (conversation_id, role, content)
            VALUES (?, ?, ?)
            """,
            (conversation_id, role, content),
        )

        connection.execute(
            """
            UPDATE conversations
            SET updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (conversation_id,),
        )


def get_conversations(db_path=DATABASE_PATH):

    with get_connection(db_path) as connection:

        rows = connection.execute("""
            SELECT id, title, created_at, updated_at
            FROM conversations
            ORDER BY updated_at DESC
        """).fetchall()

        return [dict(row) for row in rows]


def get_messages(conversation_id, db_path=DATABASE_PATH):

    with get_connection(db_path) as connection:

        rows = connection.execute(
            """
            SELECT id, conversation_id, role, content, created_at
            FROM messages
            WHERE conversation_id = ?
            ORDER BY id ASC
            """,
            (conversation_id,),
        ).fetchall()

        return [dict(row) for row in rows]


def delete_conversation(conversation_id, db_path=DATABASE_PATH):

    with get_connection(db_path) as connection:

        cursor = connection.execute(
            "DELETE FROM conversations WHERE id = ?",
            (conversation_id,)
        )

        return cursor.rowcount


# -------------------------
# LESSON FUNCTIONS
# -------------------------

def save_lesson(lesson, conversation_id=None, db_path=DATABASE_PATH):

    if hasattr(lesson, "model_dump"):
        lesson = lesson.model_dump(mode="json")

    if not isinstance(lesson, dict):
        raise ValueError("Lesson must be a dictionary or Pydantic model.")

    required_fields = ["id", "title", "subject", "difficulty"]

    if any(not lesson.get(field) for field in required_fields):
        raise ValueError("Lesson is missing required fields.")

    lesson_json = json.dumps(lesson, ensure_ascii=False)

    with get_connection(db_path) as connection:

        connection.execute(
            """
            INSERT INTO lessons (
                id,
                conversation_id,
                title,
                subject,
                difficulty,
                lesson_json,
                version
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                lesson["id"],
                conversation_id,
                lesson["title"],
                lesson["subject"],
                lesson["difficulty"],
                lesson_json,
                lesson.get("version", 1),
            ),
        )

    return lesson["id"]


def get_lesson(lesson_id, db_path=DATABASE_PATH):

    with get_connection(db_path) as connection:

        row = connection.execute(
            """
            SELECT *
            FROM lessons
            WHERE id = ?
            """,
            (lesson_id,),
        ).fetchone()

        if row is None:
            return None

        result = dict(row)
        result["lesson"] = json.loads(result.pop("lesson_json"))

        return result


def get_lessons(conversation_id=None, db_path=DATABASE_PATH):

    with get_connection(db_path) as connection:

        if conversation_id is None:

            rows = connection.execute("""
                SELECT id, conversation_id, title, subject,
                       difficulty, version, created_at, updated_at
                FROM lessons
                ORDER BY created_at DESC
            """).fetchall()

        else:

            rows = connection.execute(
                """
                SELECT id, conversation_id, title, subject,
                       difficulty, version, created_at, updated_at
                FROM lessons
                WHERE conversation_id = ?
                ORDER BY created_at DESC
                """,
                (conversation_id,),
            ).fetchall()

        return [dict(row) for row in rows]


def delete_lesson(lesson_id, db_path=DATABASE_PATH):

    with get_connection(db_path) as connection:

        cursor = connection.execute(
            "DELETE FROM lessons WHERE id = ?",
            (lesson_id,)
        )

        return cursor.rowcount
