import os
import logging
from typing import List, Optional
from iara.memory.interface import MemoryInterface, CodeChunk

logger = logging.getLogger(__name__)

class LanceDBMemory(MemoryInterface):
    """Memory implementation using LanceDB and local embeddings."""

    def __init__(self, persistence_path: str = ".iara/data/lancedb", embedding_model: str = "all-MiniLM-L6-v2"):
        self.persistence_path = persistence_path
        self.embedding_model_name = embedding_model
        self.db = None
        self.encoder = None
        self.table_name = "code_chunks"

    def _ensure_initialized(self):
        """Lazy load dependencies and model."""
        if self.db is not None and self.encoder is not None:
            return

        try:
            import lancedb
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError(
                "RAG dependencies not installed. Please install with `pip install iara-reviewer[rag]`"
            )

        if self.db is None:
            self.db = lancedb.connect(self.persistence_path)
            
        if self.encoder is None:
            self.encoder = SentenceTransformer(self.embedding_model_name)

        # Ensure table exists (check only once on init)
        # For simplicity, we'll imply it's handled by lancedb or our logic below
        pass

    def _embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        self._ensure_initialized()
        return self.encoder.encode(texts).tolist()

    def index_chunks(self, chunks: List[CodeChunk]):
        if not chunks:
            return

        self._ensure_initialized()

        data = []
        texts_to_embed = [chunk.content for chunk in chunks]
        vectors = self._embed(texts_to_embed)

        for chunk, vector in zip(chunks, vectors):
            data.append({
                "id": chunk.id,
                "vector": vector,
                "content": chunk.content,
                "file_path": chunk.file_path,
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
                "type": chunk.type,
                "metadata": chunk.metadata or {}
            })

        if self.table_name in self.db.table_names():
            table = self.db.open_table(self.table_name)
            table.add(data)
        else:
            self.db.create_table(self.table_name, data)
        
        logger.info(f"Indexed {len(chunks)} chunks into LanceDB.")

    def retrieve(self, query: str, n_results: int = 5) -> List[CodeChunk]:
        self._ensure_initialized()
        if self.table_name not in self.db.table_names():
            return []

        query_vector = self._embed([query])[0]
        table = self.db.open_table(self.table_name)
        
        results = table.search(query_vector).limit(n_results).to_list()
        
        chunks = []
        for r in results:
            chunks.append(CodeChunk(
                id=r["id"],
                content=r["content"],
                file_path=r["file_path"],
                start_line=r["start_line"],
                end_line=r["end_line"],
                type=r["type"],
                metadata=r["metadata"]
            ))
            
        return chunks

    def clear(self):
        self._ensure_initialized()
        if self.table_name in self.db.table_names():
            self.db.drop_table(self.table_name)
            logger.info("Cleared LanceDB memory.")
