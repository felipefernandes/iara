import unittest
import json
from unittest.mock import patch

from iara.reviewer import _build_payload, _extract_content, review_code_with_model


class MockResponse:
    def __init__(self, payload):
        self.payload = payload

    def read(self):
        return json.dumps(self.payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


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


class TestExtractContent(unittest.TestCase):
    def test_extract_content_anthropic(self):
        result = {"content": [{"text": "Hello"}]}
        self.assertEqual(_extract_content(result, "anthropic"), "Hello")

    def test_extract_content_openai(self):
        result = {"choices": [{"message": {"content": "Hi"}}]}
        self.assertEqual(_extract_content(result, "openai"), "Hi")


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


if __name__ == "__main__":
    unittest.main()
