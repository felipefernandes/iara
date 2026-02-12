import os
import ast
import sys
import logging
from typing import List, Generator
from iara.memory.interface import CodeChunk

logger = logging.getLogger(__name__)

class CodeChunker:
    """Splits code into chunks for indexing."""

    MAX_TEXT_CHUNK_LINES = 100

    def chunk_file(self, file_path: str, content: str) -> List[CodeChunk]:
        _, ext = os.path.splitext(file_path)
        if ext == ".py":
            return self._chunk_python(file_path, content)
        # Fallback for other files: simple block chunking
        return self._chunk_text(file_path, content)

    def _chunk_python(self, file_path: str, content: str) -> List[CodeChunk]:
        """
        Chunks Python code using AST to identify functions and classes.
        
        This method parses the python content into an AST. It then uses a
        CodeVisitor to walk the tree and extract CodeChunks for each
        FunctionDef, AsyncFunctionDef, and ClassDef. If syntax errors occur,
        it falls back to text-based chunking.
        """
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return self._chunk_text(file_path, content)

        visitor = CodeVisitor(file_path, content)
        visitor.visit(tree)
        return visitor.chunks

    def _chunk_text(self, file_path: str, content: str) -> List[CodeChunk]:
        """Simple chunking for non-code files."""
        # Simple strategy: Max 100 lines per chunk
        lines = content.splitlines()
        chunks = []
        
        for i in range(0, len(lines), self.MAX_TEXT_CHUNK_LINES):
            chunk_lines = lines[i:i + self.MAX_TEXT_CHUNK_LINES]
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


class CodeVisitor(ast.NodeVisitor):
    def __init__(self, file_path: str, content: str):
        self.file_path = file_path
        self.content = content
        self.chunks = []

    def visit_FunctionDef(self, node):
        self._process_node(node, "function")
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        self._process_node(node, "function")
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        self._process_node(node, "class")
        self.generic_visit(node)

    def _process_node(self, node, chunk_type):
        start_line = node.lineno
        end_line = node.end_lineno if hasattr(node, "end_lineno") else start_line
        
        # Extract source code
        chunk_content = ast.get_source_segment(self.content, node)
        
        if not chunk_content:
            return

        # Metadata
        metadata = {
            "name": node.name,
            "docstring": ast.get_docstring(node),
            "calls": [],
            "inherits": []
        }
        
        if isinstance(node, ast.ClassDef):
            for base in node.bases:
                if isinstance(base, ast.Name):
                    metadata["inherits"].append(base.id)
        
        # Extract calls within this node
        # We use a localized walk here as we only want calls *inside* this definition
        for subnode in ast.walk(node):
            if isinstance(subnode, ast.Call):
                if isinstance(subnode.func, ast.Name):
                    metadata["calls"].append(subnode.func.id)
                elif isinstance(subnode.func, ast.Attribute):
                        metadata["calls"].append(subnode.func.attr)

        chunk = CodeChunk(
            id=f"{self.file_path}:{node.name}:{start_line}",
            content=chunk_content,
            file_path=self.file_path,
            start_line=start_line,
            end_line=end_line,
            type=chunk_type,
            metadata=metadata
        )
        self.chunks.append(chunk)


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
        file_count = 0
        
        print(f"🧠 Scanning {root_path}...", file=sys.stderr)
        
        for root, dirs, files in os.walk(root_path):
            # Defensive check: if we somehow entered an ignored directory
            # (e.g. valid for some os.walk implementations or mocks)
            if any(ign in root.split(os.sep) for ign in self.ignore_patterns):
                continue

            # Filtering ignored directories
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
                    
                    # Progress Indicator (every 10 files)
                    file_count += 1
                    if file_count % 10 == 0:
                         print(f"   Indexed {file_count} files...", file=sys.stderr)
                        
                    chunks = self.chunker.chunk_file(rel_path, content)
                    all_chunks.extend(chunks)
                    
                    if len(all_chunks) >= 100:
                        self.memory.index_chunks(all_chunks)
                        all_chunks = []
                        
                except Exception as e:
                    # Log error but continue
                    if "utf-8" not in str(e): # Ignore common encoding errors silentlyish
                        print(f"Skipping {rel_path}: {e}")
                    
        if all_chunks:
            self.memory.index_chunks(all_chunks)
            
        print(f"✅ Indexed {file_count} files.", file=sys.stderr)
