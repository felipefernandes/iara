"""Tests for false positive filtering."""

import unittest
from iara.filters import (
    filter_false_positives,
    is_false_positive,
    _extract_line_context,
    DEFAULT_FALSE_POSITIVE_PATTERNS,
)


class TestFalsePositiveFiltering(unittest.TestCase):
    """Test false positive pattern matching and filtering."""

    def test_github_actions_secrets_filtered(self):
        """Test that GitHub Actions secrets syntax is filtered."""
        comment = {
            "file": ".github/workflows/ci.yml",
            "line": 12,  # The added line (hunk starts at 10, so 10, 11, 12)
            "message": "🔒 Potential hardcoded secret detected",
            "severity": "security"
        }
        diff = """diff --git a/.github/workflows/ci.yml b/.github/workflows/ci.yml
index 1234567..abcdefg 100644
--- a/.github/workflows/ci.yml
+++ b/.github/workflows/ci.yml
@@ -10,3 +10,4 @@ jobs:
       - name: Test
         env:
+          API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
"""
        result = is_false_positive(comment, diff, DEFAULT_FALSE_POSITIVE_PATTERNS)
        self.assertTrue(result, "GitHub Actions secret syntax should be filtered")

    def test_hardcoded_secret_not_filtered(self):
        """Test that real hardcoded secrets are NOT filtered."""
        comment = {
            "file": "config.py",
            "line": 10,
            "message": "🔒 Hardcoded API key detected",
            "severity": "security"
        }
        diff = """diff --git a/config.py b/config.py
index 1234567..abcdefg 100644
--- a/config.py
+++ b/config.py
@@ -8,3 +8,4 @@
 # Configuration
+API_KEY = "sk-proj-abc123def456"
"""
        result = is_false_positive(comment, diff, DEFAULT_FALSE_POSITIVE_PATTERNS)
        self.assertFalse(result, "Real hardcoded secret should NOT be filtered")

    def test_security_chmod_filtered(self):
        """Test that security chmod is filtered when flagged as performance issue."""
        comment = {
            "file": "config.py",
            "line": 43,  # The chmod line after additions
            "message": "⚡ os.chmod() is inefficient for performance",
            "severity": "performance"
        }
        diff = """diff --git a/config.py b/config.py
index 1234567..abcdefg 100644
--- a/config.py
+++ b/config.py
@@ -40,4 +40,5 @@
 def save_config():
     with open(config_file, 'w') as f:
         f.write(data)
+    os.chmod(config_file, 0o600)  # Restrict to owner
"""
        result = is_false_positive(comment, diff, DEFAULT_FALSE_POSITIVE_PATTERNS)
        self.assertTrue(result, "Security chmod should be filtered")

    def test_chmod_without_restrictive_perms_not_filtered(self):
        """Test that chmod without restrictive permissions is NOT filtered."""
        comment = {
            "file": "setup.py",
            "line": 20,
            "message": "⚡ os.chmod() could be performance issue",
            "severity": "performance"
        }
        diff = """diff --git a/setup.py b/setup.py
index 1234567..abcdefg 100644
--- a/setup.py
+++ b/setup.py
@@ -18,3 +18,4 @@
 # Setup script
+os.chmod(some_file, 0o777)  # World writable
"""
        result = is_false_positive(comment, diff, DEFAULT_FALSE_POSITIVE_PATTERNS)
        self.assertFalse(result, "Chmod with 0o777 should NOT be filtered (not restrictive)")

    def test_missing_error_handling_without_try_except_not_filtered(self):
        """Test that missing error handling is NOT filtered when no try-except exists."""
        comment = {
            "file": "api.py",
            "line": 30,
            "message": "🐛 Missing error handling for API call",
            "severity": "bug"
        }
        diff = """diff --git a/api.py b/api.py
index 1234567..abcdefg 100644
--- a/api.py
+++ b/api.py
@@ -28,3 +28,5 @@
 def fetch_data():
+    response = requests.get(url)
+    return response.json()
"""
        result = is_false_positive(comment, diff, DEFAULT_FALSE_POSITIVE_PATTERNS)
        self.assertFalse(result, "Missing error handling should NOT be filtered when no try-except")

    def test_missing_error_handling_with_try_except_filtered(self):
        """Test that missing error handling IS filtered when try-except exists."""
        comment = {
            "file": "api.py",
            "line": 29,  # The added line (hunk starts at 27, added at position 29)
            "message": "🐛 Missing error handling for this operation",
            "severity": "bug"
        }
        diff = """diff --git a/api.py b/api.py
index 1234567..abcdefg 100644
--- a/api.py
+++ b/api.py
@@ -27,6 +27,7 @@
 def fetch_data():
     try:
+        response = requests.get(url)
         return response.json()
     except RequestException as e:
         logger.error(f"Failed: {e}")
"""
        result = is_false_positive(comment, diff, DEFAULT_FALSE_POSITIVE_PATTERNS)
        self.assertTrue(result, "Missing error handling should be filtered when try-except exists")

    def test_small_scale_performance_filtered(self):
        """Test that small-scale performance suggestions are filtered."""
        comment = {
            "file": "utils.py",
            "line": 15,  # The for loop line
            "message": "⚡ Consider using set for O(1) lookup performance",
            "severity": "performance"
        }
        diff = """diff --git a/utils.py b/utils.py
index 1234567..abcdefg 100644
--- a/utils.py
+++ b/utils.py
@@ -13,3 +13,4 @@
 def process_users():
+    for user in users[:5]:  # Process first 5 users
         send_notification(user)
"""
        result = is_false_positive(comment, diff, DEFAULT_FALSE_POSITIVE_PATTERNS)
        self.assertTrue(result, "Small-scale performance suggestion should be filtered")

    def test_large_scale_performance_not_filtered(self):
        """Test that large-scale performance suggestions are NOT filtered."""
        comment = {
            "file": "analytics.py",
            "line": 20,
            "message": "⚡ Consider using set for O(1) lookup performance",
            "severity": "performance"
        }
        diff = """diff --git a/analytics.py b/analytics.py
index 1234567..abcdefg 100644
--- a/analytics.py
+++ b/analytics.py
@@ -18,3 +18,5 @@
 def analyze():
+    for item in large_dataset:  # Process 10000+ items
+        if item.id in processed_ids:
             continue
"""
        result = is_false_positive(comment, diff, DEFAULT_FALSE_POSITIVE_PATTERNS)
        self.assertFalse(result, "Large-scale performance suggestion should NOT be filtered")

    def test_real_bug_not_filtered(self):
        """Test that real bugs are NOT filtered."""
        comment = {
            "file": "calculator.py",
            "line": 10,
            "message": "🐛 Division by zero possible",
            "severity": "bug"
        }
        diff = """diff --git a/calculator.py b/calculator.py
index 1234567..abcdefg 100644
--- a/calculator.py
+++ b/calculator.py
@@ -8,3 +8,4 @@
 def divide(a, b):
+    return a / b  # No zero check
"""
        result = is_false_positive(comment, diff, DEFAULT_FALSE_POSITIVE_PATTERNS)
        self.assertFalse(result, "Real division by zero bug should NOT be filtered")

    def test_sql_injection_not_filtered(self):
        """Test that SQL injection vulnerabilities are NOT filtered."""
        comment = {
            "file": "database.py",
            "line": 25,
            "message": "🔒 SQL injection vulnerability detected",
            "severity": "security"
        }
        diff = """diff --git a/database.py b/database.py
index 1234567..abcdefg 100644
--- a/database.py
+++ b/database.py
@@ -23,3 +23,5 @@
 def get_user(username):
+    query = f"SELECT * FROM users WHERE name = '{username}'"
+    return db.execute(query)
"""
        result = is_false_positive(comment, diff, DEFAULT_FALSE_POSITIVE_PATTERNS)
        self.assertFalse(result, "SQL injection should NOT be filtered")


class TestContextExtraction(unittest.TestCase):
    """Test context extraction from diffs."""

    def test_extract_context_simple_diff(self):
        """Test extracting context from a simple diff."""
        diff = """diff --git a/test.py b/test.py
index 1234567..abcdefg 100644
--- a/test.py
+++ b/test.py
@@ -10,5 +10,6 @@ def foo():
     line1 = "before"
     line2 = "target"
     line3 = "after"
+    line4 = "new line"
"""
        context = _extract_line_context(diff, "test.py", 13, context_lines=2)
        self.assertIn("line2", context)
        self.assertIn("line3", context)
        self.assertIn("line4", context)

    def test_extract_context_file_not_in_diff(self):
        """Test context extraction when file is not in diff."""
        diff = """diff --git a/other.py b/other.py
index 1234567..abcdefg 100644
--- a/other.py
+++ b/other.py
@@ -1,3 +1,4 @@
 line1
+line2
"""
        context = _extract_line_context(diff, "test.py", 10, context_lines=3)
        self.assertEqual(context, "", "Should return empty string for file not in diff")

    def test_extract_context_with_multiple_hunks(self):
        """Test context extraction from diff with multiple hunks."""
        diff = """diff --git a/multi.py b/multi.py
index 1234567..abcdefg 100644
--- a/multi.py
+++ b/multi.py
@@ -5,3 +5,4 @@ def first():
     pass
+    new_line1
@@ -20,3 +21,4 @@ def second():
     target_line = "here"
+    new_line2
"""
        context = _extract_line_context(diff, "multi.py", 22, context_lines=1)
        self.assertIn("target_line", context)
        self.assertIn("new_line2", context)


class TestFilterFalsePositives(unittest.TestCase):
    """Test the main filter_false_positives function."""

    def test_filter_multiple_comments(self):
        """Test filtering a list of comments."""
        comments = [
            {
                "file": ".github/workflows/ci.yml",
                "line": 12,  # Hunk 10+2 = line 12
                "message": "🔒 Hardcoded secret detected",
                "severity": "security"
            },
            {
                "file": "calculator.py",
                "line": 8,  # Hunk 7+1 = line 8
                "message": "🐛 Division by zero possible",
                "severity": "bug"
            },
            {
                "file": "config.py",
                "line": 40,  # Hunk 39+1 = line 40
                "message": "⚡ os.chmod() is inefficient",
                "severity": "performance"
            }
        ]
        diff = """diff --git a/.github/workflows/ci.yml b/.github/workflows/ci.yml
+++ b/.github/workflows/ci.yml
@@ -10,3 +10,4 @@
       - name: Test
         env:
+          API_KEY: ${{ secrets.KEY }}

diff --git a/calculator.py b/calculator.py
+++ b/calculator.py
@@ -7,3 +7,4 @@
 def divide(a, b):
+    return a / b

diff --git a/config.py b/config.py
+++ b/config.py
@@ -39,3 +39,4 @@
 def save():
+    os.chmod(file, 0o600)
"""
        filtered = filter_false_positives(comments, diff)
        # Should filter GitHub Actions secret and chmod, keep division by zero
        self.assertEqual(len(filtered), 1, "Should keep only the real bug")
        self.assertEqual(filtered[0]["file"], "calculator.py")

    def test_filter_with_custom_patterns(self):
        """Test filtering with custom patterns."""
        comments = [
            {
                "file": "settings.py",
                "line": 10,
                "message": "🧹 Global variable detected",
                "severity": "style"
            }
        ]
        diff = """diff --git a/settings.py b/settings.py
+++ b/settings.py
@@ -8,3 +8,4 @@
+DEBUG = True
"""
        custom_patterns = [
            {
                "name": "django-settings-globals",
                "file_pattern": r"settings\.py$",
                "message_pattern": r"global.*variable",
                "reason": "Django settings.py uses globals"
            }
        ]
        filtered = filter_false_positives(comments, diff, custom_patterns)
        self.assertEqual(len(filtered), 0, "Custom pattern should filter the comment")

    def test_filter_no_matches(self):
        """Test that all comments pass through when no patterns match."""
        comments = [
            {
                "file": "test.py",
                "line": 10,
                "message": "🐛 Actual bug here",
                "severity": "bug"
            }
        ]
        diff = """diff --git a/test.py b/test.py
+++ b/test.py
@@ -8,3 +8,4 @@
+    bug_line()
"""
        filtered = filter_false_positives(comments, diff)
        self.assertEqual(len(filtered), 1, "Should keep all comments when no patterns match")


if __name__ == "__main__":
    unittest.main()
