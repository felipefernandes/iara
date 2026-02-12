
import unittest
import shutil
import tempfile
import os
from unittest.mock import MagicMock, patch

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
        self.mock_lancedb.connect.assert_called_once()

    def test_index_chunks(self):
        from iara.memory.lancedb_store import LanceDBMemory
        from iara.memory.interface import CodeChunk

        memory = LanceDBMemory()
        
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
        }] # Simulating to_list output directly which usually returns list of dicts

        results = memory.retrieve("query")
        # Ensure we handled the result correctly
        self.assertEqual(len(results), 1)

