
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

    def test_deduplicate_chunks_fallback_no_encoder(self):
        chunks = [CodeChunk(id=f"{i}", content=f"content {i}", file_path="f.py", start_line=1, end_line=1, type="function", metadata={}) for i in range(3)]
        self.mock_memory.encoder = None
        
        kept = self.retriever._deduplicate_chunks(chunks)
        self.assertEqual(len(kept), 3)

    def test_deduplicate_chunks_with_encoder(self):
        chunks = [
            CodeChunk(id="1", content="def a(): pass", file_path="f.py", start_line=1, end_line=1, type="function", metadata={}),
            CodeChunk(id="2", content="def a(): pass", file_path="f.py", start_line=1, end_line=1, type="function", metadata={}),
            CodeChunk(id="3", content="def b(): print('hi')", file_path="f.py", start_line=1, end_line=1, type="function", metadata={})
        ]
        
        # Mock an encoder that assigns identical vectors to identical content and different otherwise.
        mock_encoder = MagicMock()
        def mock_encode(contents):
            vecs = []
            for c in contents:
                if c == "def a(): pass":
                    vecs.append([1.0, 0.0])
                else:
                    vecs.append([0.0, 1.0])
            return vecs
        mock_encoder.encode.side_effect = mock_encode
        self.mock_memory.encoder = mock_encoder

        kept = self.retriever._deduplicate_chunks(chunks, similarity_threshold=0.92)
        
        # Expecting chunks 1 and 3
        self.assertEqual(len(kept), 2)
        self.assertEqual(kept[0].id, "1")
        self.assertEqual(kept[1].id, "3")

    def test_cosine_similarity(self):
        from iara.memory.retriever import _cosine_similarity
        
        sim1 = _cosine_similarity([1.0, 0.0], [1.0, 0.0])
        self.assertAlmostEqual(sim1, 1.0)
        
        sim2 = _cosine_similarity([1.0, 0.0], [0.0, 1.0])
        self.assertAlmostEqual(sim2, 0.0)
        
        sim3 = _cosine_similarity([1.0, 1.0], [2.0, 2.0])
        self.assertAlmostEqual(sim3, 1.0)
        
        sim4 = _cosine_similarity([], [1.0])
        self.assertEqual(sim4, 0.0)

    @unittest.mock.patch('iara.memory.retriever.load_config')
    def test_get_dedup_threshold_failure(self, mock_load_config):
        mock_load_config.side_effect = Exception("Config error")
        threshold = self.retriever._get_dedup_threshold()
        self.assertEqual(threshold, 0.92)

    def test_deduplicate_chunks_encoding_exception(self):
        chunks = [CodeChunk(id=f"{i}", content=f"content {i}", file_path="f.py", start_line=1, end_line=1, type="function", metadata={}) for i in range(2)]
        mock_encoder = MagicMock()
        mock_encoder.encode.side_effect = Exception("Encoding error")
        self.mock_memory.encoder = mock_encoder
        
        kept = self.retriever._deduplicate_chunks(chunks)
        # Should return all chunks on failure
        self.assertEqual(len(kept), 2)
