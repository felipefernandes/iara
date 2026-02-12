
import unittest
from unittest.mock import MagicMock
from iara.memory.retriever import Retriever
from iara.memory.interface import CodeChunk

class TestRetriever(unittest.TestCase):
    def setUp(self):
        self.mock_memory = MagicMock()
        self.retriever = Retriever(self.mock_memory)

    def test_extract_symbols_from_diff_headers(self):
        diff = """
diff --git a/test.py b/test.py
index abc..def 100644
--- a/test.py
+++ b/test.py
@@ -10,5 +10,5 @@ def critical_function():
-    old_code()
+    new_code()
"""
        symbols = self.retriever._extract_symbols_from_diff(diff)
        self.assertIn("critical_function", symbols)

    def test_extract_symbols_from_added_lines(self):
        diff = """
@@ -20,1 +20,1 @@ def other():
+    result = calculate_tax(value)
"""
        symbols = self.retriever._extract_symbols_from_diff(diff)
        self.assertIn("calculate_tax", symbols)

    def test_retrieve_context_no_symbols(self):
        diff = "No symbols here"
        context = self.retriever.retrieve_context_for_diff(diff)
        self.assertEqual(context, "")
        self.mock_memory.retrieve.assert_not_called()

    def test_retrieve_context_with_symbols(self):
        diff = "@@ ... @@ def my_func():"
        
        # Mock retrieval response
        fake_chunk = CodeChunk(
            id="1", content="def my_func(): pass", 
            file_path="utils.py", start_line=1, end_line=1, 
            type="function", metadata={"name": "my_func"}
        )
        self.mock_memory.retrieve.return_value = [fake_chunk]

        context = self.retriever.retrieve_context_for_diff(diff)
        
        self.mock_memory.retrieve.assert_called_once()
        self.assertIn("def my_func(): pass", context)
        self.assertIn("Project Context", context)
