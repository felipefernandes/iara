import re
from typing import List, Set
from iara.memory.interface import MemoryInterface, CodeChunk

class Retriever:
    """Retrieves relevant context from memory based on code changes."""

    def __init__(self, memory: MemoryInterface):
        self.memory = memory

    def retrieve_context_for_diff(self, diff: str, max_chunks: int = 5) -> str:
        """
        Analyzes the diff, extracts key symbols, and retrieves relevant context.
        Returns a formatted string suitable for LLM injection.
        """
        symbols = self._extract_symbols_from_diff(diff)
        if not symbols:
            return ""

        # Construct a query from symbols
        # TODO: Improve this query strategy. Maybe query per symbol?
        query = " ".join(list(symbols)[:10])  # Limit query length
        
        chunks = self.memory.retrieve(query, n_results=max_chunks)
        if not chunks:
            return ""
            
        return self._format_chunks(chunks)

    def _extract_symbols_from_diff(self, diff: str) -> Set[str]:
        """
        Extracts changed function/class names and key identifiers from the diff.
        This is a heuristic approach using regex.
        """
        symbols = set()
        
        # Pattern for Python function/class definitions in diff headers
        # e.g., "@@ -10,5 +10,5 @@ def my_function():"
        header_pattern = re.compile(r"@@.*?@@\s*(?:def|class)\s+([a-zA-Z_][a-zA-Z0-9_]*)")
        
        # Pattern for added/modified lines
        # Looking for function calls or usage: `some_function(...)` or `SomeClass`
        code_pattern = re.compile(r"^[+].*?([a-zA-Z_][a-zA-Z0-9_]{3,})")

        for line in diff.splitlines():
            # Check diff headers
            match_header = header_pattern.search(line)
            if match_header:
                symbols.add(match_header.group(1))
                continue
            
            # Check added lines (ignore removed lines for context retrieval usually)
            if line.startswith("+") and not line.startswith("+++"):
                # Clean line (remove +, whitespace)
                content = line[1:].strip()
                # Simple tokenization to find potential symbols
                # We skip standard keywords to reduce noise
                tokens = re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]{3,}\b", content)
                for token in tokens:
                   if token not in ["self", "import", "return", "from", "def", "class", "print", "None", "True", "False"]:
                       symbols.add(token)

        return symbols

    def _format_chunks(self, chunks: List[CodeChunk]) -> str:
        """Formats code chunks into a context string."""
        formatted = ["### 🧠 Project Context (Retrieved from Memory)"]
        
        for chunk in chunks:
            formatted.append(f"\n**File**: `{chunk.file_path}` (Lines {chunk.start_line}-{chunk.end_line})")
            if chunk.type == "function" or chunk.type == "class":
                 formatted.append(f"*{chunk.type.capitalize()}*: `{chunk.metadata.get('name', 'N/A')}`")
            
            formatted.append("```python")
            formatted.append(chunk.content)
            formatted.append("```")
            
        return "\n".join(formatted)
