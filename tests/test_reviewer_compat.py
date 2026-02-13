import unittest
import warnings
from unittest.mock import patch, MagicMock
from iara.reviewer import Reviewer

class TestReviewerCompatibility(unittest.TestCase):
    def test_reviewer_deprecation_warning(self):
        """Test that instantiating Reviewer emits a DeprecationWarning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            Reviewer()
            self.assertTrue(len(w) > 0)
            self.assertTrue(issubclass(w[-1].category, DeprecationWarning))
            self.assertIn("deprecated", str(w[-1].message))

    @patch("iara.reviewer.review_code")
    def test_review_method_delegation(self, mock_review_code):
        """Test that Reviewer.review delegates to review_code."""
        mock_review_code.return_value = "Mock Review"
        
        reviewer = Reviewer(api_key="test-key", config={"model": {"provider": "openai"}})
        result = reviewer.review("diff content")
        
        mock_review_code.assert_called_once()
        args, _ = mock_review_code.call_args
        self.assertEqual(args[0], "diff content")
        self.assertEqual(args[1], "test-key")
        self.assertEqual(reviewer.config, args[2])
        self.assertEqual(result, "Mock Review")

if __name__ == "__main__":
    unittest.main()
