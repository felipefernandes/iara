import unittest
import json
import os
import tempfile
from unittest.mock import patch

# We will need to import the functions from ai-codereview.py
# Since it's a script with a hyphen, we use importlib
import importlib.util

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
script_path = os.path.join(project_root, "ai-codereview.py")

spec = importlib.util.spec_from_file_location("ai_codereview", script_path)
ai_codereview = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ai_codereview)

load_config = ai_codereview.load_config
DEFAULT_CONFIG = ai_codereview.DEFAULT_CONFIG

class TestConfig(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.config_path = os.path.join(self.test_dir.name, ".iara.json")

    def tearDown(self):
        self.test_dir.cleanup()

    def test_load_config_defaults(self):
        """Test that default config is returned when file is missing."""
        # Ensure file doesn't exist
        if os.path.exists(self.config_path):
            os.remove(self.config_path)
            
        config = load_config(self.config_path)
        self.assertEqual(config, DEFAULT_CONFIG)
        self.assertEqual(config['project']['name'], "Projeto Genérico")

    def test_load_config_from_file(self):
        """Test loading configuration from a JSON file."""
        custom_config = {
            "project": {
                "name": "Test Project",
                "description": "A test project",
                "tech_stack": ["Python", "Django"]
            },
            "model": {
                "preferred": "test-model"
            }
        }
        with open(self.config_path, 'w') as f:
            json.dump(custom_config, f)

        config = load_config(self.config_path)
        self.assertEqual(config['project']['name'], "Test Project")
        self.assertEqual(config['project']['tech_stack'], ["Python", "Django"])
        # Should merge with defaults for missing keys? Or replace? 
        # Design decision: Simple merge or full replace. Let's assume full replace of top-level keys for now, 
        # but robust implementation might merge. For this test, we check what we wrote.

    def test_load_config_malformed_json(self):
        """Test behavior when JSON is malformed."""
        with open(self.config_path, 'w') as f:
            f.write("{ invalid json")

        # Should probably return default config and log warning, or raise error.
        # Let's say it prints warning and returns default for robustness.
        with patch('sys.stderr.write') as mock_stderr:
            config = load_config(self.config_path)
            self.assertEqual(config, DEFAULT_CONFIG)
            # Verify warning was printed
            # mock_stderr.assert_called() 

if __name__ == '__main__':
    unittest.main()
