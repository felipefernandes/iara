
import unittest
import ast
from unittest.mock import MagicMock
from iara.memory.indexer import CodeChunker, CodeVisitor

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
