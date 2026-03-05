import unittest
import sys
from io import StringIO

from iara.diff_compressor import DiffCompressor


class TestDiffCompressor(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.compressor = DiffCompressor(max_diff_tokens=500)

    def test_init_with_invalid_type(self):
        """Test that initializing with invalid type raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            DiffCompressor(max_diff_tokens="not_a_number")
        self.assertIn("must be a positive integer", str(ctx.exception))

    def test_init_with_negative_value(self):
        """Test that initializing with negative value raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            DiffCompressor(max_diff_tokens=-100)
        self.assertIn("must be positive", str(ctx.exception))

    def test_init_with_zero(self):
        """Test that initializing with zero raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            DiffCompressor(max_diff_tokens=0)
        self.assertIn("must be positive", str(ctx.exception))

    def test_init_with_string_number(self):
        """Test that string numbers are converted to int."""
        compressor = DiffCompressor(max_diff_tokens="5000")
        self.assertEqual(compressor.max_diff_tokens, 5000)

    def test_small_diff_untouched(self):
        """Test that small diffs are returned unchanged."""
        small_diff = """diff --git a/file.py b/file.py
--- a/file.py
+++ b/file.py
@@ -1,3 +1,3 @@
 def hello():
-    print("old")
+    print("new")
"""
        result = self.compressor.compress(small_diff)
        self.assertEqual(result, small_diff)

    def test_large_diff_compression(self):
        """Test that large diffs get compressed by removing context lines."""
        # Create a large diff with many context lines
        large_diff = "diff --git a/large_file.py b/large_file.py\n"
        large_diff += "--- a/large_file.py\n"
        large_diff += "+++ b/large_file.py\n"
        large_diff += "@@ -1,100 +1,100 @@\n"

        # Add 50 context lines
        for i in range(50):
            large_diff += f" context line {i}\n"

        # Add some changes
        large_diff += "-old line 1\n"
        large_diff += "+new line 1\n"

        # Add more context lines
        for i in range(50, 100):
            large_diff += f" context line {i}\n"

        # Add more changes
        large_diff += "-old line 2\n"
        large_diff += "+new line 2\n"

        result = self.compressor.compress(large_diff)

        # Result should be smaller than original
        self.assertLess(len(result), len(large_diff))

        # But should still contain the important parts
        self.assertIn("diff --git a/large_file.py b/large_file.py", result)
        self.assertIn("--- a/large_file.py", result)
        self.assertIn("+++ b/large_file.py", result)
        self.assertIn("@@", result)
        self.assertIn("+new line 1", result)
        self.assertIn("-old line 1", result)
        self.assertIn("+new line 2", result)
        self.assertIn("-old line 2", result)

        # Context lines should be removed
        self.assertNotIn("context line 0", result)

    def test_multiple_files_preserved(self):
        """Test that all file headers are preserved even when compressing."""
        multi_file_diff = """diff --git a/file1.py b/file1.py
--- a/file1.py
+++ b/file1.py
@@ -1,2 +1,2 @@
-old content 1
+new content 1
diff --git a/file2.py b/file2.py
--- a/file2.py
+++ b/file2.py
@@ -1,2 +1,2 @@
-old content 2
+new content 2
diff --git a/file3.py b/file3.py
--- a/file3.py
+++ b/file3.py
@@ -1,2 +1,2 @@
-old content 3
+new content 3
"""
        result = self.compressor.compress(multi_file_diff)

        # All file headers should be present
        self.assertIn("diff --git a/file1.py b/file1.py", result)
        self.assertIn("diff --git a/file2.py b/file2.py", result)
        self.assertIn("diff --git a/file3.py b/file3.py", result)

        # All changes should be present
        self.assertIn("+new content 1", result)
        self.assertIn("+new content 2", result)
        self.assertIn("+new content 3", result)

    def test_compression_logging(self):
        """Test that compression logs statistics to stderr."""
        # Create a diff that will trigger compression
        large_diff = "diff --git a/file.py b/file.py\n"
        large_diff += "--- a/file.py\n"
        large_diff += "+++ b/file.py\n"
        large_diff += "@@ -1,200 +1,200 @@\n"

        for i in range(200):
            large_diff += f" context line {i}\n"

        large_diff += "-old\n+new\n"

        # Capture stderr
        captured_output = StringIO()
        sys.stderr = captured_output

        self.compressor.compress(large_diff)

        sys.stderr = sys.__stderr__

        output = captured_output.getvalue()

        # Check for compression log message
        self.assertIn("🗜️", output)
        self.assertIn("Diff compressed:", output)
        self.assertIn("KB", output)
        self.assertIn("reduction", output)

    def test_preserves_added_lines(self):
        """Test that all added lines are preserved."""
        diff = """diff --git a/test.py b/test.py
--- a/test.py
+++ b/test.py
@@ -1,5 +1,7 @@
 context line 1
 context line 2
+added line 1
 context line 3
+added line 2
 context line 4
 context line 5
"""
        result = self.compressor.compress(diff)

        self.assertIn("+added line 1", result)
        self.assertIn("+added line 2", result)

    def test_preserves_removed_lines(self):
        """Test that all removed lines are preserved."""
        diff = """diff --git a/test.py b/test.py
--- a/test.py
+++ b/test.py
@@ -1,7 +1,5 @@
 context line 1
-removed line 1
 context line 2
 context line 3
-removed line 2
 context line 4
 context line 5
"""
        result = self.compressor.compress(diff)

        self.assertIn("-removed line 1", result)
        self.assertIn("-removed line 2", result)

    def test_format_size(self):
        """Test the size formatting helper."""
        self.assertEqual(self.compressor._format_size(1024), "1.0KB")
        self.assertEqual(self.compressor._format_size(2048), "2.0KB")
        self.assertEqual(self.compressor._format_size(1536), "1.5KB")
        self.assertEqual(self.compressor._format_size(30720), "30.0KB")

    def test_empty_diff(self):
        """Test handling of empty diff."""
        result = self.compressor.compress("")
        self.assertEqual(result, "")

    def test_parse_diff_files(self):
        """Test the diff file parsing logic."""
        diff = """diff --git a/file1.py b/file1.py
--- a/file1.py
+++ b/file1.py
@@ -1,1 +1,1 @@
-old
+new
diff --git a/file2.py b/file2.py
--- a/file2.py
+++ b/file2.py
@@ -1,1 +1,1 @@
-old2
+new2
"""
        files = self.compressor._parse_diff_files(diff)

        # Should have 2 files
        self.assertEqual(len(files), 2)

        # Each file should be a tuple of (header, content)
        self.assertEqual(files[0][0], "diff --git a/file1.py b/file1.py")
        self.assertIn("--- a/file1.py", files[0][1])

        self.assertEqual(files[1][0], "diff --git a/file2.py b/file2.py")
        self.assertIn("--- a/file2.py", files[1][1])

    def test_extremely_large_diff_truncation(self):
        """Test that extremely large diffs are truncated with a warning."""
        # Create a compressor with a very small limit
        tiny_compressor = DiffCompressor(max_diff_tokens=100)

        # Create a diff that will exceed the limit even after compression
        huge_diff = "diff --git a/huge.py b/huge.py\n"
        huge_diff += "--- a/huge.py\n"
        huge_diff += "+++ b/huge.py\n"
        huge_diff += "@@ -1,500 +1,500 @@\n"

        for i in range(500):
            huge_diff += f"+added line {i}\n"

        result = tiny_compressor.compress(huge_diff)

        # Should be truncated
        self.assertLessEqual(len(result), 150)  # Allow some buffer
        self.assertIn("[... diff still too large, truncated ...]", result)

    def test_parse_diff_with_no_trailing_newline(self):
        """Test parsing diff that doesn't end with newline."""
        diff_no_newline = "diff --git a/file.py b/file.py\n--- a/file.py\n+++ b/file.py\n+new line"
        files = self.compressor._parse_diff_files(diff_no_newline)

        self.assertEqual(len(files), 1)
        self.assertEqual(files[0][0], "diff --git a/file.py b/file.py")
        self.assertIn("+new line", files[0][1])

    def test_parse_empty_diff(self):
        """Test parsing an empty diff string."""
        files = self.compressor._parse_diff_files("")
        self.assertEqual(len(files), 0)

    def test_parse_diff_with_no_markers(self):
        """Test parsing a string with no diff markers."""
        no_markers = "This is not a diff\nJust random text"
        files = self.compressor._parse_diff_files(no_markers)
        self.assertEqual(len(files), 0)


if __name__ == '__main__':
    unittest.main()
