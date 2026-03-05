import unittest

from iara.prompt import generate_system_prompt

class TestPrompt(unittest.TestCase):
    def test_generate_prompt_generic_default(self):
        """Test that default config generates the generic prompt."""
        config = {
            "project": {
                "name": "Generic Project",
                "description": "A software project.",
                "tech_stack": ["Python"]
            },
            "review": {
               "focus_areas": []
            }
        }
        prompt = generate_system_prompt(config)
        self.assertIn("Generic Project", prompt)
        self.assertIn("Python", prompt)
        self.assertIn("English", prompt)

    def test_generate_prompt_unity(self):
        """Test that Unity config generates Unity-specific instructions."""
        config = {
            "project": {
                "name": "Unity Game",
                "description": "A mobile game",
                "tech_stack": ["C#", "Unity"]
            },
             "review": {
                "focus_areas": ["Performance"]
            }
        }
        prompt = generate_system_prompt(config)
        self.assertIn("Unity", prompt)
        self.assertIn("C#", prompt)
        self.assertIn("mobile game", prompt)

    def test_generate_prompt_language_ptbr(self):
        """Test that pt-br language is injected into prompt."""
        config = {
            "project": {
                "name": "Meu Projeto",
                "description": "Um projeto.",
                "tech_stack": ["Python"]
            },
            "language": "pt-br"
        }
        prompt = generate_system_prompt(config)
        self.assertIn("Brazilian Portuguese", prompt)

    def test_generate_prompt_language_default(self):
        """Test that missing language defaults to English."""
        config = {
            "project": {
                "name": "Test",
                "description": "Test.",
                "tech_stack": []
            }
        }
        prompt = generate_system_prompt(config)
        self.assertIn("English", prompt)

    def test_generate_prompt_unknown_language(self):
        """Test that unknown language code is used as-is."""
        config = {
            "project": {
                "name": "Test",
                "description": "Test.",
                "tech_stack": []
            },
            "language": "swahili"
        }
        prompt = generate_system_prompt(config)
        self.assertIn("swahili", prompt)

    def test_generate_prompt_summary_mode(self):
        """Test that summary mode generates markdown format instructions."""
        config = {
            "project": {
                "name": "Test Project",
                "description": "Test description",
                "tech_stack": ["Python"]
            }
        }
        prompt = generate_system_prompt(config, review_mode="summary")

        # Should include summary mode format instructions
        self.assertIn("RESPONSE FORMAT", prompt)
        self.assertIn("Be direct and objective", prompt)
        self.assertIn("Bug", prompt)
        self.assertIn("Security", prompt)

        # Should NOT include JSON schema instructions
        self.assertNotIn("JSON object", prompt)
        self.assertNotIn("comments", prompt.lower()[:200])  # Check early in prompt

    def test_generate_prompt_inline_mode(self):
        """Test that inline mode generates JSON schema instructions."""
        config = {
            "project": {
                "name": "Test Project",
                "description": "Test description",
                "tech_stack": ["Python"]
            }
        }
        prompt = generate_system_prompt(config, review_mode="inline")

        # Should include JSON schema instructions
        self.assertIn("OUTPUT FORMAT", prompt)
        self.assertIn("JSON object", prompt)
        self.assertIn('"summary"', prompt)
        self.assertIn('"comments"', prompt)
        self.assertIn('"file"', prompt)
        self.assertIn('"line"', prompt)
        self.assertIn('"severity"', prompt)
        self.assertIn('"message"', prompt)

        # Should include severity validation
        self.assertIn("bug", prompt)
        self.assertIn("security", prompt)
        self.assertIn("performance", prompt)

        # Should NOT include summary mode format
        self.assertNotIn("Be direct and objective", prompt)

    def test_generate_prompt_inline_mode_includes_examples(self):
        """Test that inline mode includes JSON examples."""
        config = {
            "project": {
                "name": "Test Project",
                "description": "Test description",
                "tech_stack": ["Python"]
            }
        }
        prompt = generate_system_prompt(config, review_mode="inline")

        # Should include example JSON
        self.assertIn("Example", prompt)
        self.assertIn("```json", prompt)

    def test_generate_prompt_default_mode_is_summary(self):
        """Test that default review_mode is summary."""
        config = {
            "project": {
                "name": "Test Project",
                "description": "Test description",
                "tech_stack": ["Python"]
            }
        }
        prompt_default = generate_system_prompt(config)
        prompt_summary = generate_system_prompt(config, review_mode="summary")

        # Default should match summary mode
        self.assertEqual(prompt_default, prompt_summary)

if __name__ == '__main__':
    unittest.main()
