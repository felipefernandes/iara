import os
import ast
import sys
from typing import List, Generator
from iara.memory.interface import CodeChunk

class CodeChunker:
    """Splits code into chunks for indexing."""

    def chunk_file(self, file_path: str, content: str) -> List[CodeChunk]:
        _, ext = os.path.splitext(file_path)
        if ext == ".py":
            return self._chunk_python(file_path, content)
        # Fallback for other files: simple block chunking
        return self._chunk_text(file_path, content)

    def _chunk_python(self, file_path: str, content: str) -> List[CodeChunk]:
        chunks = []
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return self._chunk_text(file_path, content)

        lines = content.splitlines()

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                start_line = node.lineno
                end_line = node.end_lineno if hasattr(node, "end_lineno") else start_line
                
                # Extract source code for this node
                # Note: This is a simple extraction. Ideally we'd capture decorators too.
                # ast.get_source_segment is available in Python 3.8+
                chunk_content = ast.get_source_segment(content, node)
                
                if not chunk_content:
                    continue

                # Graph-Lite Metadata Extraction
                metadata = {
                    "name": node.name,
                    "docstring": ast.get_docstring(node),
                    "calls": [],
                    "inherits": []
                }
                
                if isinstance(node, ast.ClassDef):
                    chunk_type = "class"
                    for base in node.bases:
                        if isinstance(base, ast.Name):
                            metadata["inherits"].append(base.id)
                else:
                    chunk_type = "function"
                
                # Extract calls within this function/method
                for subnode in ast.walk(node):
                    if isinstance(subnode, ast.Call):
                        if isinstance(subnode.func, ast.Name):
                            metadata["calls"].append(subnode.func.id)
                        elif isinstance(subnode.func, ast.Attribute):
                             metadata["calls"].append(subnode.func.attr)

                chunk = CodeChunk(
                    id=f"{file_path}:{node.name}:{start_line}",
                    content=chunk_content,
                    file_path=file_path,
                    start_line=start_line,
                    end_line=end_line,
                    type=chunk_type,
                    metadata=metadata
                )
                chunks.append(chunk)

        # Also capture top-level module docstrings or assignments? 
        # For now, let's keep it to functions and classes to reduce noise.
        return chunks

    def _chunk_text(self, file_path: str, content: str) -> List[CodeChunk]:
        """Simple chunking for non-code files."""
        # Simple strategy: Max 100 lines per chunk
        lines = content.splitlines()
        chunks = []
        chunk_size = 100
        
        for i in range(0, len(lines), chunk_size):
            chunk_lines = lines[i:i + chunk_size]
            chunk_content = "\n".join(chunk_lines)
            chunks.append(CodeChunk(
                id=f"{file_path}:{i+1}",
                content=chunk_content,
                file_path=file_path,
                start_line=i + 1,
                end_line=i + len(chunk_lines),
                type="text",
                metadata={
                    "name": "", 
                    "docstring": "",
                    "calls": [],
                    "inherits": []
                }
            ))
            
        return chunks

class Indexer:
    """Walks directory and indexes files."""
    
    def __init__(self, memory_interface):
        self.memory = memory_interface
        self.chunker = CodeChunker()
        self.ignore_patterns = set([
            ".git", "__pycache__", "venv", ".venv", "node_modules", 
            ".idea", ".vscode", "dist", "build", ".iara", "__pypackages__"
        ])
        self.ignore_extensions = set([
            ".pyc", ".pyo", ".pyd", ".so", ".dll", ".exe", ".bin", ".iso", 
            ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".psd", ".pdf",
            ".zip", ".tar", ".gz", ".7z", ".rar", ".db", ".sqlite", ".lancedb"
        ])

    def index_project(self, root_path: str):
        all_chunks = []
        for root, dirs, files in os.walk(root_path):
            # Filtering ignored directories
            dirs[:] = [d for d in dirs if d not in self.ignore_patterns]
            
            for file in files:
                if file.startswith("."):
                    continue
                
                _, ext = os.path.splitext(file)
                if ext.lower() in self.ignore_extensions:
                    continue
                    
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, root_path)
                
                try:
                    # simplistic binary check
                    with open(file_path, "r", encoding="utf-8", errors="strict") as f:
                        content = f.read()
                        
                    print(f"📄 Indexing: {rel_path}", file=sys.stderr)
                        
                    chunks = self.chunker.chunk_file(rel_path, content)
                    all_chunks.extend(chunks)
                    
                    if len(all_chunks) >= 100:
                        self.memory.index_chunks(all_chunks)
                        all_chunks = []
                        
                except Exception as e:
                    # Log error but continue
                    print(f"Skipping {rel_path}: {e}")
                    
        if all_chunks:
            self.memory.index_chunks(all_chunks)
