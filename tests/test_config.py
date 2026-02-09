import unittest
import json
import os
import tempfile
from unittest.mock import patch

from iara.config import load_config, DEFAULT_CONFIG

class TestConfig(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.config_path = os.path.join(self.test_dir.name, ".iara.json")

    def tearDown(self):
        self.test_dir.cleanup()

    def test_load_config_defaults(self):
        """Test that default config is returned when file is missing."""
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

    def test_load_config_malformed_json(self):
        """Test behavior when JSON is malformed."""
        with open(self.config_path, 'w') as f:
            f.write("{ invalid json")

        config = load_config(self.config_path)
        self.assertEqual(config, DEFAULT_CONFIG)

if __name__ == '__main__':
    unittest.main()
