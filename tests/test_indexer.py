
import unittest
import ast
import os
from unittest.mock import MagicMock, patch, mock_open
from iara.memory.indexer import CodeChunker, CodeVisitor, Indexer
from iara.memory.interface import CodeChunk

class TestCodeChunker(unittest.TestCase):
    def setUp(self):
        self.chunker = CodeChunker()

    def test_chunk_python_function(self):
        code = """
def hello_world():
    print("Hello")
    return True
"""
        chunks = self.chunker.chunk_file("test.py", code)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].type, "function")
        self.assertEqual(chunks[0].metadata["name"], "hello_world")
        self.assertIn('print("Hello")', chunks[0].content)

    def test_chunk_python_class_with_methods(self):
        code = """
class MyClass(BaseClass):
    def method_one(self):
        pass
    
    def method_two(self):
        self.method_one()
"""
        chunks = self.chunker.chunk_file("test.py", code)
        # Expect 3 chunks: Class, Method1, Method2
        self.assertEqual(len(chunks), 3)

        class_chunk = next(c for c in chunks if c.type == "class")
        self.assertEqual(class_chunk.metadata["name"], "MyClass")
        self.assertIn("BaseClass", class_chunk.metadata["inherits"])

        method_chunk = next(c for c in chunks if c.metadata["name"] == "method_two")
        self.assertIn("method_one", method_chunk.metadata["calls"])

    def test_shallow_call_extraction(self):
        """Regression: calls in nested functions should NOT appear in parent metadata."""
        code = """
class Outer:
    def outer_method(self):
        top_level_call()
    
    def inner_container(self):
        def nested_helper():
            nested_only_call()
        nested_helper()
"""
        chunks = self.chunker.chunk_file("test.py", code)
        
        # Find the class chunk
        class_chunk = next(c for c in chunks if c.type == "class")
        # The class itself should NOT have any calls (its methods are separate chunks)
        # Calls inside methods are counted per-method, not at class level
        self.assertNotIn("nested_only_call", class_chunk.metadata["calls"])
        
        # Find inner_container method
        container = next(c for c in chunks if c.metadata["name"] == "inner_container")
        # inner_container directly calls nested_helper(), but NOT nested_only_call()
        self.assertIn("nested_helper", container.metadata["calls"])
        self.assertNotIn("nested_only_call", container.metadata["calls"])

    def test_chunk_python_async(self):
        code = """
async def async_func():
    await something()
"""
        chunks = self.chunker.chunk_file("async.py", code)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].type, "function")
        self.assertEqual(chunks[0].metadata["name"], "async_func")

    def test_chunk_invalid_python_falls_back_to_text(self):
        # Invalid syntax should trigger text chunking
        code = "def invalid_syntax(: print()"
        chunks = self.chunker.chunk_file("broken.py", code)
        self.assertGreater(len(chunks), 0)
        self.assertEqual(chunks[0].type, "text")

    def test_chunk_text_file(self):
        # Create dummy content with > 100 lines
        lines = ["line" + str(i) for i in range(150)]
        content = "\n".join(lines)
        
        # Override constant for test
        self.chunker.MAX_TEXT_CHUNK_LINES = 100
        
        chunks = self.chunker.chunk_file("notes.txt", content)
        self.assertEqual(len(chunks), 2) # 100 + 50
        self.assertEqual(chunks[0].type, "text")
        self.assertEqual(chunks[1].type, "text")

class TestIndexer(unittest.TestCase):
    def test_index_project_integration(self):
        """Integration test for index_project using a temporary directory."""
        import tempfile
        import shutil
        import os
        from iara.memory.indexer import Indexer
        
        # Create a temp directory structure
        with tempfile.TemporaryDirectory() as temp_dir:
            # 1. Valid Python file
            with open(os.path.join(temp_dir, "valid.py"), "w", encoding="utf-8") as f:
                f.write("def foo(): pass")
                
            # 2. Ignored file (by extension)
            with open(os.path.join(temp_dir, "ignored.pyc"), "w", encoding="utf-8") as f:
                f.write("binary data")
                
            # 3. Ignored directory
            os.makedirs(os.path.join(temp_dir, ".git"))
            with open(os.path.join(temp_dir, ".git", "HEAD"), "w", encoding="utf-8") as f:
                f.write("ref: refs/heads/main")
                
            # 4. Nested valid file
            os.makedirs(os.path.join(temp_dir, "src"))
            with open(os.path.join(temp_dir, "src", "main.py"), "w", encoding="utf-8") as f:
                f.write("class Bar: pass")

            # Mock memory to verify calls
            mock_memory = MagicMock()
            indexer = Indexer(mock_memory)
            
            # Run indexing
            indexer.index_project(temp_dir)
            
            # Verify that index_chunks was called
            self.assertTrue(mock_memory.index_chunks.called)
            
            # Collect all chunks that were indexed
            all_chunks = []
            for call in mock_memory.index_chunks.call_args_list:
                all_chunks.extend(call.args[0])
                
            # Check content
            file_paths = [c.file_path for c in all_chunks]
            # normalize paths for comparison
            # The indexer produces relative paths
            
            self.assertFalse(any("ignored.pyc" in p for p in file_paths))
            self.assertFalse(any(".git" in p for p in file_paths))

    def test_indexer_ignores_files(self):
        """Test that indexer correctly ignores specified patterns and extensions."""
        # Using mocks to test ignore logic specifically without creating files
        mock_memory = MagicMock()
        indexer = Indexer(mock_memory)
        
        with patch('os.walk') as mock_walk, \
             patch('builtins.open', mock_open(read_data="print('hello')")) as mock_file:
            
            mock_walk.return_value = [
                ('root', ['.git', 'src'], ['ignored.pyc', 'valid.py']),
                ('root/.git', [], ['HEAD']),
                ('root/src', [], ['utils.py'])
            ]
            
            indexer.index_project('root')
            
            # Check opened files
            # Note: valid.py and utils.py should be opened
            # ignored.pyc and .git/HEAD should NOT
            
            opened_files = []
            for c in mock_file.mock_calls:
                if c[0] == '': # call(path, ...)
                    args = c[1]
                    if args:
                        opened_files.append(args[0])
            
            # Normalize for comparison
            opened_files = [os.path.normpath(p) for p in opened_files]
            
            self.assertTrue(any('valid.py' in p for p in opened_files))
            self.assertTrue(any('utils.py' in p for p in opened_files))
            self.assertFalse(any('ignored.pyc' in p for p in opened_files))

    def test_indexer_handles_read_errors(self):
        """Test that indexer continues despite file read errors."""
        mock_memory = MagicMock()
        indexer = Indexer(mock_memory)
        
        # Simple file mock that supports context manager
        good_file_mock = MagicMock()
        good_file_mock.__enter__.return_value.read.return_value = "good_code"
        
        m_open = MagicMock()
        def open_side_effect(file, *args, **kwargs):
            if "bad.py" in str(file):
                 raise IOError("Permission denied")
            return good_file_mock
            
        m_open.side_effect = open_side_effect
        
        with patch('os.walk') as mock_walk, \
             patch('builtins.open', m_open), \
             patch('sys.stderr'):
            
            mock_walk.return_value = [
                ('root', [], ['bad.py', 'good.py'])
            ]

             # Mock chunker to return a chunk for good.py
            indexer.chunker = MagicMock()
            indexer.chunker.chunk_file.return_value = [CodeChunk(
                id="1", content="good", file_path="good.py", start_line=1, end_line=1, type="text"
            )]
            
            indexer.index_project('root')
            
            # Should have indexed good.py
            self.assertTrue(mock_memory.index_chunks.called)
