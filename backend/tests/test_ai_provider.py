import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from services.ai_provider import AIProvider


class GeminiRequestMappingTests(unittest.TestCase):
    def test_system_messages_become_system_instruction(self):
        system, contents = AIProvider._gemini_contents([
            {"role": "system", "content": "Teach clearly."},
            {"role": "user", "content": "What is force?"},
            {"role": "assistant", "content": "Force is an interaction."},
        ])

        self.assertEqual(system, "Teach clearly.")
        self.assertEqual(contents, [
            {"role": "user", "parts": [{"text": "What is force?"}]},
            {"role": "model", "parts": [{"text": "Force is an interaction."}]},
        ])

    def test_json_object_mode_maps_to_gemini_json_mime_type(self):
        config = AIProvider._gemini_config(
            temperature=0.2,
            max_tokens=1200,
            response_format={"type": "json_object"},
        )

        self.assertEqual(config["response_mime_type"], "application/json")
        self.assertEqual(config["temperature"], 0.2)
        self.assertEqual(config["max_output_tokens"], 1200)
        self.assertNotIn("response_json_schema", config)

    def test_json_schema_mode_passes_standard_schema(self):
        schema = {
            "type": "object",
            "properties": {"answer": {"type": ["string", "null"]}},
            "required": ["answer"],
            "additionalProperties": False,
        }
        config = AIProvider._gemini_config(
            temperature=0.3,
            max_tokens=800,
            response_format={
                "type": "json_schema",
                "json_schema": {"name": "answer", "strict": True, "schema": schema},
            },
        )

        self.assertEqual(config["response_mime_type"], "application/json")
        self.assertEqual(config["response_json_schema"], schema)


class ProviderFallbackTests(unittest.TestCase):
    def make_provider(self, provider="gemini", fallback=True):
        instance = object.__new__(AIProvider)
        instance.provider = provider
        instance.model = "test-model"
        instance.client = Mock()
        instance.fallback_client = Mock() if fallback else None
        instance.fallback_model = "test-groq-model" if fallback else None
        return instance

    def test_gemini_max_tokens_uses_groq_fallback(self):
        provider = self.make_provider()
        provider.client.models.generate_content.return_value = SimpleNamespace(
            text='{"steps": [',
            candidates=[
                SimpleNamespace(finish_reason="MAX_TOKENS")
            ],
        )
        provider.fallback_client.chat.completions.create.return_value = (
            SimpleNamespace(
                choices=[SimpleNamespace(
                    message=SimpleNamespace(content='{"steps": []}')
                )]
            )
        )

        result = provider.generate_response(
            [{"role": "user", "content": "Generate JSON"}],
            response_format={"type": "json_object"},
        )

        self.assertEqual(result, '{"steps": []}')
        provider.fallback_client.chat.completions.create.assert_called_once()

    def test_gemini_failure_uses_groq_fallback(self):
        provider = self.make_provider()
        provider.client.models.generate_content.side_effect = Exception("Gemini unavailable")
        provider.fallback_client.chat.completions.create.return_value = (
            SimpleNamespace(
                choices=[SimpleNamespace(
                    message=SimpleNamespace(content="Fallback answer")
                )]
            )
        )

        result = provider.generate_response([{"role": "user", "content": "Hello"}])

        self.assertEqual(result, "Fallback answer")
        provider.fallback_client.chat.completions.create.assert_called_once()

    def test_gemini_fallback_converts_json_schema_to_json_object_mode(self):
        provider = self.make_provider()
        provider.client.models.generate_content.side_effect = Exception(
            "Gemini unavailable"
        )
        provider.fallback_client.chat.completions.create.return_value = (
            SimpleNamespace(
                choices=[SimpleNamespace(
                    message=SimpleNamespace(content='{"steps": []}')
                )]
            )
        )

        schema_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "test_response",
                "strict": True,
                "schema": {"type": "object", "properties": {}, "required": []},
            },
        }

        provider.generate_response(
            [{"role": "user", "content": "Generate JSON"}],
            response_format=schema_format,
        )

        kwargs = provider.fallback_client.chat.completions.create.call_args.kwargs
        self.assertEqual(kwargs["response_format"], {"type": "json_object"})

    def test_direct_groq_converts_json_schema_to_json_object_mode(self):
        provider = self.make_provider(provider="groq", fallback=False)
        provider.client.chat.completions.create.return_value = (
            SimpleNamespace(
                choices=[SimpleNamespace(
                    message=SimpleNamespace(content='{"steps": []}')
                )]
            )
        )

        schema_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "test_response",
                "strict": True,
                "schema": {"type": "object", "properties": {}, "required": []},
            },
        }

        provider.generate_response(
            [{"role": "user", "content": "Generate JSON"}],
            response_format=schema_format,
        )

        kwargs = provider.client.chat.completions.create.call_args.kwargs
        self.assertEqual(kwargs["response_format"], {"type": "json_object"})

    def test_both_provider_failures_are_reported(self):
        provider = self.make_provider()
        provider.client.models.generate_content.side_effect = Exception("Gemini unavailable")
        provider.fallback_client.chat.completions.create.side_effect = Exception(
            "Groq quota exhausted"
        )

        with self.assertRaises(RuntimeError) as context:
            provider.generate_response([{"role": "user", "content": "Hello"}])

        message = str(context.exception)
        self.assertIn("Gemini API request failed", message)
        self.assertIn("Gemini unavailable", message)
        self.assertIn("Groq fallback failed", message)
        self.assertIn("Groq quota exhausted", message)

    def test_direct_groq_failure_is_labelled_correctly(self):
        provider = self.make_provider(provider="groq", fallback=False)
        provider.client.chat.completions.create.side_effect = Exception(
            "Groq quota exhausted"
        )

        with self.assertRaises(RuntimeError) as context:
            provider.generate_response([{"role": "user", "content": "Hello"}])

        self.assertIn("Groq API request failed", str(context.exception))
        self.assertIn("Groq quota exhausted", str(context.exception))

    def test_gemini_stream_failure_uses_groq_fallback(self):
        provider = self.make_provider()
        provider.client.models.generate_content_stream.side_effect = Exception(
            "Gemini stream unavailable"
        )
        provider.fallback_client.chat.completions.create.return_value = [
            SimpleNamespace(
                choices=[SimpleNamespace(
                    delta=SimpleNamespace(content="Fallback stream")
                )]
            )
        ]

        result = list(provider.generate_stream([
            {"role": "user", "content": "Hello"}
        ]))

        self.assertEqual(result, ["Fallback stream"])

    def test_partial_gemini_stream_does_not_restart_with_groq(self):
        provider = self.make_provider()

        def broken_stream(**kwargs):
            yield SimpleNamespace(text="Partial answer")
            raise Exception("Gemini stream interrupted")

        provider.client.models.generate_content_stream.side_effect = broken_stream

        stream = provider.generate_stream([
            {"role": "user", "content": "Hello"}
        ])

        self.assertEqual(next(stream), "Partial answer")

        with self.assertRaises(RuntimeError) as context:
            next(stream)

        self.assertIn("Gemini streaming request failed", str(context.exception))
        self.assertIn("Gemini stream interrupted", str(context.exception))
        provider.fallback_client.chat.completions.create.assert_not_called()


if __name__ == "__main__":
    unittest.main()
