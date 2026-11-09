import unittest

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


if __name__ == "__main__":
    unittest.main()
