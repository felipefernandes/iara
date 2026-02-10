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

if __name__ == '__main__':
    unittest.main()
