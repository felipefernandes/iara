# Proposal: Implement Hybrid RAG Search with Reciprocal Rank Fusion

**Change ID**: `implement-hybrid-rag-search`
**Related Issue**: [#48](https://github.com/felipefernandes/iara-bot-reviewer/issues/48)
**Status**: Proposed
**Complexity**: 🟡 Medium

## Problem

The current RAG retrieval system uses **vector search only** (semantic similarity via embeddings). This creates two critical blind spots when retrieving context for code reviews:

1. **Exact name matches**: When a diff changes `calculate_risk_score()`, vector search may return semantically similar functions but miss the exact function being modified.
2. **Lexical precision**: Symbol names, API signatures, and specific identifiers often lack dense semantic neighborhoods, causing vector search to miss critical context.

**Current implementation** (`iara/memory/lancedb_store.py:81-84`):
```python
query_vector = self._embed([query])[0]
results = table.search(query_vector).limit(n_results).to_list()
```

This returns chunks that are "similar" but may not be "correct" for the specific symbols in the diff.

## Solution

Implement **hybrid search** combining:
- **Vector search** (semantic similarity) — broad understanding
- **Full-Text Search (FTS)** (lexical matching) — exact symbol matching
- **Reciprocal Rank Fusion (RRF)** — combines both rankings without parameter tuning

This approach is inspired by [Th0th's architecture](https://www.tabnews.com.br/S1LV4/como-reduzi-em-98-por-cento-o-uso-de-contexto-e-os-custos-de-ia-no-meu-workflow), which achieved 98% reduction in context usage through hybrid search.

### High-Level Design

1. **FTS indexing**: Create full-text index on `content` field when indexing chunks
2. **Dual search**: Execute vector and FTS searches in parallel (fetch 2x results from each)
3. **RRF fusion**: Merge results using Reciprocal Rank Fusion algorithm
4. **Graceful degradation**: Fall back to vector-only if FTS unavailable

## Impact

- **Better context retrieval**: Combines semantic understanding with exact matching
- **No parameter tuning**: RRF automatically balances both search modes
- **Backward compatible**: Falls back to vector-only if FTS not available
- **No breaking changes**: Public interface of `retrieve()` stays the same

## Acceptance Criteria

- [ ] LanceDB creates FTS index on `content` field during chunk indexing
- [ ] `retrieve()` executes both vector and FTS searches
- [ ] RRF algorithm correctly merges dual rankings
- [ ] Graceful fallback when FTS index doesn't exist
- [ ] Unit tests for RRF algorithm
- [ ] Integration tests for hybrid retrieval
- [ ] Performance remains acceptable (< 2x overhead vs vector-only)

## References

- [Th0th — Hybrid Semantic Search](https://www.tabnews.com.br/S1LV4/como-reduzi-em-98-por-cento-o-uso-de-contexto-e-os-custos-de-ia-no-meu-workflow)
- [LanceDB FTS Documentation](https://lancedb.github.io/lancedb/fts/)
- [Reciprocal Rank Fusion Paper](https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf)
- Current implementation: `iara/memory/lancedb_store.py`, `iara/memory/retriever.py`

## Out of Scope

- Custom weighting/tuning of vector vs FTS (RRF handles this)
- Multi-language FTS analyzers (use default English for now)
- Query expansion or synonym handling
- Caching of search results
