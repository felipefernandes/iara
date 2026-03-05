import unittest
from unittest.mock import Mock, patch
import requests
from iara.platforms.github import GitHubAdapter


class TestGitHubAdapter(unittest.TestCase):
    def setUp(self):
        self.adapter = GitHubAdapter(
            token="test_token",
            repo="owner/repo",
            pr_id="123"
        )

    def test_initialization(self):
        """Test adapter initialization."""
        self.assertEqual(self.adapter.token, "test_token")
        self.assertEqual(self.adapter.repo, "owner/repo")
        self.assertEqual(self.adapter.pr_id, "123")
        self.assertEqual(self.adapter.base_url, "https://api.github.com")

    @patch('iara.platforms.github.requests.post')
    def test_post_inline_comments_success(self, mock_post):
        """Test successful inline comments posting."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_post.return_value = mock_response

        comments = [
            {
                "file": "test.py",
                "line": 10,
                "severity": "bug",
                "message": "🐛 Logic error"
            }
        ]

        result = self.adapter.post_inline_comments("abc123", comments)

        self.assertTrue(result)
        mock_post.assert_called_once()

        # Verify payload structure
        call_kwargs = mock_post.call_args[1]
        payload = call_kwargs['json']
        self.assertEqual(payload["commit_id"], "abc123")
        self.assertEqual(payload["event"], "COMMENT")
        self.assertEqual(len(payload["comments"]), 1)
        self.assertEqual(payload["comments"][0]["path"], "test.py")
        self.assertEqual(payload["comments"][0]["line"], 10)
        self.assertEqual(payload["comments"][0]["body"], "🐛 Logic error")

    @patch('iara.platforms.github.requests.post')
    def test_post_inline_comments_api_error(self, mock_post):
        """Test inline comments posting with API error."""
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.text = "Forbidden"
        mock_post.return_value = mock_response

        comments = [
            {
                "file": "test.py",
                "line": 10,
                "severity": "bug",
                "message": "Test"
            }
        ]

        result = self.adapter.post_inline_comments("abc123", comments)

        self.assertFalse(result)

    @patch('iara.platforms.github.requests.post')
    def test_post_inline_comments_empty_list(self, mock_post):
        """Test posting empty comments list."""
        result = self.adapter.post_inline_comments("abc123", [])

        self.assertTrue(result)
        mock_post.assert_not_called()

    @patch('iara.platforms.github.requests.post')
    def test_post_inline_comments_network_error(self, mock_post):
        """Test inline comments posting with network error."""
        mock_post.side_effect = requests.exceptions.RequestException("Network error")

        comments = [
            {
                "file": "test.py",
                "line": 10,
                "severity": "bug",
                "message": "Test"
            }
        ]

        result = self.adapter.post_inline_comments("abc123", comments)

        self.assertFalse(result)

    @patch('iara.platforms.github.requests.post')
    def test_post_summary_comment_success(self, mock_post):
        """Test successful summary comment posting."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_post.return_value = mock_response

        result = self.adapter.post_summary_comment("Test review")

        self.assertTrue(result)
        mock_post.assert_called_once()

        # Verify payload
        call_kwargs = mock_post.call_args[1]
        payload = call_kwargs['json']
        self.assertIn("body", payload)
        self.assertIn("Test review", payload["body"])
        self.assertIn("Iara Code Review", payload["body"])

    @patch('iara.platforms.github.requests.post')
    def test_post_summary_comment_api_error(self, mock_post):
        """Test summary comment posting with API error."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response

        result = self.adapter.post_summary_comment("Test review")

        self.assertFalse(result)

    @patch('iara.platforms.github.requests.post')
    def test_post_multiple_inline_comments(self, mock_post):
        """Test posting multiple inline comments."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_post.return_value = mock_response

        comments = [
            {"file": "file1.py", "line": 10, "severity": "bug", "message": "Bug 1"},
            {"file": "file2.py", "line": 20, "severity": "security", "message": "Security 1"},
            {"file": "file3.py", "line": 30, "severity": "performance", "message": "Perf 1"}
        ]

        result = self.adapter.post_inline_comments("abc123", comments)

        self.assertTrue(result)

        # Verify all comments are included
        call_kwargs = mock_post.call_args[1]
        payload = call_kwargs['json']
        self.assertEqual(len(payload["comments"]), 3)


if __name__ == '__main__':
    unittest.main()
