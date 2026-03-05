import unittest
import io
import json
import urllib.error
from unittest.mock import patch, MagicMock

from iara.reviewer import (
    _build_headers,
    _build_payload,
    _extract_content,
    _extract_error_message,
    review_code_with_model,
    review_code,
)


class MockResponse:
    def __init__(self, payload):
        self.payload = payload

    def read(self):
        return json.dumps(self.payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


# ── _extract_error_message ──────────────────────────────────────────────


class TestExtractErrorMessage(unittest.TestCase):
    def test_404_returns_model_not_available(self):
        msg = _extract_error_message(404, '{}', "gpt-4o")
        self.assertEqual(msg, "model not available")

    def test_429_returns_rate_limited(self):
        msg = _extract_error_message(429, '{}', "gpt-4o")
        self.assertIn("rate limited", msg)

    def test_401_returns_invalid_api_key(self):
        msg = _extract_error_message(401, '{}', "gpt-4o")
        self.assertEqual(msg, "invalid API key")

    def test_400_with_invalid_model_message(self):
        body = json.dumps({"error": {"message": "Not a valid model ID"}})
        msg = _extract_error_message(400, body, "bad-model")
        self.assertEqual(msg, "model ID no longer valid")

    def test_400_with_other_message(self):
        body = json.dumps({"error": {"message": "Something went wrong"}})
        msg = _extract_error_message(400, body, "gpt-4o")
        self.assertEqual(msg, "Something went wrong")

    def test_500_no_json_body(self):
        msg = _extract_error_message(500, "not json", "gpt-4o")
        self.assertEqual(msg, "HTTP 500")

    def test_500_empty_message(self):
        body = json.dumps({"error": {"message": ""}})
        msg = _extract_error_message(500, body, "gpt-4o")
        self.assertEqual(msg, "HTTP 500")


# ── _build_headers ──────────────────────────────────────────────────────


class TestBuildHeaders(unittest.TestCase):
    def test_bearer_auth_for_openai(self):
        headers = _build_headers("sk-test", "openai")
        self.assertEqual(headers["Authorization"], "Bearer sk-test")
        self.assertNotIn("x-api-key", headers)

    def test_x_api_key_for_anthropic(self):
        headers = _build_headers("sk-ant-test", "anthropic")
        self.assertEqual(headers["x-api-key"], "sk-ant-test")
        self.assertIn("anthropic-version", headers)
        self.assertNotIn("Authorization", headers)

    def test_openrouter_includes_referer(self):
        headers = _build_headers("sk-or-test", "openrouter")
        self.assertIn("HTTP-Referer", headers)
        self.assertIn("X-Title", headers)

    def test_unknown_provider_falls_back_to_openrouter(self):
        headers = _build_headers("sk-test", "unknown_provider")
        self.assertIn("Authorization", headers)


# ── _extract_content ────────────────────────────────────────────────────


class TestExtractContent(unittest.TestCase):
    def test_extract_content_anthropic(self):
        result = {"content": [{"text": "Hello"}]}
        self.assertEqual(_extract_content(result, "anthropic"), "Hello")

    def test_extract_content_anthropic_empty(self):
        with self.assertRaises(ValueError):
            _extract_content({"content": []}, "anthropic")

    def test_extract_content_anthropic_no_text(self):
        with self.assertRaises(ValueError):
            _extract_content({"content": [{"type": "text"}]}, "anthropic")

    def test_extract_content_openai(self):
        result = {"choices": [{"message": {"content": "Hi"}}]}
        self.assertEqual(_extract_content(result, "openai"), "Hi")

    def test_extract_content_openai_none_content(self):
        result = {"choices": [{"message": {"content": None}}]}
        with self.assertRaises(ValueError):
            _extract_content(result, "openai")

    def test_extract_content_no_choices(self):
        with self.assertRaises(ValueError):
            _extract_content({}, "openai")

    def test_extract_content_empty_choices(self):
        with self.assertRaises(ValueError):
            _extract_content({"choices": []}, "openai")


# ── _build_payload ──────────────────────────────────────────────────────


class TestPayloads(unittest.TestCase):
    def test_build_payload_anthropic(self):
        payload = _build_payload("diff", "claude-3", "sys", "anthropic")
        self.assertEqual(payload["model"], "claude-3")
        self.assertEqual(payload["system"], "sys")
        self.assertEqual(payload["messages"][0]["role"], "user")
        self.assertIn("diff", payload["messages"][0]["content"])
        self.assertIn("max_tokens", payload)

    def test_build_payload_openai_compatible(self):
        payload = _build_payload("diff", "gpt-4o", "sys", "openai")
        self.assertEqual(payload["model"], "gpt-4o")
        self.assertEqual(payload["messages"][0]["role"], "system")
        self.assertEqual(payload["messages"][0]["content"], "sys")


# ── review_code_with_model ──────────────────────────────────────────────


class TestReviewCodeWithModel(unittest.TestCase):
    @patch("urllib.request.urlopen")
    def test_review_openai_compatible(self, mock_urlopen):
        mock_urlopen.return_value = MockResponse({"choices": [{"message": {"content": "OK"}}]})
        content = review_code_with_model("diff", "sk-test", "gpt-4o", "sys", "openai")
        self.assertEqual(content, "OK")

    @patch("urllib.request.urlopen")
    def test_review_anthropic(self, mock_urlopen):
        mock_urlopen.return_value = MockResponse({"content": [{"text": "Looks good"}]})
        content = review_code_with_model("diff", "sk-test", "claude", "sys", "anthropic")
        self.assertEqual(content, "Looks good")

    @patch("urllib.request.urlopen")
    def test_strips_think_tags(self, mock_urlopen):
        mock_urlopen.return_value = MockResponse({
            "choices": [{"message": {"content": "<think>reasoning</think>Clean answer"}}]
        })
        content = review_code_with_model("diff", "sk-test", "deepseek", "sys", "openrouter")
        self.assertEqual(content, "Clean answer")

    @patch("urllib.request.urlopen")
    def test_only_think_tags_raises(self, mock_urlopen):
        mock_urlopen.return_value = MockResponse({
            "choices": [{"message": {"content": "<think>only reasoning</think>"}}]
        })
        with self.assertRaises(ValueError):
            review_code_with_model("diff", "sk-test", "deepseek", "sys", "openrouter")

    @patch("urllib.request.urlopen")
    def test_api_error_in_response_body(self, mock_urlopen):
        mock_urlopen.return_value = MockResponse({"error": "quota exceeded"})
        with self.assertRaises(Exception) as ctx:
            review_code_with_model("diff", "sk-test", "gpt-4o", "sys", "openai")
        self.assertIn("API Error", str(ctx.exception))

    @patch("urllib.request.urlopen")
    def test_http_error_raises_friendly_message(self, mock_urlopen):
        error_body = json.dumps({"error": {"message": ""}}).encode("utf-8")
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="https://api.openai.com/v1/chat/completions",
            code=401,
            msg="Unauthorized",
            hdrs={},
            fp=io.BytesIO(error_body),
        )
        with self.assertRaises(Exception) as ctx:
            review_code_with_model("diff", "sk-test", "gpt-4o", "sys", "openai")
        self.assertEqual(str(ctx.exception), "invalid API key")

    @patch("urllib.request.urlopen")
    def test_http_429_raises_rate_limited(self, mock_urlopen):
        error_body = json.dumps({}).encode("utf-8")
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="https://api.openai.com/v1/chat/completions",
            code=429,
            msg="Too Many Requests",
            hdrs={},
            fp=io.BytesIO(error_body),
        )
        with self.assertRaises(Exception) as ctx:
            review_code_with_model("diff", "sk-test", "gpt-4o", "sys", "openai")
        self.assertIn("rate limited", str(ctx.exception))

    @patch("urllib.request.urlopen")
    def test_no_truncation_in_review_code_with_model(self, mock_urlopen):
        """
        review_code_with_model no longer truncates diffs.
        Compression now happens in review_code before calling this function.
        """
        mock_urlopen.return_value = MockResponse({"choices": [{"message": {"content": "OK"}}]})
        long_diff = "x" * 20000
        content = review_code_with_model(long_diff, "sk-test", "gpt-4o", "sys", "openai")
        self.assertEqual(content, "OK")
        # Verify the full diff was sent (no truncation in this function)
        call_args = mock_urlopen.call_args
        sent_data = json.loads(call_args[0][0].data.decode("utf-8"))
        user_msg = sent_data["messages"][1]["content"]
        # Should NOT contain truncation message since that logic was removed
        self.assertNotIn("[... diff truncated", user_msg)
        # Should contain the full diff
        self.assertIn("x" * 100, user_msg)  # Check a portion of the original diff is present


# ── review_code (full integration with mocked HTTP) ────────────────────


class TestReviewCode(unittest.TestCase):
    def _base_config(self, provider="openrouter", model=None, fallback=True):
        config = {
            "project": {"name": "Test", "tech_stack": ["Python"]},
            "review": {"focus_areas": ["Security"]},
            "model": {"provider": provider, "fallback_enabled": fallback},
            "language": "en",
        }
        if model:
            config["model"]["preferred"] = model
        return config

    def test_empty_diff(self):
        result = review_code("   ", "sk-test", self._base_config())
        self.assertIn("No code changes", result)

    def test_invalid_provider(self):
        config = self._base_config()
        config["model"]["provider"] = "invalid_provider"
        result = review_code("diff content", "sk-test", config)
        self.assertIn("Invalid provider", result)

    @patch("iara.reviewer.review_code_with_model", return_value="LGTM")
    def test_success_with_preferred_model(self, mock_review):
        config = self._base_config(provider="openai", model="gpt-4o", fallback=False)
        result = review_code("diff content", "sk-test", config)
        self.assertEqual(result, "LGTM")
        mock_review.assert_called_once()

    @patch("iara.reviewer.time.sleep")
    @patch("iara.reviewer.review_code_with_model")
    def test_fallback_on_exception(self, mock_review, mock_sleep):
        mock_review.side_effect = [Exception("model failed"), "Fallback review"]
        config = self._base_config(provider="openrouter", model="bad-model")
        result = review_code("diff content", "sk-test", config)
        self.assertEqual(result, "Fallback review")
        self.assertEqual(mock_review.call_count, 2)

    @patch("iara.reviewer.time.sleep")
    @patch("iara.reviewer.review_code_with_model")
    def test_all_models_fail(self, mock_review, mock_sleep):
        mock_review.side_effect = Exception("fail")
        config = self._base_config(provider="openrouter")
        result = review_code("diff content", "sk-test", config)
        self.assertIn("Could not review", result)

    @patch("iara.reviewer.time.sleep")
    @patch("iara.reviewer.review_code_with_model")
    def test_http_error_triggers_fallback(self, mock_review, mock_sleep):
        mock_review.side_effect = [
            urllib.error.HTTPError("url", 429, "Too Many Requests", {}, io.BytesIO(b"")),
            "Success on retry",
        ]
        config = self._base_config(provider="openrouter", model="model-a")
        result = review_code("diff content", "sk-test", config)
        self.assertEqual(result, "Success on retry")

    @patch.dict("os.environ", {"IARA_MODEL": "forced-model"}, clear=False)
    @patch("iara.reviewer.review_code_with_model", return_value="Forced result")
    def test_env_model_overrides_config(self, mock_review):
        config = self._base_config(provider="openrouter", model="config-model")
        result = review_code("diff content", "sk-test", config)
        self.assertEqual(result, "Forced result")
        mock_review.assert_called_once()
        self.assertEqual(mock_review.call_args[0][2], "forced-model")

    @patch.dict("os.environ", {"IARA_MODEL": "forced-model"}, clear=False)
    @patch("iara.reviewer.time.sleep")
    @patch("iara.reviewer.review_code_with_model", side_effect=Exception("fail"))
    def test_env_model_breaks_on_failure(self, mock_review, mock_sleep):
        config = self._base_config(provider="openrouter", model="config-model")
        result = review_code("diff content", "sk-test", config)
        self.assertIn("Could not review", result)
        mock_review.assert_called_once()

    def test_no_model_configured_for_paid_provider(self):
        config = self._base_config(provider="openai", fallback=False)
        result = review_code("diff content", "sk-test", config)
        self.assertIn("No model configured", result)

    def test_reviewer_with_rag_enabled_but_no_context(self):
        """Test that reviewer works when RAG is enabled but returns no results."""
        config = {
            "model": {"provider": "openai", "preferred": "gpt-4o"},
            "memory": {"enabled": True}, 
            "review": {"ignore_patterns": []}
        }
        
        # Patch the functions in iara.reviewer, not class methods
        with patch('iara.reviewer.LanceDBMemory') as mock_memory_cls, \
             patch('iara.reviewer.Retriever') as mock_retriever_cls, \
             patch('iara.reviewer.review_code_with_model') as mock_review_func:
                 
            mock_memory = mock_memory_cls.return_value
            mock_retriever = mock_retriever_cls.return_value
            mock_retriever.retrieve_context_for_diff.return_value = "" # No context found
            
            mock_review_func.return_value = "LGTM"
            
            diff = "diff --git a/foo.py b/foo.py\n+print('hello')"
            
            # We need to ensure review_code can be imported/called.
            # It is imported at top of this file.
            result = review_code(diff, "fake-key", config)
            
            self.assertIn("LGTM", result)
            # Ensure retrieval was attempted
            mock_retriever.retrieve_context_for_diff.assert_called()


if __name__ == "__main__":
    unittest.main()
