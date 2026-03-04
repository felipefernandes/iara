- [x] **1. Update Default Configuration**
   - Add `"memory": { "dedup_threshold": 0.92 }` to `DEFAULT_CONFIG` in `iara/config.py`.

- [x] **2. Implement `_deduplicate_chunks` in Retriever**
   - Provide a basic implementation of `cosine_similarity` in `iara/memory/retriever.py` to avoid NumPy.
   - Implement `_deduplicate_chunks(self, chunks: List[CodeChunk], similarity_threshold: float) -> List[CodeChunk]`.
   - Ensure the logic safely skips if `self.memory` lacks an `encoder` property or if `encoder` is `None`.

- [x] **3. Update `retrieve_context_for_diff` in Retriever**
   - Query config for `memory.dedup_threshold` (default 0.92).
   - Fetch `max_chunks * 2` from memory index.
   - Run `_deduplicate_chunks` and slice to `max_chunks`.
   - Emit informative logger string (`🔍 RAG: X chunks → Y após dedup (Z redundantes removidos)`).

- [x] **4. Update Unit Tests**
   - Add unit tests for `_deduplicate_chunks` handling identical chunks, divergent chunks, partial matches, and disabled/fallback behaviors.
