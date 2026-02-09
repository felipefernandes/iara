import unittest
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import importlib.util

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
script_path = os.path.join(project_root, "ai-codereview.py")

spec = importlib.util.spec_from_file_location("ai_codereview", script_path)
ai_codereview = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ai_codereview)

generate_system_prompt = ai_codereview.generate_system_prompt

class TestPrompt(unittest.TestCase):
    def test_generate_prompt_generic_default(self):
        """Test that default config generates the generic prompt."""
        config = {
            "project": {
                "name": "Projeto Genérico",
                "description": "Um projeto de software.",
                "tech_stack": ["Python"]
            },
            "review": {
               "focus_areas": []
            }
        }
        prompt = generate_system_prompt(config)
        self.assertIn("Projeto Genérico", prompt)
        self.assertIn("Python", prompt)

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
        # We expect some Unity specific keywords if logic is implemented
        # e.g. self.assertIn("GetComponent", prompt) 

if __name__ == '__main__':
    unittest.main()
