
import os

from dotenv import load_dotenv
from groq import Groq


# Load environment variables from the backend directory.
load_dotenv(override=True)


class AIProvider:
    """
    Handles communication with the Groq API.
    Keeps AI communication separate from lesson generation.
    """

    def __init__(self, model: str = "openai/gpt-oss-120b"):
        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY is missing from the backend .env file."
            )

        self.client = Groq(api_key=api_key)
        self.model = model

    def generate_response(
        self,
        messages: list[dict],
        temperature: float = 0.3,
        max_tokens: int = 8000,
        response_format: dict | None = None,
    ) -> str:
        """
        Send messages to Groq and return the generated text.
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=response_format,
            )

            return response.choices[0].message.content or ""

        except Exception as error:
            raise RuntimeError(
                f"Groq API request failed: {error}"
            ) from error
