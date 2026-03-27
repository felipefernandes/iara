import unittest
import json
import os
import tempfile
from unittest.mock import patch

from iara.config import load_config, DEFAULT_CONFIG, validate_ci_config

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
        self.assertEqual(config['project']['name'], "Generic Project")

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

    def test_ci_config_defaults(self):
        """Test that CI config has correct defaults."""
        config = load_config(self.config_path)
        self.assertIn("ci", config)
        self.assertEqual(config["ci"]["platform"], None)
        self.assertEqual(config["ci"]["review_mode"], "summary")

    def test_ci_config_parse_github(self):
        """Test parsing GitHub platform from config."""
        custom_config = {
            "ci": {
                "platform": "github",
                "review_mode": "inline"
            }
        }
        with open(self.config_path, 'w') as f:
            json.dump(custom_config, f)

        config = load_config(self.config_path)
        self.assertEqual(config["ci"]["platform"], "github")
        self.assertEqual(config["ci"]["review_mode"], "inline")

    def test_ci_config_parse_gitlab(self):
        """Test parsing GitLab platform from config."""
        custom_config = {
            "ci": {
                "platform": "gitlab",
                "review_mode": "summary"
            }
        }
        with open(self.config_path, 'w') as f:
            json.dump(custom_config, f)

        config = load_config(self.config_path)
        self.assertEqual(config["ci"]["platform"], "gitlab")
        self.assertEqual(config["ci"]["review_mode"], "summary")

    def test_ci_config_invalid_platform(self):
        """Test that truly unsupported platform values raise ValueError."""
        custom_config = {
            "ci": {
                "platform": "jenkins"
            }
        }
        with open(self.config_path, 'w') as f:
            json.dump(custom_config, f)

        with self.assertRaises(ValueError) as cm:
            load_config(self.config_path)
        self.assertIn("Invalid ci.platform", str(cm.exception))

    def test_ci_config_known_platforms_accepted(self):
        """Test that all known platforms pass validation without error."""
        for platform in ("github", "gitlab", "azure-devops", "bitbucket"):
            custom_config = {"ci": {"platform": platform}}
            with open(self.config_path, 'w') as f:
                json.dump(custom_config, f)
            config = load_config(self.config_path)
            self.assertEqual(config["ci"]["platform"], platform)

    def test_ci_config_invalid_review_mode(self):
        """Test that invalid review_mode raises ValueError."""
        custom_config = {
            "ci": {
                "platform": "github",
                "review_mode": "invalid"
            }
        }
        with open(self.config_path, 'w') as f:
            json.dump(custom_config, f)

        with self.assertRaises(ValueError) as cm:
            load_config(self.config_path)
        self.assertIn("Invalid ci.review_mode", str(cm.exception))

    def test_ci_config_inline_without_platform(self):
        """Test that inline mode without explicit platform is valid (auto-detected at runtime)."""
        custom_config = {
            "ci": {
                "review_mode": "inline"
            }
        }
        with open(self.config_path, 'w') as f:
            json.dump(custom_config, f)

        # Should not raise — platform is resolved at runtime via detect_platform()
        config = load_config(self.config_path)
        self.assertEqual(config["ci"]["review_mode"], "inline")
        self.assertIsNone(config["ci"]["platform"])

    def test_ci_config_platform_without_review_mode(self):
        """Test that platform without review_mode defaults to summary."""
        custom_config = {
            "ci": {
                "platform": "github"
            }
        }
        with open(self.config_path, 'w') as f:
            json.dump(custom_config, f)

        config = load_config(self.config_path)
        self.assertEqual(config["ci"]["platform"], "github")
        self.assertEqual(config["ci"]["review_mode"], "summary")

    def test_ci_config_empty_section(self):
        """Test that empty CI section uses defaults."""
        custom_config = {
            "ci": {}
        }
        with open(self.config_path, 'w') as f:
            json.dump(custom_config, f)

        config = load_config(self.config_path)
        self.assertEqual(config["ci"]["platform"], None)
        self.assertEqual(config["ci"]["review_mode"], "summary")

if __name__ == '__main__':
    unittest.main()
