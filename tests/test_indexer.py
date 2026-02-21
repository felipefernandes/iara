
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
             patch('builtins.open', mock_open(read_data="print('hello')")) as mock_file, \
             patch('os.path.exists', return_value=True), \
             patch('os.path.isdir', return_value=True):
            
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
             patch('sys.stderr'), \
             patch('os.path.exists', return_value=True), \
             patch('os.path.isdir', return_value=True):
            
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

    def test_index_project_invalid_path(self):
        """Test that index_project raises FileNotFoundError for nonexistent paths."""
        mock_memory = MagicMock()
        indexer = Indexer(mock_memory)
        with self.assertRaises(FileNotFoundError):
            indexer.index_project('/nonexistent/path/xyz')

    def test_index_project_not_a_directory(self):
        """Test that index_project raises NotADirectoryError for file paths."""
        import tempfile
        mock_memory = MagicMock()
        indexer = Indexer(mock_memory)
        # Create a temporary file (not directory)
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name
        try:
            with self.assertRaises(NotADirectoryError):
                indexer.index_project(temp_path)
        finally:
            os.remove(temp_path)

    def test_index_project_skips_dotfiles(self):
        """Test that files starting with '.' are skipped."""
        mock_memory = MagicMock()
        indexer = Indexer(mock_memory)
        
        with patch('os.walk') as mock_walk, \
             patch('builtins.open', mock_open(read_data="content")) as mock_file, \
             patch('os.path.exists', return_value=True), \
             patch('os.path.isdir', return_value=True), \
             patch('sys.stderr'):
            
            mock_walk.return_value = [
                ('root', [], ['.hidden', 'visible.py'])
            ]
            
            indexer.index_project('root')
            
            # Only visible.py should be opened, not .hidden
            opened_files = [c[1][0] for c in mock_file.mock_calls if c[0] == '' and c[1]]
            opened_files = [os.path.normpath(p) for p in opened_files]
            self.assertFalse(any('.hidden' in p for p in opened_files))
            self.assertTrue(any('visible.py' in p for p in opened_files))

    def test_index_project_unicode_error(self):
        """Test that UnicodeDecodeError is handled gracefully (binary files)."""
        mock_memory = MagicMock()
        indexer = Indexer(mock_memory)
        
        real_open = open
        def smart_open(file, *args, **kwargs):
            # Allow hash file operations to succeed normally
            if 'file_hashes' in str(file):
                return real_open(os.devnull, *args, **kwargs)
            raise UnicodeDecodeError("utf-8", b"", 0, 1, "invalid byte")
        
        with patch('os.walk') as mock_walk, \
             patch('builtins.open', side_effect=smart_open), \
             patch('os.path.exists', return_value=True), \
             patch('os.path.isdir', return_value=True), \
             patch('os.makedirs'), \
             self.assertLogs('iara.memory.indexer', level='DEBUG') as cm:
            
            mock_walk.return_value = [
                ('root', [], ['binary.dat'])
            ]
            
            # Should not raise
            indexer.index_project('root')
            
            # Verify log message
            self.assertTrue(any("Skipping binary/non-UTF-8" in output for output in cm.output))
            
            # No chunks should be indexed
            mock_memory.index_chunks.assert_not_called()

    def test_index_project_unexpected_error(self):
        """Test that unexpected errors are caught and logged."""
        mock_memory = MagicMock()
        indexer = Indexer(mock_memory)
        
        real_open = open
        def smart_open(file, *args, **kwargs):
            # Allow hash file operations to succeed normally
            if 'file_hashes' in str(file):
                return real_open(os.devnull, *args, **kwargs)
            raise RuntimeError("Something unexpected")
        
        with patch('os.walk') as mock_walk, \
             patch('builtins.open', side_effect=smart_open), \
             patch('os.path.exists', return_value=True), \
             patch('os.path.isdir', return_value=True), \
             patch('os.makedirs'), \
             self.assertLogs('iara.memory.indexer', level='WARNING') as cm:
            
            mock_walk.return_value = [
                ('root', [], ['problem.py'])
            ]
            
            # Should not raise
            indexer.index_project('root')
            
            # Verify log message
            self.assertTrue(any("Unexpected error processing" in output for output in cm.output))
            
            mock_memory.index_chunks.assert_not_called()

    def test_index_project_progress_indicator(self):
        """Test that progress is printed every 10 files."""
        import tempfile, shutil
        
        mock_memory = MagicMock()
        indexer = Indexer(mock_memory)
        
        # Create 11 files to trigger the progress indicator
        temp_dir = tempfile.mkdtemp()
        try:
            for i in range(11):
                with open(os.path.join(temp_dir, f"file{i}.py"), "w") as f:
                    f.write(f"def func{i}(): pass")
            
            with patch('sys.stderr') as mock_stderr:
                indexer.index_project(temp_dir)
                
                # The progress print should have been called (at file 10)
                stderr_output = "".join(str(c) for c in mock_stderr.write.call_args_list)
                self.assertIn("10", stderr_output)
        finally:
            shutil.rmtree(temp_dir)

    def test_index_project_batch_flush(self):
        """Test that chunks are flushed in batches of 100."""
        mock_memory = MagicMock()
        indexer = Indexer(mock_memory)
        
        # Make chunker return many chunks per file to trigger batch flush
        indexer.chunker = MagicMock()
        chunks_batch = [CodeChunk(
            id=f"chunk-{i}", content=f"code-{i}", file_path="big.py",
            start_line=i, end_line=i, type="function"
        ) for i in range(50)]
        indexer.chunker.chunk_file.return_value = chunks_batch
        
        with patch('os.walk') as mock_walk, \
             patch('builtins.open', mock_open(read_data="code")), \
             patch('os.path.exists', return_value=True), \
             patch('os.path.isdir', return_value=True), \
             patch('sys.stderr'):
            
            # 3 files x 50 chunks = 150 chunks. Should flush at 100 and then at final.
            mock_walk.return_value = [
                ('root', [], ['a.py', 'b.py', 'c.py'])
            ]
            
            indexer.index_project('root')
            
            # Should have been called at least twice (batch at 100 + final flush)
            self.assertGreaterEqual(mock_memory.index_chunks.call_count, 2)


class TestCodeChunkRepr(unittest.TestCase):
    def test_repr_with_metadata(self):
        chunk = CodeChunk(
            id="test:foo:1", content="def foo(): pass",
            file_path="main.py", start_line=1, end_line=3,
            type="function", metadata={"name": "foo", "calls": []}
        )
        result = repr(chunk)
        self.assertIn("function", result)
        self.assertIn("foo", result)
        self.assertIn("main.py", result)
        self.assertIn("1-3", result)

    def test_repr_without_metadata(self):
        chunk = CodeChunk(
            id="test:1:1", content="some text",
            file_path="notes.txt", start_line=1, end_line=10,
            type="text", metadata=None
        )
        result = repr(chunk)
        self.assertIn("text", result)
        self.assertIn("notes.txt", result)


class TestIndexerDeletion(unittest.TestCase):
    """Tests for deleted file detection and cleanup functionality."""

    def test_detect_deleted_files_empty_existing(self):
        """First run with no existing hashes should detect no deletions."""
        mock_memory = MagicMock()
        indexer = Indexer(mock_memory)

        deleted = indexer._detect_deleted_files({}, {"file1.py": "hash1"})

        self.assertEqual(deleted, [])

    def test_detect_deleted_files_some_deleted(self):
        """Should detect files in existing but not in new."""
        mock_memory = MagicMock()
        indexer = Indexer(mock_memory)

        existing = {"file1.py": "hash1", "file2.py": "hash2", "file3.py": "hash3"}
        new = {"file1.py": "hash1", "file3.py": "hash3"}

        deleted = indexer._detect_deleted_files(existing, new)

        self.assertEqual(deleted, ["file2.py"])

    def test_detect_deleted_files_all_deleted(self):
        """Should detect when all files are deleted."""
        mock_memory = MagicMock()
        indexer = Indexer(mock_memory)

        existing = {"file1.py": "hash1", "file2.py": "hash2"}
        new = {}

        deleted = indexer._detect_deleted_files(existing, new)

        self.assertCountEqual(deleted, ["file1.py", "file2.py"])

    def test_cleanup_deleted_files_calls_memory(self):
        """Should call memory.delete_by_file_paths with correct arguments."""
        mock_memory = MagicMock()
        indexer = Indexer(mock_memory)
        deleted = ["file1.py", "file2.py"]

        with patch('iara.memory.indexer.logger') as mock_logger:
            indexer._cleanup_deleted_files(deleted)

        mock_memory.delete_by_file_paths.assert_called_once_with(deleted)
        mock_logger.info.assert_called()

    def test_cleanup_deleted_files_handles_exception(self):
        """Should log warning but not raise when deletion fails."""
        mock_memory = MagicMock()
        mock_memory.delete_by_file_paths.side_effect = Exception("DB error")
        indexer = Indexer(mock_memory)

        with patch('iara.memory.indexer.logger') as mock_logger:
            # Should not raise exception
            indexer._cleanup_deleted_files(["file1.py"])

        mock_logger.warning.assert_called()

    def test_cleanup_deleted_files_empty_list(self):
        """Should be a no-op when list is empty."""
        mock_memory = MagicMock()
        indexer = Indexer(mock_memory)

        indexer._cleanup_deleted_files([])

        # Should not call delete_by_file_paths
        mock_memory.delete_by_file_paths.assert_not_called()

    def test_index_project_cleanup_deleted_files_integration(self):
        """Integration test: deleted files should be cleaned up from index."""
        import tempfile
        import shutil

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create initial files
            file1 = os.path.join(temp_dir, "keep.py")
            file2 = os.path.join(temp_dir, "delete.py")

            with open(file1, "w") as f:
                f.write("def keep(): pass")
            with open(file2, "w") as f:
                f.write("def delete(): pass")

            # First indexing
            mock_memory = MagicMock()
            indexer = Indexer(mock_memory)
            indexer.index_project(temp_dir)

            # Verify both files were indexed
            all_chunks = []
            for call in mock_memory.index_chunks.call_args_list:
                all_chunks.extend(call.args[0])
            self.assertTrue(any("keep.py" in c.file_path for c in all_chunks))
            self.assertTrue(any("delete.py" in c.file_path for c in all_chunks))

            # Delete one file
            os.remove(file2)

            # Re-index
            mock_memory.reset_mock()
            indexer2 = Indexer(mock_memory)
            indexer2.index_project(temp_dir)

            # Verify delete_by_file_paths was called with deleted file
            mock_memory.delete_by_file_paths.assert_called_once()
            deleted_paths = mock_memory.delete_by_file_paths.call_args[0][0]
            self.assertTrue(any("delete.py" in path for path in deleted_paths))
