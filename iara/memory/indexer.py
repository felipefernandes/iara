import os
import re
import ast
import sys
import logging
from typing import List, Generator, Tuple
from iara.memory.interface import CodeChunk

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Regex patterns for brace-language smart chunking (JS/TS/C#)
# ---------------------------------------------------------------------------
_JS_TS_PATTERNS = [
    # Named function: function foo(…) { or export async function foo(…) {
    re.compile(
        r'^(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\([^)]*\)',
        re.MULTILINE
    ),
    # Class declaration: class Foo { or export class Foo extends Bar {
    re.compile(
        r'^(?:export\s+)?class\s+(\w+)',
        re.MULTILINE
    ),
    # Arrow-function const: const foo = (…) => { or const foo = async (…) => {
    re.compile(
        r'^\s*(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>',
        re.MULTILINE
    ),
]

_CS_PATTERNS = [
    # Class / struct / interface / enum
    re.compile(
        r'(?:public|private|protected|internal)?\s*'
        r'(?:static\s+|abstract\s+|sealed\s+|partial\s+)*'
        r'(?:class|struct|interface|record|enum)\s+(\w+)',
        re.MULTILINE
    ),
    # Method declaration  (visibility + return-type + name + parentheses)
    re.compile(
        r'(?:public|private|protected|internal)\s+'
        r'(?:static\s+|virtual\s+|override\s+|abstract\s+|async\s+)*'
        r'[\w<>\[\],\s]+\s+(\w+)\s*\([^)]*\)',
        re.MULTILINE
    ),
]


class CodeChunker:
    """Splits code into chunks for indexing."""

    MAX_TEXT_CHUNK_LINES = 100

    def chunk_file(self, file_path: str, content: str) -> List[CodeChunk]:
        _, ext = os.path.splitext(file_path)
        if ext == ".py":
            return self._chunk_python(file_path, content)
        if ext in (".js", ".ts"):
            return self._chunk_js_ts(file_path, content)
        if ext == ".cs":
            return self._chunk_csharp(file_path, content)
        # Fallback for other files: simple block chunking
        return self._chunk_text(file_path, content)

    # -- Python (AST) -------------------------------------------------------

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

    # -- JavaScript / TypeScript (Regex + brace balancing) ------------------

    def _chunk_js_ts(self, file_path: str, content: str) -> List[CodeChunk]:
        """Chunk JS/TS code by function and class declarations."""
        chunks = self._chunk_brace_language(file_path, content, _JS_TS_PATTERNS)
        return chunks if chunks else self._chunk_text(file_path, content)

    # -- C# (Regex + brace balancing) ---------------------------------------

    def _chunk_csharp(self, file_path: str, content: str) -> List[CodeChunk]:
        """Chunk C# code by class and method declarations."""
        chunks = self._chunk_brace_language(file_path, content, _CS_PATTERNS)
        return chunks if chunks else self._chunk_text(file_path, content)

    # -- Shared brace-language helper ---------------------------------------

    def _chunk_brace_language(
        self,
        file_path: str,
        content: str,
        patterns: List[re.Pattern],
    ) -> List[CodeChunk]:
        """Extract code blocks by matching declaration patterns then balancing braces.

        For each regex match the helper locates the first opening brace ``{``
        after the match and counts braces until the matching ``}`` is found.
        The full text from the match start to the closing brace (inclusive)
        becomes one ``CodeChunk``.  Matches whose opening brace falls inside
        an already-extracted block are skipped to avoid duplicates.
        """
        lines = content.splitlines(True)  # keep line endings for offset maths
        line_offsets: List[int] = []
        offset = 0
        for line in lines:
            line_offsets.append(offset)
            offset += len(line)

        def _offset_to_line(off: int) -> int:
            """Return the 1-based line number for a character offset."""
            lo, hi = 0, len(line_offsets) - 1
            while lo < hi:
                mid = (lo + hi + 1) // 2
                if line_offsets[mid] <= off:
                    lo = mid
                else:
                    hi = mid - 1
            return lo + 1  # 1-based

        # Collect all matches across all patterns
        raw_matches: List[Tuple[int, int, str]] = []  # (start, end_of_match, name)
        for pat in patterns:
            for m in pat.finditer(content):
                name = m.group(1) if m.lastindex else ""
                raw_matches.append((m.start(), m.end(), name))

        # Sort by position so we can skip nested matches
        raw_matches.sort(key=lambda t: t[0])

        chunks: List[CodeChunk] = []
        covered_end = -1  # track the furthest byte already covered

        for match_start, match_end, name in raw_matches:
            if match_start < covered_end:
                continue  # inside a previously extracted block

            # Find the first '{' at or after match_start
            brace_pos = content.find("{", match_start)
            if brace_pos == -1:
                continue  # no body to extract

            # Balance braces
            depth = 0
            block_end = brace_pos
            in_string: str = ""
            escape_next = False

            for i in range(brace_pos, len(content)):
                ch = content[i]

                if escape_next:
                    escape_next = False
                    continue

                if ch == "\\":
                    escape_next = True
                    continue

                # Simple string tracking (single / double / template-literal)
                if in_string:
                    if ch == in_string:
                        in_string = ""
                    continue
                if ch in ('"', "'", "`"):
                    in_string = ch
                    continue

                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        block_end = i
                        break

            if depth != 0:
                # Unbalanced – skip this match
                continue

            block_text = content[match_start: block_end + 1]
            start_line = _offset_to_line(match_start)
            end_line = _offset_to_line(block_end)

            # Determine chunk type
            declaration_snippet = content[match_start:match_end]
            _CLASS_KEYWORDS = ("class ", "struct ", "interface ", "record ", "enum ")
            chunk_type = "class" if any(kw in declaration_snippet for kw in _CLASS_KEYWORDS) else "function"

            chunks.append(CodeChunk(
                id=f"{file_path}:{name}:{start_line}",
                content=block_text,
                file_path=file_path,
                start_line=start_line,
                end_line=end_line,
                type=chunk_type,
                metadata={
                    "name": name,
                    "docstring": "",
                    "calls": [],
                    "inherits": [],
                },
            ))

            covered_end = block_end + 1

        return chunks

    # -- Plain-text fallback ------------------------------------------------

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
        
        # Extract calls only from direct statements (not nested functions/classes)
        metadata["calls"] = self._extract_calls_shallow(node)

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

    def _extract_calls_shallow(self, node) -> list:
        """Extract function/method calls from direct statements only.
        
        Unlike ast.walk(), this skips nested FunctionDef/AsyncFunctionDef/ClassDef
        nodes, so calls inside nested definitions are not attributed to the parent.
        This is O(n) on the node's direct children rather than O(n²) from ast.walk.
        """
        calls = []
        for child in ast.iter_child_nodes(node):
            # Skip nested definitions — they will be processed separately
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            # Check if the child itself is a Call
            if isinstance(child, ast.Call):
                self._collect_call_name(child, calls)
            # Walk the child's subtree (but NOT nested defs)
            for subnode in ast.walk(child):
                if isinstance(subnode, ast.Call):
                    self._collect_call_name(subnode, calls)
        return calls

    @staticmethod
    def _collect_call_name(call_node, calls):
        """Extract the function name from an ast.Call node."""
        if isinstance(call_node.func, ast.Name):
            calls.append(call_node.func.id)
        elif isinstance(call_node.func, ast.Attribute):
            calls.append(call_node.func.attr)


import hashlib
import json
import fnmatch
from pathlib import Path

class Indexer:
    """Walks directory and indexes files."""
    
    def __init__(self, memory_interface, config=None):
        from iara.config import load_config
        self.memory = memory_interface
        self.config = config or load_config()
        self.max_index_file_size = self.config.get("review", {}).get("max_index_file_size", 1048576)
        self.chunker = CodeChunker()
        user_ignore_patterns = self.config.get("review", {}).get("ignore_patterns", [])
        
        valid_user_patterns = []
        for p in user_ignore_patterns:
            try:
                # Test if the pattern can be compiled to regex
                re.compile(fnmatch.translate(p))
                valid_user_patterns.append(p)
            except re.error:
                logger.warning(f"Invalid ignore pattern '{p}' provided in config. Skipping.")
                
        self.ignore_patterns = set([
            ".git", "__pycache__", "venv", ".venv", "node_modules", 
            ".idea", ".vscode", "dist", "build", ".iara", "__pypackages__"
        ]).union(set(valid_user_patterns))
        self.ignore_extensions = set([
            ".pyc", ".pyo", ".pyd", ".so", ".dll", ".exe", ".bin", ".iso", 
            ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".psd", ".pdf",
            ".zip", ".tar", ".gz", ".7z", ".rar", ".db", ".sqlite", ".lancedb"
        ])
        self.hashes_file = ".iara/file_hashes.json"
        self._ignore_regex = None

    def _is_ignored(self, name: str) -> bool:
        if self._ignore_regex is None:
            regexes = [fnmatch.translate(p) for p in self.ignore_patterns]
            self._ignore_regex = re.compile('|'.join(regexes)) if regexes else None
            
        return bool(self._ignore_regex and self._ignore_regex.match(name))

    def _load_hashes(self):
        if os.path.exists(self.hashes_file):
            try:
                with open(self.hashes_file, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError, OSError) as e:
                logger.warning("Failed to load file hashes: %s", e)
                return {}
        return {}

    def _save_hashes(self, hashes):
        os.makedirs(os.path.dirname(self.hashes_file), exist_ok=True)
        with open(self.hashes_file, "w") as f:
            json.dump(hashes, f)

    def _compute_hash(self, content):
        return hashlib.md5(content.encode("utf-8")).hexdigest()

    def _detect_deleted_files(self, existing_hashes: dict, new_hashes: dict) -> List[str]:
        """Detect files that were deleted since last indexing.

        Args:
            existing_hashes: Hash map from previous indexing run.
            new_hashes: Hash map from current indexing run.

        Returns:
            List of relative file paths that exist in existing_hashes but not in new_hashes.
        """
        if not existing_hashes:
            return []  # First run, nothing to delete

        deleted = []
        for file_path in existing_hashes.keys():
            if file_path not in new_hashes:
                deleted.append(file_path)

        return deleted

    def _cleanup_deleted_files(self, deleted_files: List[str]):
        """Remove chunks for deleted files from the memory store.

        Args:
            deleted_files: List of relative file paths to clean up.
        """
        if not deleted_files:
            return

        logger.info(f"Detected {len(deleted_files)} deleted files, cleaning up...")

        try:
            self.memory.delete_by_file_paths(deleted_files)
            # Log first 5 files to avoid spam
            sample = ', '.join(deleted_files[:5])
            if len(deleted_files) > 5:
                sample += f" and {len(deleted_files) - 5} more..."
            logger.debug(f"Deleted files: {sample}")
        except Exception as e:
            logger.warning(f"Failed to cleanup deleted files: {e}")

    def index_project(self, root_path: str, force: bool = False):
        """Index all files in a project directory.
        
        Args:
            root_path: Absolute path to the project root directory.
            force: If True, re-index all files regardless of changes.
            
        Raises:
            FileNotFoundError: If root_path does not exist.
            NotADirectoryError: If root_path is not a directory.
        """
        if not os.path.exists(root_path):
            raise FileNotFoundError(f"Path does not exist: {root_path}")
        if not os.path.isdir(root_path):
            raise NotADirectoryError(f"Path is not a directory: {root_path}")

        existing_hashes = self._load_hashes() if not force else {}
        new_hashes = {}
        
        all_chunks = []
        file_count = 0
        skipped_count = 0
        
        print(f"🧠 Scanning {root_path}...", file=sys.stderr)
        
        for root, dirs, files in os.walk(root_path):
            # Defensive check: if we somehow entered an ignored directory
            # Handle both scenarios gracefully using Path.parts
            path_parts = Path(root).parts
            if any(self._is_ignored(p) for p in path_parts):
                continue

            # Filtering ignored directories
            dirs[:] = [d for d in dirs if not self._is_ignored(d)]
            
            for file in files:
                if file.startswith("."):
                    continue
                
                if self._is_ignored(file):
                    continue
                
                _, ext = os.path.splitext(file)
                if ext.lower() in self.ignore_extensions:
                    continue
                    
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, root_path)
                
                try:
                    file_size = os.path.getsize(file_path)
                    if file_size > self.max_index_file_size:
                        logger.debug("Skipping large file: %s (%d bytes > %d limit)", rel_path, file_size, self.max_index_file_size)
                        skipped_count += 1
                        continue

                    # simplistic binary check
                    with open(file_path, "r", encoding="utf-8", errors="strict") as f:
                        content = f.read()
                    
                    current_hash = self._compute_hash(content)
                    new_hashes[rel_path] = current_hash
                    
                    if not force and rel_path in existing_hashes and existing_hashes[rel_path] == current_hash:
                        skipped_count += 1
                        continue

                    # Progress Indicator (every 10 files)
                    file_count += 1
                    if file_count % 10 == 0:
                         print(f"   Indexed {file_count} files...", file=sys.stderr)
                        
                    chunks = self.chunker.chunk_file(rel_path, content)
                    all_chunks.extend(chunks)
                    
                    if len(all_chunks) >= 100:
                        self.memory.index_chunks(all_chunks)
                        all_chunks = []
                        
                except (UnicodeDecodeError, UnicodeError):
                    # Binary or non-UTF-8 file — skip silently
                    logger.debug("Skipping binary/non-UTF-8 file: %s", rel_path)
                except OSError as e:
                    logger.warning("Could not read %s: %s", rel_path, e)
                except Exception as e:
                    logger.warning("Unexpected error processing %s: %s", rel_path, e)
                    
        if all_chunks:
            self.memory.index_chunks(all_chunks)

        # Detect and clean up deleted files
        deleted_files = self._detect_deleted_files(existing_hashes, new_hashes)
        if deleted_files:
            self._cleanup_deleted_files(deleted_files)

        self._save_hashes(new_hashes)

        deleted_count = len(deleted_files) if deleted_files else 0
        print(f"✅ Indexed {file_count} files (Skipped {skipped_count} unchanged, Cleaned up {deleted_count} deleted).", file=sys.stderr)
