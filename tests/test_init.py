import unittest
import json
import os
import tempfile
from unittest.mock import patch, call

from iara.init import run_init, _step_api_key, _step_project_config, _step_review_config, _step_language, _mask_key


class TestMaskKey(unittest.TestCase):
    def test_long_key(self):
        """Long keys are masked."""
        self.assertEqual(_mask_key("sk-or-v1-abcdef1234567890"), "sk-or-v1...7890")

    def test_short_key(self):
        """Short keys return ***."""
        self.assertEqual(_mask_key("short"), "***")


class TestStepLanguage(unittest.TestCase):
    @patch("builtins.input", return_value="")
    def test_default_en(self, mock_input):
        """Default language is en."""
        self.assertEqual(_step_language(), "en")

    @patch("builtins.input", return_value="pt-br")
    def test_custom_language(self, mock_input):
        """Custom language code is accepted."""
        self.assertEqual(_step_language(), "pt-br")

    @patch("builtins.input", return_value="ES")
    def test_uppercase_normalized(self, mock_input):
        """Input is lowercased."""
        self.assertEqual(_step_language(), "es")


class TestStepProjectConfig(unittest.TestCase):
    @patch("builtins.input", side_effect=["", "", ""])
    def test_defaults(self, mock_input):
        """Default values are used when input is empty."""
        config = _step_project_config()
        self.assertEqual(config["tech_stack"], ["Python"])
        self.assertEqual(config["description"], "A software project.")
        self.assertIsNotNone(config["name"])

    @patch("builtins.input", side_effect=["My Game", "C#, Unity", "A puzzle game"])
    def test_custom_values(self, mock_input):
        """Custom values are accepted."""
        config = _step_project_config()
        self.assertEqual(config["name"], "My Game")
        self.assertEqual(config["tech_stack"], ["C#", "Unity"])
        self.assertEqual(config["description"], "A puzzle game")


class TestStepReviewConfig(unittest.TestCase):
    @patch("builtins.input", side_effect=["", ""])
    def test_defaults(self, mock_input):
        """Default values are used when input is empty."""
        config = _step_review_config()
        self.assertEqual(config["focus_areas"], ["Logic", "Security", "Performance", "Clean Code",
                                                     "Error Handling", "Testing"])
        self.assertEqual(config["ignore_patterns"], [])

    @patch("builtins.input", side_effect=["Security, Performance", "tests/*, docs/*"])
    def test_custom_values(self, mock_input):
        """Custom values are accepted."""
        config = _step_review_config()
        self.assertEqual(config["focus_areas"], ["Security", "Performance"])
        self.assertEqual(config["ignore_patterns"], ["tests/*", "docs/*"])


class TestRunInit(unittest.TestCase):
    @patch("builtins.print")
    @patch("iara.init.save_global_config")
    @patch("iara.init.save_config")
    @patch("iara.init.validate_api_key", return_value=(True, None))
    @patch("iara.init.resolve_api_key", return_value=(None, "none"))
    @patch("getpass.getpass", return_value="sk-or-test-key")
    @patch("builtins.input", side_effect=[
        "pt-br",            # language
        "Test Project",     # project name
        "Python",           # tech stack
        "A test project",   # description
        "",                 # focus areas (default)
        "",                 # ignore patterns (default)
    ])
    def test_full_flow_new_setup(self, mock_input, mock_getpass,
                                  mock_resolve, mock_validate,
                                  mock_save_config, mock_save_global,
                                  mock_print):
        """Full flow with new configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("os.getcwd", return_value=tmpdir):
                run_init()

        # Verify save_config was called
        mock_save_config.assert_called_once()
        config_arg = mock_save_config.call_args[0][0]
        self.assertEqual(config_arg["project"]["name"], "Test Project")
        self.assertEqual(config_arg["language"], "pt-br")

        # Verify save_global_config was called with the key
        mock_save_global.assert_called_once_with({"api_key": "sk-or-test-key"})

    @patch("iara.init.save_global_config")
    @patch("iara.init.save_config")
    @patch("iara.init.resolve_api_key", return_value=("sk-or-existing", "config"))
    @patch("builtins.input", side_effect=[
        "Y",                # use existing key
        "",                 # language (default en)
        "My Project",       # project name
        "",                 # tech stack (default)
        "",                 # description (default)
        "",                 # focus areas (default)
        "",                 # ignore patterns (default)
    ])
    def test_reuse_existing_key(self, mock_input, mock_resolve,
                                 mock_save_config, mock_save_global):
        """Reuse existing key when user accepts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("os.getcwd", return_value=tmpdir):
                run_init()

        mock_save_global.assert_called_once_with({"api_key": "sk-or-existing"})


if __name__ == "__main__":
    unittest.main()
