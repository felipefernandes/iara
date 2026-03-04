# Proposal: Implement Semantic Deduplication in Retriever

## Why
At present, Iara retrieves up to 3 context chunks from LanceDB and injects them into the system prompt for context, without checking if they overlap significantly or are redundant. In codebases with dense interconnections, these chunks can be extremely similar, leading to bloated prompts and wasting tokens on duplicate information. Inspired by the `semantic_dedup` logic from Th0th, this proposal will eliminate redundant chunks through localized cosine similarity before injecting them into the system prompt.

## Proposed Change
We introduce a semantic deduplication step in the `Retriever` module:
- `iara/config.py` will include a new setting `memory.dedup_threshold` (default `0.92`).
- `Retriever` will expose a `_deduplicate_chunks` method filtering retrieved items by cosine similarity.
- `Retriever.retrieve_context_for_diff` will be updated to fetch `max_chunks * 2` from memory, run deduplication, and limit to `max_chunks`.
- Informational logging will be emitted to surface how many redundant chunks were removed.
- In environments or memory implementations without an `encoder` accessible (e.g., RAG disabled), the deduplication will be silently skipped.

## Impact
- **Token Efficiency**: Potential 30-50% reduction of wasted context tokens.
- **Diversity**: Allows discovering varied context instead of redundant function copies.
