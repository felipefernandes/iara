import re
import logging
import math
from typing import List, Set
from iara.memory.interface import MemoryInterface, CodeChunk
from iara.config import load_config

logger = logging.getLogger(__name__)

def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    mag1 = math.sqrt(sum(a * a for a in vec1))
    mag2 = math.sqrt(sum(b * b for b in vec2))
    if mag1 == 0 or mag2 == 0:
        return 0.0
    return dot_product / (mag1 * mag2)

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
        
        config = load_config()
        dedup_threshold = config.get("memory", {}).get("dedup_threshold", 0.92)
        
        fetch_chunks = max_chunks * 2
        chunks = self.memory.retrieve(query, n_results=fetch_chunks)
        if not chunks:
            return ""
            
        chunks = self._deduplicate_chunks(chunks, similarity_threshold=dedup_threshold)
        chunks = chunks[:max_chunks]
            
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

    def _deduplicate_chunks(self, chunks: List[CodeChunk], similarity_threshold: float = 0.92) -> List[CodeChunk]:
        """
        Removes semantically redundant chunks using cosine similarity.
        Safely skips if no encoder is available.
        """
        if len(chunks) <= 1:
            return chunks

        # Try to access encoder, handling cases where it's not present or none
        encoder = getattr(self.memory, "encoder", None)
        if encoder is None:
            return chunks

        try:
            contents = [c.content for c in chunks]
            embeddings = encoder.encode(contents)
            if hasattr(embeddings, 'tolist'):
                embeddings = embeddings.tolist()
        except Exception as e:
            logger.warning(f"Semantic dedup failed during encoding: {e}")
            return chunks

        kept = []
        kept_indices = []
        
        for i, chunk in enumerate(chunks):
            is_redundant = False
            for j in range(len(kept)):
                cos_sim = _cosine_similarity(embeddings[i], embeddings[kept_indices[j]])
                if cos_sim > similarity_threshold:
                    is_redundant = True
                    break
            if not is_redundant:
                kept.append(chunk)
                kept_indices.append(i)
                
        if len(kept) < len(chunks):
            logger.info(f"🔍 RAG: {len(chunks)} chunks -> {len(kept)} after dedup ({len(chunks) - len(kept)} redundant removed)")
            
        return kept


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
