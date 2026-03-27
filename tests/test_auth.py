import unittest
import json
import os
import tempfile
from unittest.mock import patch, MagicMock

from iara.auth import resolve_api_key, validate_api_key, save_global_config, _load_global_config, normalize_provider


class TestResolveApiKey(unittest.TestCase):
    @patch.dict(os.environ, {"OPENROUTER_API_KEY": "sk-or-test-key"})
    def test_resolve_from_env(self):
        """Env var has highest priority."""
        key, source = resolve_api_key()
        self.assertEqual(key, "sk-or-test-key")
        self.assertEqual(source, "env")

    @patch.dict(os.environ, {"OPENAI_API_KEY": "sk-openai-test-key"})
    def test_resolve_from_env_openai(self):
        """Provider-specific env var is used."""
        key, source = resolve_api_key("openai")
        self.assertEqual(key, "sk-openai-test-key")
        self.assertEqual(source, "env")

    @patch.dict(os.environ, {}, clear=True)
    @patch("iara.auth._load_global_config", return_value={"api_key": "sk-or-config-key"})
    def test_resolve_from_config(self, mock_config):
        """Global config is used when env var doesn't exist."""
        # Ensure OPENROUTER_API_KEY is not in env
        os.environ.pop("OPENROUTER_API_KEY", None)
        key, source = resolve_api_key()
        self.assertEqual(key, "sk-or-config-key")
        self.assertEqual(source, "config")

    @patch.dict(os.environ, {}, clear=True)
    @patch("iara.auth._load_global_config", return_value={"openai_api_key": "sk-openai-config"})
    def test_resolve_from_config_openai(self, mock_config):
        """Provider-specific config key is used."""
        key, source = resolve_api_key("openai")
        self.assertEqual(key, "sk-openai-config")
        self.assertEqual(source, "config")

    @patch.dict(os.environ, {"OPENROUTER_API_KEY": "sk-or-env-key"})
    @patch("iara.auth._load_global_config", return_value={"api_key": "sk-or-config-key"})
    def test_env_takes_precedence_over_config(self, mock_config):
        """Env var takes precedence over config."""
        key, source = resolve_api_key()
        self.assertEqual(key, "sk-or-env-key")
        self.assertEqual(source, "env")

    @patch.dict(os.environ, {}, clear=True)
    @patch("iara.auth._load_global_config", return_value={"api_key": "sk-or-legacy"})
    def test_openrouter_fallback_to_legacy_config(self, mock_config):
        """OpenRouter falls back to legacy api_key field."""
        key, source = resolve_api_key("openrouter")
        self.assertEqual(key, "sk-or-legacy")
        self.assertEqual(source, "config")

    @patch.dict(os.environ, {}, clear=True)
    @patch("iara.auth._load_global_config", return_value={})
    def test_resolve_none(self, mock_config):
        """Returns None when no key is found."""
        os.environ.pop("OPENROUTER_API_KEY", None)
        key, source = resolve_api_key()
        self.assertIsNone(key)
        self.assertEqual(source, "none")

    @patch.dict(os.environ, {}, clear=True)
    def test_invalid_provider_returns_none(self):
        """Invalid provider returns none."""
        key, source = resolve_api_key("invalid")
        self.assertIsNone(key)
        self.assertEqual(source, "none")


class TestNormalizeProvider(unittest.TestCase):
    def test_default_provider(self):
        self.assertEqual(normalize_provider(None), "openrouter")

    def test_invalid_provider(self):
        self.assertIsNone(normalize_provider("not-a-provider"))


class TestSaveGlobalConfig(unittest.TestCase):
    def test_save_and_load(self):
        """Save and load global config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.json")
            with patch("iara.auth.GLOBAL_CONFIG_DIR", tmpdir), \
                 patch("iara.auth.GLOBAL_CONFIG_PATH", config_path):
                save_global_config({"api_key": "sk-or-test"})

                self.assertTrue(os.path.exists(config_path))
                with open(config_path, "r") as f:
                    data = json.load(f)
                self.assertEqual(data["api_key"], "sk-or-test")


class TestValidateApiKey(unittest.TestCase):
    @patch("urllib.request.urlopen")
    def test_valid_key(self, mock_urlopen):
        """Valid key returns True."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        is_valid, error = validate_api_key("sk-or-valid")
        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_skip_validation_non_openrouter(self):
        """Non-openrouter providers skip validation."""
        is_valid, error = validate_api_key("sk-openai", provider="openai")
        self.assertTrue(is_valid)
        self.assertIsNone(error)

    @patch("urllib.request.urlopen")
    def test_invalid_key_401(self, mock_urlopen):
        """Invalid key returns False with message."""
        import urllib.error
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="", code=401, msg="Unauthorized", hdrs=None, fp=None
        )

        is_valid, error = validate_api_key("sk-or-invalid")
        self.assertFalse(is_valid)
        self.assertIn("401", error)

    @patch("urllib.request.urlopen")
    def test_network_error(self, mock_urlopen):
        """Network error returns True to avoid blocking valid keys."""
        import urllib.error
        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")

        is_valid, error = validate_api_key("sk-or-test")
        self.assertTrue(is_valid)
        self.assertIsNone(error)

    @patch("urllib.request.urlopen")
    def test_http_500_error_skips_validation(self, mock_urlopen):
        """HTTP Errors other than 401/403 (like 500) assume key might be valid to not block the user."""
        import urllib.error
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="", code=500, msg="Internal Server Error", hdrs=None, fp=None
        )

        is_valid, error = validate_api_key("sk-500-test")
        self.assertTrue(is_valid)
        self.assertIsNone(error)

    @patch("urllib.request.urlopen")
    def test_validate_anthropic_valid_key(self, mock_urlopen):
        """Anthropic: valid key returns True against /v1/models endpoint."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        is_valid, error = validate_api_key("sk-ant-valid", provider="anthropic")
        self.assertTrue(is_valid)
        self.assertIsNone(error)

        # Verify the correct Anthropic endpoint was hit
        req = mock_urlopen.call_args[0][0]
        self.assertIn("api.anthropic.com", req.full_url)
        self.assertEqual(req.get_header("X-api-key"), "sk-ant-valid")

    @patch("urllib.request.urlopen")
    def test_validate_anthropic_invalid_key_401(self, mock_urlopen):
        """Anthropic: invalid key returns False with 401 message."""
        import urllib.error
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="", code=401, msg="Unauthorized", hdrs=None, fp=None
        )

        is_valid, error = validate_api_key("sk-ant-bad", provider="anthropic")
        self.assertFalse(is_valid)
        self.assertIn("401", error)


if __name__ == "__main__":
    unittest.main()

