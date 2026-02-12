import os
import logging
from typing import List, Optional
from iara.memory.interface import MemoryInterface, CodeChunk

logger = logging.getLogger(__name__)

class LanceDBMemory(MemoryInterface):
    """Memory implementation using LanceDB and local embeddings."""

    def __init__(self, persistence_path: str = ".iara/data/lancedb", embedding_model: str = "all-MiniLM-L6-v2"):
        try:
            import lancedb
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError(
                "RAG dependencies not installed. Please install with `pip install iara-reviewer[rag]`"
            )

        self.db = lancedb.connect(persistence_path)
        self.encoder = SentenceTransformer(embedding_model)
        self.table_name = "code_chunks"
        
        # Ensure table exists
        if self.table_name not in self.db.table_names():
            # Define schema explicitly or rely on auto-schema from data
            # For simplicity, we'll let it infer from the first batch of data,
            # but we need to handle the case where it's empty.
            pass

    def _embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        return self.encoder.encode(texts).tolist()

    def index_chunks(self, chunks: List[CodeChunk]):
        if not chunks:
            return

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
        if self.table_name in self.db.table_names():
            self.db.drop_table(self.table_name)
            logger.info("Cleared LanceDB memory.")
