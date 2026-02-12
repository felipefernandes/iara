from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class CodeChunk:
    """Represents a chunk of code or documentation."""
    id: str
    content: str
    file_path: str
    start_line: int
    end_line: int
    type: str  # 'function', 'class', 'markdown', etc.
    metadata: Optional[Dict[str, Any]] = None

class MemoryInterface(ABC):
    """Abstract base class for Iara's memory system."""

    @abstractmethod
    def index_chunks(self, chunks: List[CodeChunk]):
        """Index a list of code chunks into the vector store."""
        pass

    @abstractmethod
    def retrieve(self, query: str, n_results: int = 5) -> List[CodeChunk]:
        """Retrieve relevant code chunks based on a query."""
        pass

    @abstractmethod
    def clear(self):
        """Clear all data from the memory."""
        pass
