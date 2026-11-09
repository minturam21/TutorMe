"""Provider-neutral AI adapter for TutorMe.

Gemini is the default provider. Groq remains available as a fallback by setting
AI_PROVIDER=groq and providing GROQ_API_KEY in backend/.env.
"""
from __future__ import annotations

import os
from collections.abc import Iterator

from dotenv import load_dotenv

load_dotenv(override=True)


class AIProvider:
    """Unified text-generation interface for Gemini and Groq."""

    def __init__(self, model: str | None = None, provider: str | None = None):
        requested = (provider or os.getenv("AI_PROVIDER", "gemini")).strip().lower()
        gemini_key = os.getenv("GEMINI_API_KEY")
        groq_key = os.getenv("GROQ_API_KEY")

        # If Gemini is the default but its key is not configured, use Groq when
        # a Groq key exists. An explicitly selected provider is never silently changed.
        if requested == "gemini" and not gemini_key and groq_key and provider is None:
            requested = "groq"

        if requested == "gemini":
            if not gemini_key:
                raise RuntimeError("GEMINI_API_KEY is missing from backend/.env.")
            try:
                from google import genai
            except ImportError as error:
                raise RuntimeError(
                    "Gemini SDK is not installed. Install backend requirements."
                ) from error
            self.client = genai.Client(api_key=gemini_key)
            self.model = model or os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
        elif requested == "groq":
            if not groq_key:
                raise RuntimeError("GROQ_API_KEY is missing from backend/.env.")
            try:
                from groq import Groq
            except ImportError as error:
                raise RuntimeError("Groq SDK is not installed.") from error
            self.client = Groq(api_key=groq_key)
            self.model = model or os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
        else:
            raise RuntimeError("AI_PROVIDER must be either 'gemini' or 'groq'.")

        self.provider = requested

    @staticmethod
    def _gemini_contents(messages: list[dict]) -> tuple[str | None, list[dict]]:
        system_parts = []
        contents = []
        for message in messages:
            role = message.get("role", "user")
            text = message.get("content", "")
            if role == "system":
                system_parts.append(text)
            else:
                contents.append({
                    "role": "model" if role == "assistant" else "user",
                    "parts": [{"text": text}],
                })
        return ("\n\n".join(system_parts) or None), contents

    @staticmethod
    def _gemini_config(temperature: float, max_tokens: int, response_format: dict | None):
        config = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }
        if response_format:
            config["response_mime_type"] = "application/json"
            if response_format.get("type") == "json_schema":
                schema = response_format.get("json_schema", {}).get("schema")
                if schema:
                    config["response_json_schema"] = schema
        return config

    def generate_response(
        self,
        messages: list[dict],
        temperature: float = 0.3,
        max_tokens: int = 8000,
        response_format: dict | None = None,
    ) -> str:
        try:
            if self.provider == "gemini":
                system_instruction, contents = self._gemini_contents(messages)
                config = self._gemini_config(temperature, max_tokens, response_format)
                if system_instruction:
                    config["system_instruction"] = system_instruction
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=contents,
                    config=config,
                )
                return response.text or ""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=response_format,
            )
            return response.choices[0].message.content or ""
        except Exception as error:
            raise RuntimeError(f"{self.provider.title()} API request failed: {error}") from error

    def generate_stream(
        self,
        messages: list[dict],
        temperature: float = 0.6,
    ) -> Iterator[str]:
        """Yield text chunks for the existing /ask/stream endpoint."""
        try:
            if self.provider == "gemini":
                system_instruction, contents = self._gemini_contents(messages)
                config = {"temperature": temperature}
                if system_instruction:
                    config["system_instruction"] = system_instruction
                stream = self.client.models.generate_content_stream(
                    model=self.model,
                    contents=contents,
                    config=config,
                )
                for chunk in stream:
                    if chunk.text:
                        yield chunk.text
            else:
                stream = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    stream=True,
                )
                for chunk in stream:
                    content = chunk.choices[0].delta.content
                    if content:
                        yield content
        except Exception as error:
            raise RuntimeError(f"{self.provider.title()} streaming request failed: {error}") from error
