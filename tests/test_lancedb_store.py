
import unittest
import shutil
import tempfile
import os
from unittest.mock import MagicMock, patch
from iara.memory.interface import CodeChunk

# We mock lancedb/sentence_transformers to avoid heavy dependencies in unit tests
# Integration tests would use real DB
class TestLanceDBMemory(unittest.TestCase):
    

    def setUp(self):
        # Patch modules before they are imported
        self.mock_lancedb = MagicMock()
        self.mock_sent_trans = MagicMock()
        
        self.patcher = patch.dict('sys.modules', {
            'lancedb': self.mock_lancedb,
            'sentence_transformers': self.mock_sent_trans
        })
        self.patcher.start()
        
        # Setup common mocks
        self.mock_sent_trans.SentenceTransformer.return_value.encode.return_value.tolist.return_value = [[0.1, 0.2]]
        self.mock_lancedb.connect.return_value.table_names.return_value = []

    def tearDown(self):
        self.patcher.stop()

    def test_initialization(self):
        from iara.memory.lancedb_store import LanceDBMemory
        memory = LanceDBMemory()
        # Should NOT be called on init
        self.mock_lancedb.connect.assert_not_called()
        
        # Should be called after access
        memory._ensure_initialized()
        self.mock_lancedb.connect.assert_called_once()

    def test_index_chunks(self):
        from iara.memory.lancedb_store import LanceDBMemory
        from iara.memory.interface import CodeChunk

        memory = LanceDBMemory()
        memory._ensure_initialized() # Initialize DB
        
        # Mock create_table
        memory.db.create_table.return_value = MagicMock()
        
        chunk = CodeChunk(
            id="test:1", content="print('hello')", 
            file_path="test.py", start_line=1, end_line=1, 
            type="function", metadata={}
        )
        
        memory.index_chunks([chunk])
        memory.db.create_table.assert_called()

    def test_retrieve(self):
        from iara.memory.lancedb_store import LanceDBMemory
        
        memory = LanceDBMemory()
        memory._ensure_initialized()
        
        memory.db.table_names.return_value = ["code_chunks"]
        
        mock_table = MagicMock()
        memory.db.open_table.return_value = mock_table
        
        # Mock search result
        mock_result = MagicMock()
        mock_result.to_pandas.return_value.to_dict.return_value = [{
            "id": "test:1",
            "text": "def found(): pass",
            "metadata": {"name": "found"},
            "file_path": "found.py",
            "start_line": 10,
            "end_line": 12,
            "type": "function",
            "content": "def found(): pass" 
        }]
        mock_table.search.return_value.limit.return_value.to_list.return_value = [{
            "id": "test:1",
            "content": "def found(): pass",
            "metadata": {"name": "found"},
            "file_path": "found.py",
            "start_line": 10,
            "end_line": 12,
            "type": "function",
            "content": "def found(): pass", 
            "start_line": 10, # Add missing fields to match CodeChunk expected structure if mocked fully or partially
            "end_line": 12,
            "type": "function"
        }] 

        results = memory.retrieve("query")
        # Ensure we handled the result correctly
        self.assertEqual(len(results), 1)

    def test_import_error(self):
        """Test that LanceDBMemory raises ImportError if dependencies are missing."""
        # Using a fresh import context to simulate missing module
        with patch.dict('sys.modules', {'lancedb': None}):
             from iara.memory.lancedb_store import LanceDBMemory
             memory = LanceDBMemory()
             # Should fail on initialization access, not on creation
             with self.assertRaises(ImportError):
                 memory._ensure_initialized()

    def test_create_new_table(self):
        """Test logic for creating a new table when one doesn't exist."""
        from iara.memory.lancedb_store import LanceDBMemory
        from iara.memory.interface import CodeChunk

        memory = LanceDBMemory()
        memory._ensure_initialized()
        
        memory.db = MagicMock()
        memory.db.table_names.return_value = [] # No tables
        memory._embed = MagicMock(return_value=[[0.1, 0.2]])
        
        chunk = CodeChunk(id="1", content="code", file_path="f", start_line=1, end_line=1, type="text")
        memory.index_chunks([chunk])
        
        memory.db.create_table.assert_called_once()

    def test_append_existing_table(self):
        """Test logic for appending to an existing table."""
        from iara.memory.lancedb_store import LanceDBMemory
        from iara.memory.interface import CodeChunk

        memory = LanceDBMemory()
        memory._ensure_initialized()
        
        memory.db = MagicMock()
        memory.db.table_names.return_value = ["code_chunks"] 
        memory.db.open_table.return_value = MagicMock()
        memory._embed = MagicMock(return_value=[[0.1, 0.2]])
        
        chunk = CodeChunk(id="1", content="code", file_path="f", start_line=1, end_line=1, type="text")
        memory.index_chunks([chunk])
        
        memory.db.create_table.assert_not_called()
        memory.db.open_table.assert_called_with("code_chunks")

    def test_delete_by_file_paths_empty_list(self):
        """Deleting empty list should be a no-op."""
        from iara.memory.lancedb_store import LanceDBMemory

        memory = LanceDBMemory()
        memory._ensure_initialized()

        # Should not raise, no DB calls made
        memory.delete_by_file_paths([])

    def test_delete_by_file_paths_predicate_format(self):
        """Should construct correct SQL predicate."""
        from iara.memory.lancedb_store import LanceDBMemory

        memory = LanceDBMemory()
        memory._ensure_initialized()
        memory.db = MagicMock()
        memory.db.table_names.return_value = ["code_chunks"]
        mock_table = MagicMock()
        memory.db.open_table.return_value = mock_table
        mock_table.delete.return_value = 5

        memory.delete_by_file_paths(["path1.py", "path2.py"])

        mock_table.delete.assert_called_once()
        predicate = mock_table.delete.call_args[0][0]
        self.assertIn("file_path IN", predicate)
        self.assertIn("'path1.py'", predicate)
        self.assertIn("'path2.py'", predicate)

    def test_delete_by_file_paths_escapes_quotes(self):
        """Should escape single quotes in file paths."""
        from iara.memory.lancedb_store import LanceDBMemory

        memory = LanceDBMemory()
        memory._ensure_initialized()
        memory.db = MagicMock()
        memory.db.table_names.return_value = ["code_chunks"]
        mock_table = MagicMock()
        memory.db.open_table.return_value = mock_table
        mock_table.delete.return_value = 1

        memory.delete_by_file_paths(["path'with'quotes.py"])

        predicate = mock_table.delete.call_args[0][0]
        self.assertIn("path''with''quotes.py", predicate)

    def test_delete_by_file_paths_nonexistent_table(self):
        """Should handle gracefully when table doesn't exist."""
        from iara.memory.lancedb_store import LanceDBMemory

        memory = LanceDBMemory()
        memory._ensure_initialized()
        memory.db = MagicMock()
        memory.db.table_names.return_value = []  # No tables exist

        # Should not raise, just return early
        memory.delete_by_file_paths(["file.py"])

        # Should not attempt to open or delete from table
        memory.db.open_table.assert_not_called()

    def test_delete_by_file_paths_exception_handling(self):
        """Should log warning but not raise when deletion fails."""
        from iara.memory.lancedb_store import LanceDBMemory

        memory = LanceDBMemory()
        memory._ensure_initialized()
        memory.db = MagicMock()
        memory.db.table_names.return_value = ["code_chunks"]
        mock_table = MagicMock()
        mock_table.delete.side_effect = Exception("DB error")
        memory.db.open_table.return_value = mock_table

        with patch('iara.memory.lancedb_store.logger') as mock_logger:
            # Should not raise exception
            memory.delete_by_file_paths(["file.py"])

        mock_logger.warning.assert_called()

    def test_rrf_merge_identical_rankings(self):
        """RRF should preserve order when both rankings are identical."""
        from iara.memory.lancedb_store import LanceDBMemory

        memory = LanceDBMemory()

        vec_results = [
            {"id": "A", "content": "A"},
            {"id": "B", "content": "B"},
            {"id": "C", "content": "C"}
        ]
        fts_results = [
            {"id": "A", "content": "A"},
            {"id": "B", "content": "B"},
            {"id": "C", "content": "C"}
        ]

        merged = memory._rrf_merge(vec_results, fts_results)

        # Should maintain order A, B, C (all boosted equally)
        self.assertEqual([r["id"] for r in merged], ["A", "B", "C"])
        # No duplicates
        self.assertEqual(len(merged), 3)

    def test_rrf_merge_disjoint_rankings(self):
        """RRF should interleave when rankings have no overlap."""
        from iara.memory.lancedb_store import LanceDBMemory

        memory = LanceDBMemory()

        vec_results = [
            {"id": "A", "content": "A"},
            {"id": "B", "content": "B"},
            {"id": "C", "content": "C"}
        ]
        fts_results = [
            {"id": "D", "content": "D"},
            {"id": "E", "content": "E"},
            {"id": "F", "content": "F"}
        ]

        merged = memory._rrf_merge(vec_results, fts_results)

        # All 6 items should be present
        self.assertEqual(len(merged), 6)
        # Items should be ordered by RRF score
        merged_ids = [r["id"] for r in merged]
        # A and D should rank highest (both rank 0 in their lists)
        self.assertIn("A", merged_ids[:2])
        self.assertIn("D", merged_ids[:2])

    def test_rrf_merge_overlapping_rankings(self):
        """RRF should boost items appearing in both rankings."""
        from iara.memory.lancedb_store import LanceDBMemory

        memory = LanceDBMemory()

        vec_results = [
            {"id": "A", "content": "A"},
            {"id": "B", "content": "B"},
            {"id": "C", "content": "C"},
            {"id": "D", "content": "D"}
        ]
        fts_results = [
            {"id": "B", "content": "B"},  # Also in vec at rank 1
            {"id": "A", "content": "A"},  # Also in vec at rank 0
            {"id": "E", "content": "E"},
            {"id": "F", "content": "F"}
        ]

        merged = memory._rrf_merge(vec_results, fts_results)

        # A and B appear in both lists → should rank highest
        merged_ids = [r["id"] for r in merged]
        self.assertIn("A", merged_ids[:2])
        self.assertIn("B", merged_ids[:2])

        # Should have 6 unique items (A, B, C, D, E, F)
        self.assertEqual(len(merged), 6)

    def test_rrf_merge_empty_vector_results(self):
        """RRF should handle empty vector results gracefully."""
        from iara.memory.lancedb_store import LanceDBMemory

        memory = LanceDBMemory()

        vec_results = []
        fts_results = [
            {"id": "A", "content": "A"},
            {"id": "B", "content": "B"}
        ]

        merged = memory._rrf_merge(vec_results, fts_results)

        # Should return FTS results only
        self.assertEqual(len(merged), 2)
        self.assertEqual([r["id"] for r in merged], ["A", "B"])

    def test_rrf_merge_empty_fts_results(self):
        """RRF should handle empty FTS results gracefully."""
        from iara.memory.lancedb_store import LanceDBMemory

        memory = LanceDBMemory()

        vec_results = [
            {"id": "A", "content": "A"},
            {"id": "B", "content": "B"}
        ]
        fts_results = []

        merged = memory._rrf_merge(vec_results, fts_results)

        # Should return vector results only
        self.assertEqual(len(merged), 2)
        self.assertEqual([r["id"] for r in merged], ["A", "B"])

    def test_rrf_merge_both_empty(self):
        """RRF should handle both inputs empty."""
        from iara.memory.lancedb_store import LanceDBMemory

        memory = LanceDBMemory()

        merged = memory._rrf_merge([], [])

        self.assertEqual(merged, [])

    def test_rrf_merge_k_parameter(self):
        """RRF should use custom k parameter correctly."""
        from iara.memory.lancedb_store import LanceDBMemory

        memory = LanceDBMemory()

        vec_results = [{"id": "A", "content": "A"}]
        fts_results = [{"id": "B", "content": "B"}]

        # With different k values, relative scores change
        # But output should still be valid and ordered
        merged_k10 = memory._rrf_merge(vec_results, fts_results, k=10)
        merged_k100 = memory._rrf_merge(vec_results, fts_results, k=100)

        # Both should have same items
        self.assertEqual(len(merged_k10), 2)
        self.assertEqual(len(merged_k100), 2)

        # Order might differ based on k, but both valid
        ids_k10 = {r["id"] for r in merged_k10}
        ids_k100 = {r["id"] for r in merged_k100}
        self.assertEqual(ids_k10, {"A", "B"})
        self.assertEqual(ids_k100, {"A", "B"})

    def test_rrf_merge_preserves_first_occurrence(self):
        """RRF should preserve first occurrence when same ID appears in both lists."""
        from iara.memory.lancedb_store import LanceDBMemory

        memory = LanceDBMemory()

        # Same ID "A" appears in both lists but with different content
        vec_results = [
            {"id": "A", "content": "vec_content", "source": "vector"}
        ]
        fts_results = [
            {"id": "A", "content": "fts_content", "source": "fts"}
        ]

        merged = memory._rrf_merge(vec_results, fts_results)

        # Should have only 1 item (no duplicates)
        self.assertEqual(len(merged), 1)

        # Should preserve the first occurrence (from vec_results)
        self.assertEqual(merged[0]["content"], "vec_content")
        self.assertEqual(merged[0]["source"], "vector")

    def test_rrf_merge_handles_missing_id(self):
        """RRF should gracefully skip items without 'id' key."""
        from iara.memory.lancedb_store import LanceDBMemory

        memory = LanceDBMemory()

        vec_results = [
            {"id": "A", "content": "A"},
            {"content": "no_id_1"},  # Missing 'id' key
            {"id": "B", "content": "B"}
        ]
        fts_results = [
            {"content": "no_id_2"},  # Missing 'id' key
            {"id": "C", "content": "C"}
        ]

        merged = memory._rrf_merge(vec_results, fts_results)

        # Should only include items with valid IDs (A, B, C)
        self.assertEqual(len(merged), 3)
        merged_ids = {r["id"] for r in merged}
        self.assertEqual(merged_ids, {"A", "B", "C"})

    def test_hybrid_search_both_searches_called(self):
        """Hybrid search should call both vector and FTS searches."""
        from iara.memory.lancedb_store import LanceDBMemory

        memory = LanceDBMemory()
        memory._ensure_initialized()
        memory.db = MagicMock()
        memory.db.table_names.return_value = ["code_chunks"]
        memory._embed = MagicMock(return_value=[[0.1, 0.2]])

        # Mock table with both search modes
        mock_table = MagicMock()
        memory.db.open_table.return_value = mock_table

        # Mock vector search results (chain: search().limit().to_list())
        vec_chain = MagicMock()
        vec_chain.to_list.return_value = [
            {"id": "1", "content": "vec1", "file_path": "f", "start_line": 1, "end_line": 1, "type": "text", "metadata": {}}
        ]

        # Mock FTS search results (chain: search().limit().to_list())
        fts_chain = MagicMock()
        fts_chain.to_list.return_value = [
            {"id": "2", "content": "fts1", "file_path": "f", "start_line": 2, "end_line": 2, "type": "text", "metadata": {}}
        ]

        # Configure mock to return different results for vector vs FTS
        def search_side_effect(*args, **kwargs):
            if kwargs.get("query_type") == "fts":
                mock_fts_search = MagicMock()
                mock_fts_search.limit.return_value = fts_chain
                return mock_fts_search
            else:
                mock_vec_search = MagicMock()
                mock_vec_search.limit.return_value = vec_chain
                return mock_vec_search

        mock_table.search.side_effect = search_side_effect

        results = memory.retrieve("test query", n_results=5)

        # Both searches should have been called
        self.assertEqual(mock_table.search.call_count, 2)

        # Should get results from both (RRF merged)
        self.assertGreaterEqual(len(results), 1)

    def test_hybrid_search_fts_fallback(self):
        """Hybrid search should fall back to vector-only when FTS fails."""
        from iara.memory.lancedb_store import LanceDBMemory

        memory = LanceDBMemory()
        memory._ensure_initialized()
        memory.db = MagicMock()
        memory.db.table_names.return_value = ["code_chunks"]
        memory._embed = MagicMock(return_value=[[0.1, 0.2]])

        # Mock table
        mock_table = MagicMock()
        memory.db.open_table.return_value = mock_table

        # Mock vector search success (chain: search().limit().to_list())
        vec_chain = MagicMock()
        vec_chain.to_list.return_value = [
            {"id": "1", "content": "vec1", "file_path": "f", "start_line": 1, "end_line": 1, "type": "text", "metadata": {}}
        ]

        # Mock FTS search failure
        def search_side_effect(*args, **kwargs):
            if kwargs.get("query_type") == "fts":
                raise Exception("FTS index not found")
            else:
                mock_vec_search = MagicMock()
                mock_vec_search.limit.return_value = vec_chain
                return mock_vec_search

        mock_table.search.side_effect = search_side_effect

        with patch('iara.memory.lancedb_store.logger') as mock_logger:
            results = memory.retrieve("test query", n_results=5)

            # Should log warning about fallback
            mock_logger.warning.assert_called()
            warning_msg = mock_logger.warning.call_args[0][0]
            self.assertIn("FTS search failed", warning_msg)
            self.assertIn("falling back to vector-only", warning_msg)

        # Should still return results (from vector search)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, "1")

    def test_hybrid_search_combines_results(self):
        """Hybrid search should combine results from both searches using RRF."""
        from iara.memory.lancedb_store import LanceDBMemory

        memory = LanceDBMemory()
        memory._ensure_initialized()
        memory.db = MagicMock()
        memory.db.table_names.return_value = ["code_chunks"]
        memory._embed = MagicMock(return_value=[[0.1, 0.2]])

        # Mock table
        mock_table = MagicMock()
        memory.db.open_table.return_value = mock_table

        # Mock vector search returns items A, B (chain: search().limit().to_list())
        vec_chain = MagicMock()
        vec_chain.to_list.return_value = [
            {"id": "A", "content": "vecA", "file_path": "f", "start_line": 1, "end_line": 1, "type": "text", "metadata": {}},
            {"id": "B", "content": "vecB", "file_path": "f", "start_line": 2, "end_line": 2, "type": "text", "metadata": {}}
        ]

        # Mock FTS search returns items B, C (chain: search().limit().to_list())
        fts_chain = MagicMock()
        fts_chain.to_list.return_value = [
            {"id": "B", "content": "ftsB", "file_path": "f", "start_line": 2, "end_line": 2, "type": "text", "metadata": {}},
            {"id": "C", "content": "ftsC", "file_path": "f", "start_line": 3, "end_line": 3, "type": "text", "metadata": {}}
        ]

        def search_side_effect(*args, **kwargs):
            if kwargs.get("query_type") == "fts":
                mock_fts_search = MagicMock()
                mock_fts_search.limit.return_value = fts_chain
                return mock_fts_search
            else:
                mock_vec_search = MagicMock()
                mock_vec_search.limit.return_value = vec_chain
                return mock_vec_search

        mock_table.search.side_effect = search_side_effect

        results = memory.retrieve("test query", n_results=5)

        # Should have 3 unique items (A, B, C)
        result_ids = {r.id for r in results}
        self.assertEqual(result_ids, {"A", "B", "C"})

        # Item B appears in both → should rank higher due to RRF
        # (This is tested by the RRF algorithm tests, here we just verify it's combined)

    def test_hybrid_search_respects_limit(self):
        """Hybrid search should respect n_results limit after RRF merge."""
        from iara.memory.lancedb_store import LanceDBMemory

        memory = LanceDBMemory()
        memory._ensure_initialized()
        memory.db = MagicMock()
        memory.db.table_names.return_value = ["code_chunks"]
        memory._embed = MagicMock(return_value=[[0.1, 0.2]])

        # Mock table
        mock_table = MagicMock()
        memory.db.open_table.return_value = mock_table

        # Mock vector search returns 5 items
        vec_items = [
            {"id": f"V{i}", "content": f"vec{i}", "file_path": "f", "start_line": i, "end_line": i, "type": "text", "metadata": {}}
            for i in range(5)
        ]

        # Mock FTS search returns 5 different items
        fts_items = [
            {"id": f"F{i}", "content": f"fts{i}", "file_path": "f", "start_line": i+10, "end_line": i+10, "type": "text", "metadata": {}}
            for i in range(5)
        ]

        vec_chain = MagicMock()
        vec_chain.to_list.return_value = vec_items

        fts_chain = MagicMock()
        fts_chain.to_list.return_value = fts_items

        def search_side_effect(*args, **kwargs):
            if kwargs.get("query_type") == "fts":
                mock_fts_search = MagicMock()
                mock_fts_search.limit.return_value = fts_chain
                return mock_fts_search
            else:
                mock_vec_search = MagicMock()
                mock_vec_search.limit.return_value = vec_chain
                return mock_vec_search

        mock_table.search.side_effect = search_side_effect

        # Request only 3 results
        results = memory.retrieve("test query", n_results=3)

        # Should return exactly 3 results (even though 10 were available)
        self.assertEqual(len(results), 3)


