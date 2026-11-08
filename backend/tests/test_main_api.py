
import unittest
from types import SimpleNamespace
from unittest.mock import patch, MagicMock, call

from fastapi.testclient import TestClient
import main


class TestMainAPI(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(main.app)

    # --------------------------------
    # BASIC ENDPOINTS
    # --------------------------------

    @patch("main.create_conversation", return_value=1)
    def test_create_conversation(self, mock_create):
        response = self.client.post(
            "/conversations",
            json={"title": "Physics"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], 1)
        self.assertEqual(response.json()["title"], "Physics")

    @patch("main.get_conversations", return_value=[
        {
            "id": 1,
            "title": "Physics",
            "created_at": "2026-11-05",
            "updated_at": "2026-11-05"
        }
    ])
    def test_list_conversations(self, mock_get):
        response = self.client.get("/conversations")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    @patch("main.delete_conversation", return_value=1)
    def test_delete_conversation(self, mock_delete):
        response = self.client.delete("/conversations/1")

        self.assertEqual(response.status_code, 200)

    @patch("main.delete_conversation", return_value=0)
    def test_delete_missing_conversation(self, mock_delete):
        response = self.client.delete("/conversations/999")

        self.assertEqual(response.status_code, 404)

    @patch("main.get_conversations", return_value=[])
    def test_empty_conversation_list(self, mock_get):
        response = self.client.get("/conversations")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_home_endpoint(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["project"], "TutorMe")

    def test_health_endpoint(self):
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertIn("status", response.json())

    # --------------------------------
    # GROQ CONFIGURATION
    # --------------------------------

    @patch("main.client", None)
    def test_ask_without_groq_key(self):
        response = self.client.post(
            "/ask",
            json={"message": "Explain Newton's laws"}
        )

        self.assertEqual(response.status_code, 500)

    @patch("main.client", None)
    def test_stream_without_groq_key(self):
        response = self.client.post(
            "/ask/stream",
            json={"message": "Explain gravity"}
        )

        self.assertEqual(response.status_code, 500)

    # --------------------------------
    # NORMAL AI RESPONSE
    # --------------------------------

    @patch("main.client")
    def test_successful_ask_response(self, mock_client):

        mock_client.chat.completions.create.return_value = (
            SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(
                            content="Newton's second law is F = ma."
                        )
                    )
                ]
            )
        )

        response = self.client.post(
            "/ask",
            json={"message": "Explain Newton's second law"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["answer"],
            "Newton's second law is F = ma."
        )

    # --------------------------------
    # SUCCESSFUL STREAMING
    # --------------------------------

    @patch("main.save_message")
    @patch("main.client")
    def test_successful_streaming(self, mock_client, mock_save):

        chunks = [
            SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        delta=SimpleNamespace(content="Newton's ")
                    )
                ]
            ),
            SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        delta=SimpleNamespace(content="second law ")
                    )
                ]
            ),
            SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        delta=SimpleNamespace(content="is F = ma.")
                    )
                ]
            )
        ]

        mock_client.chat.completions.create.return_value = iter(chunks)

        response = self.client.post(
            "/ask/stream",
            json={
                "message": "Explain Newton's second law",
                "conversation_id": 1
            }
        )

        expected_answer = "Newton's second law is F = ma."

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, expected_answer)

        mock_save.assert_has_calls([
            call(1, "user", "Explain Newton's second law"),
            call(1, "assistant", expected_answer)
        ])

        self.assertEqual(mock_save.call_count, 2)

    # --------------------------------
    # STREAMING FAILURE
    # --------------------------------

    @patch("main.save_message")
    @patch("main.client")
    def test_streaming_failure(self, mock_client, mock_save):

        mock_client.chat.completions.create.side_effect = (
            RuntimeError("Mock Groq failure")
        )

        response = self.client.post(
            "/ask/stream",
            json={
                "message": "Explain gravity",
                "conversation_id": 1
            }
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("TutorMe error", response.text)

        # Only the user message should be saved.
        mock_save.assert_called_once_with(
            1,
            "user",
            "Explain gravity"
        )


if __name__ == "__main__":
    unittest.main()
