import unittest
import json
import os
import tempfile
from unittest.mock import patch, call, MagicMock

from iara.init import run_init, _step_api_key, _step_project_config, _step_review_config, _step_language, _step_provider, _mask_key, _step_ollama_setup


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


class TestStepProvider(unittest.TestCase):
    @patch("builtins.input", return_value="")
    def test_default_provider(self, mock_input):
        """Default provider is openrouter."""
        self.assertEqual(_step_provider(), "openrouter")

    @patch("builtins.input", return_value="anthropic")
    def test_custom_provider(self, mock_input):
        """Custom provider is accepted."""
        self.assertEqual(_step_provider(), "anthropic")


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
        "openrouter",       # provider
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
        mock_save_global.assert_called_once_with({
            "openrouter_api_key": "sk-or-test-key",
            "api_key": "sk-or-test-key"
        })

    @patch("iara.init.save_global_config")
    @patch("iara.init.save_config")
    @patch("iara.init.resolve_api_key", return_value=("sk-or-existing", "config"))
    @patch("builtins.input", side_effect=[
        "",                 # language (default en)
        "openrouter",       # provider
        "Y",                # use existing key
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

        mock_save_global.assert_called_once_with({
            "openrouter_api_key": "sk-or-existing",
            "api_key": "sk-or-existing"
        })


class TestStepProviderOllama(unittest.TestCase):
    @patch("builtins.input", return_value="ollama")
    def test_ollama_accepted(self, mock_input):
        self.assertEqual(_step_provider(), "ollama")


class TestStepApiKeyOllama(unittest.TestCase):
    @patch("builtins.print")
    @patch("urllib.request.urlopen")
    def test_ollama_skips_api_key_returns_none(self, mock_urlopen, mock_print):
        """_step_api_key for ollama calls _step_ollama_setup and returns None."""
        import json
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"models": [{"name": "qwen2.5-coder:7b"}]}).encode()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        result = _step_api_key("ollama")
        self.assertIsNone(result)


class TestStepOllamaSetup(unittest.TestCase):
    @patch("builtins.print")
    @patch("urllib.request.urlopen")
    def test_ollama_running_lists_models(self, mock_urlopen, mock_print):
        """When Ollama is running, available models are printed."""
        import json
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(
            {"models": [{"name": "qwen2.5-coder:7b"}, {"name": "codellama:13b"}]}
        ).encode()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        result = _step_ollama_setup()
        self.assertIsNone(result)
        printed = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("qwen2.5-coder:7b", printed)

    @patch("builtins.print")
    @patch("urllib.request.urlopen")
    def test_ollama_not_running_prints_install_instructions(self, mock_urlopen, mock_print):
        """When Ollama is not running, install instructions are shown."""
        import urllib.error
        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")

        result = _step_ollama_setup()
        self.assertIsNone(result)
        printed = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("ollama serve", printed)

    @patch("builtins.print")
    @patch("urllib.request.urlopen")
    def test_ollama_running_no_models_shows_pull_hint(self, mock_urlopen, mock_print):
        """When Ollama is running but no models are installed, shows pull hint."""
        import json
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"models": []}).encode()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        _step_ollama_setup()
        printed = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("ollama pull", printed)


class TestRunInitOllama(unittest.TestCase):
    @patch("builtins.print")
    @patch("iara.init.save_global_config")
    @patch("iara.init.save_config")
    @patch("urllib.request.urlopen")
    @patch("builtins.input", side_effect=[
        "en",           # language
        "ollama",       # provider
        "My Project",   # project name
        "Python",       # tech stack
        "A test",       # description
        "",             # focus areas (default)
        "",             # ignore patterns (default)
    ])
    def test_ollama_full_flow_no_api_key(self, mock_input, mock_urlopen,
                                         mock_save_config, mock_save_global, mock_print):
        """Full flow with Ollama: no API key prompt, no key saved to global config."""
        import json
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(
            {"models": [{"name": "qwen2.5-coder:7b"}]}
        ).encode()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("os.getcwd", return_value=tmpdir):
                run_init()

        mock_save_config.assert_called_once()
        local_config = mock_save_config.call_args[0][0]
        self.assertEqual(local_config["model"]["provider"], "ollama")

        # No ollama_api_key should be saved
        if mock_save_global.called:
            saved = mock_save_global.call_args[0][0]
            self.assertNotIn("ollama_api_key", saved)


if __name__ == "__main__":
    unittest.main()
