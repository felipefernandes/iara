import unittest
import json
from iara.parsers.inline_parser import parse_inline_review


class TestInlineParser(unittest.TestCase):
    def test_parse_valid_json(self):
        """Test parsing valid inline review JSON."""
        json_text = json.dumps({
            "summary": "Found 2 issues",
            "comments": [
                {
                    "file": "test.py",
                    "line": 10,
                    "severity": "bug",
                    "message": "🐛 Logic error"
                },
                {
                    "file": "main.py",
                    "line": 42,
                    "severity": "security",
                    "message": "🔒 SQL injection risk"
                }
            ]
        })

        result = parse_inline_review(json_text)
        self.assertEqual(result["summary"], "Found 2 issues")
        self.assertEqual(len(result["comments"]), 2)
        self.assertEqual(result["comments"][0]["file"], "test.py")
        self.assertEqual(result["comments"][0]["line"], 10)
        self.assertEqual(result["comments"][0]["severity"], "bug")

    def test_parse_empty_comments(self):
        """Test parsing JSON with empty comments array."""
        json_text = json.dumps({
            "summary": "No issues found",
            "comments": []
        })

        result = parse_inline_review(json_text)
        self.assertEqual(result["summary"], "No issues found")
        self.assertEqual(len(result["comments"]), 0)

    def test_parse_invalid_json(self):
        """Test that invalid JSON raises ValueError."""
        invalid_json = "{ not valid json"

        with self.assertRaises(ValueError) as cm:
            parse_inline_review(invalid_json)
        self.assertIn("Invalid JSON", str(cm.exception))

    def test_parse_missing_summary(self):
        """Test that missing 'summary' field raises ValueError."""
        json_text = json.dumps({
            "comments": []
        })

        with self.assertRaises(ValueError) as cm:
            parse_inline_review(json_text)
        self.assertIn("Missing required field: 'summary'", str(cm.exception))

    def test_parse_missing_comments(self):
        """Test that missing 'comments' field raises ValueError."""
        json_text = json.dumps({
            "summary": "Test"
        })

        with self.assertRaises(ValueError) as cm:
            parse_inline_review(json_text)
        self.assertIn("Missing required field: 'comments'", str(cm.exception))

    def test_parse_comments_not_array(self):
        """Test that non-array comments field raises ValueError."""
        json_text = json.dumps({
            "summary": "Test",
            "comments": "not an array"
        })

        with self.assertRaises(ValueError) as cm:
            parse_inline_review(json_text)
        self.assertIn("'comments' must be array", str(cm.exception))

    def test_parse_comment_missing_file(self):
        """Test that comment without 'file' field raises ValueError."""
        json_text = json.dumps({
            "summary": "Test",
            "comments": [
                {
                    "line": 10,
                    "severity": "bug",
                    "message": "Test"
                }
            ]
        })

        with self.assertRaises(ValueError) as cm:
            parse_inline_review(json_text)
        self.assertIn("missing required field: 'file'", str(cm.exception))

    def test_parse_comment_missing_line(self):
        """Test that comment without 'line' field raises ValueError."""
        json_text = json.dumps({
            "summary": "Test",
            "comments": [
                {
                    "file": "test.py",
                    "severity": "bug",
                    "message": "Test"
                }
            ]
        })

        with self.assertRaises(ValueError) as cm:
            parse_inline_review(json_text)
        self.assertIn("missing required field: 'line'", str(cm.exception))

    def test_parse_comment_invalid_line_type(self):
        """Test that non-integer line number raises ValueError."""
        json_text = json.dumps({
            "summary": "Test",
            "comments": [
                {
                    "file": "test.py",
                    "line": "10",
                    "severity": "bug",
                    "message": "Test"
                }
            ]
        })

        with self.assertRaises(ValueError) as cm:
            parse_inline_review(json_text)
        self.assertIn("'line' must be integer", str(cm.exception))

    def test_parse_comment_invalid_severity(self):
        """Test that invalid severity value raises ValueError."""
        json_text = json.dumps({
            "summary": "Test",
            "comments": [
                {
                    "file": "test.py",
                    "line": 10,
                    "severity": "invalid",
                    "message": "Test"
                }
            ]
        })

        with self.assertRaises(ValueError) as cm:
            parse_inline_review(json_text)
        self.assertIn("invalid severity", str(cm.exception))

    def test_parse_comment_negative_line(self):
        """Test that negative line number raises ValueError."""
        json_text = json.dumps({
            "summary": "Test",
            "comments": [
                {
                    "file": "test.py",
                    "line": -1,
                    "severity": "bug",
                    "message": "Test"
                }
            ]
        })

        with self.assertRaises(ValueError) as cm:
            parse_inline_review(json_text)
        self.assertIn("line number must be positive", str(cm.exception))

    def test_parse_all_severities(self):
        """Test parsing all valid severity types."""
        json_text = json.dumps({
            "summary": "Test all severities",
            "comments": [
                {"file": "test.py", "line": 1, "severity": "bug", "message": "Bug"},
                {"file": "test.py", "line": 2, "severity": "security", "message": "Security"},
                {"file": "test.py", "line": 3, "severity": "performance", "message": "Performance"},
                {"file": "test.py", "line": 4, "severity": "style", "message": "Style"},
                {"file": "test.py", "line": 5, "severity": "other", "message": "Other"}
            ]
        })

        result = parse_inline_review(json_text)
        self.assertEqual(len(result["comments"]), 5)
        severities = [c["severity"] for c in result["comments"]]
        self.assertEqual(severities, ["bug", "security", "performance", "style", "other"])


if __name__ == '__main__':
    unittest.main()
