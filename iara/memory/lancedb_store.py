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

    def _rrf_merge(self, vec_results: List[dict], fts_results: List[dict], k: int = 60) -> List[dict]:
        """
        Merge two ranked result lists using Reciprocal Rank Fusion (RRF).

        Args:
            vec_results: Results from vector search (ranked list)
            fts_results: Results from FTS search (ranked list)
            k: RRF constant (default 60 from literature)

        Returns:
            Unified list sorted by combined RRF score (descending)
        """
        scores = {}
        all_items = {}

        # Calculate RRF scores from vector search ranking
        # Use standard RRF formula: 1 / (k + rank + 1)
        # Note: rank starts at 0 (enumerate), so we add 1 to align with standard RRF (ranks starting at 1)
        for rank, item in enumerate(vec_results):
            item_id = item.get("id")
            if item_id is None:
                continue  # Skip items without ID
            scores[item_id] = scores.get(item_id, 0) + 1 / (k + rank + 1)
            # Store first occurrence to avoid overwriting with duplicates
            if item_id not in all_items:
                all_items[item_id] = item

        # Calculate RRF scores from FTS search ranking
        for rank, item in enumerate(fts_results):
            item_id = item.get("id")
            if item_id is None:
                continue  # Skip items without ID
            scores[item_id] = scores.get(item_id, 0) + 1 / (k + rank + 1)
            # Store first occurrence to avoid overwriting with duplicates
            if item_id not in all_items:
                all_items[item_id] = item

        # Sort by RRF score (descending)
        sorted_ids = sorted(scores, key=scores.get, reverse=True)

        return [all_items[item_id] for item_id in sorted_ids]

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
            table = self.db.create_table(self.table_name, data)
            try:
                table.create_fts_index("content")
                logger.info("Created FTS index on 'content' field.")
            except Exception as e:
                logger.warning(f"Failed to create FTS index (will fall back to vector-only search): {e}")

        logger.info(f"Indexed {len(chunks)} chunks into LanceDB.")

    def retrieve(self, query: str, n_results: int = 5) -> List[CodeChunk]:
        self._ensure_initialized()
        if self.table_name not in self.db.table_names():
            return []

        query_vector = self._embed([query])[0]
        table = self.db.open_table(self.table_name)

        # Vector search (always works) - fetch 2x for better RRF fusion
        vec_results = table.search(query_vector).limit(n_results * 2).to_list()

        # Try hybrid search with FTS, fall back to vector-only if FTS unavailable
        try:
            # FTS search - fetch 2x for better RRF fusion
            fts_results = table.search(query, query_type="fts").limit(n_results * 2).to_list()

            # Merge using RRF and truncate to requested limit
            results = self._rrf_merge(vec_results, fts_results)[:n_results]

            logger.debug(
                f"Hybrid search: {len(vec_results)} vec + {len(fts_results)} fts "
                f"→ {len(results)} merged (RRF)"
            )
        except Exception as e:
            # Graceful fallback to vector-only search
            logger.warning(f"FTS search failed, falling back to vector-only: {e}")
            results = vec_results[:n_results]

        # Convert to CodeChunk objects
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

    def delete_by_file_paths(self, file_paths: List[str]):
        """Delete all chunks for the specified file paths using LanceDB's delete predicate.

        Args:
            file_paths: List of relative file paths to remove from the index.
        """
        if not file_paths:
            return

        self._ensure_initialized()
        if self.table_name not in self.db.table_names():
            return  # Nothing to delete

        table = self.db.open_table(self.table_name)

        # Build SQL-like predicate: file_path IN ('path1', 'path2', ...)
        # Escape single quotes for SQL safety
        escaped_paths = [path.replace("'", "''") for path in file_paths]
        path_list = ", ".join(f"'{p}'" for p in escaped_paths)
        predicate = f"file_path IN ({path_list})"

        try:
            deleted_count = table.delete(predicate)
            logger.info(f"Deleted {deleted_count} chunks from {len(file_paths)} files.")
        except Exception as e:
            logger.warning(f"Failed to delete chunks for {len(file_paths)} files: {e}")
