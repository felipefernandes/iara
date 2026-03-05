# Design: Hybrid RAG Search with RRF

## Overview

This design introduces **hybrid search** combining vector similarity (semantic) and full-text search (lexical) using Reciprocal Rank Fusion (RRF) to merge results. The goal is to improve context retrieval for code reviews by capturing both semantic meaning and exact symbol matches.

## Architecture

### Current State

```
diff → Retriever._extract_symbols_from_diff()
     → query = " ".join(symbols)
     → LanceDBMemory.retrieve(query)
         → embed query → vector search → results
```

**Problem**: Vector search alone misses exact symbol matches, returning "similar" but not "correct" context.

### Proposed State

```
diff → Retriever._extract_symbols_from_diff()
     → query = " ".join(symbols)
     → LanceDBMemory.retrieve(query)
         ├─→ Vector Search (semantic) → vec_results
         ├─→ FTS Search (lexical)     → fts_results
         └─→ RRF Merge → combined_results
```

**Benefit**: Combines broad semantic understanding with precise lexical matching.

## Key Design Decisions

### 1. Where to Implement Hybrid Search

**Decision**: Implement hybrid logic **inside `LanceDBMemory.retrieve()`**, not in `Retriever`.

**Rationale**:
- `LanceDBMemory` owns the search logic and table access
- `Retriever` just calls `retrieve()` — no awareness of search internals needed
- Keeps interface unchanged (`retrieve(query, n_results)`)
- Makes hybrid search transparent to consumers

**Alternative Considered**: Implementing in `Retriever.retrieve_context_for_diff()`
- **Rejected**: Would couple retriever to LanceDB-specific features
- **Rejected**: Harder to test in isolation

### 2. FTS Index Creation

**Decision**: Create FTS index during `index_chunks()` right after table creation.

**Approach**:
```python
if self.table_name in self.db.table_names():
    table = self.db.open_table(self.table_name)
    table.add(data)
else:
    table = self.db.create_table(self.table_name, data)
    table.create_fts_index("content")  # NEW
    logger.info("Created FTS index on 'content' field.")
```

**Rationale**:
- One-time cost during indexing (acceptable)
- No runtime overhead for retrieval
- LanceDB persists FTS index to disk

**Edge Case**: If table exists and FTS was never created (upgrading users):
- FTS search will fail → graceful fallback to vector-only
- Users can re-index to get FTS benefits

**Alternative Considered**: Create index lazily on first `retrieve()` call
- **Rejected**: Adds complexity to retrieval path
- **Rejected**: May cause race conditions if multiple retrievals happen simultaneously

### 3. Reciprocal Rank Fusion Algorithm

**Decision**: Use standard RRF with k=60 (no tuning).

**Algorithm**:
```python
def _rrf_merge(self, vec_results, fts_results, k=60):
    scores = {}
    for rank, item in enumerate(vec_results):
        scores[item["id"]] = scores.get(item["id"], 0) + 1 / (k + rank + 1)
    for rank, item in enumerate(fts_results):
        scores[item["id"]] = scores.get(item["id"], 0) + 1 / (k + rank + 1)

    all_items = {item["id"]: item for item in vec_results + fts_results}
    sorted_ids = sorted(scores, key=scores.get, reverse=True)
    return [all_items[id] for id in sorted_ids]
```

**Rationale**:
- **k=60** is the standard value from RRF literature (Cormack et al.)
- No parameter tuning required (key RRF advantage)
- Handles duplicates automatically (IDs appearing in both searches get higher scores)

**Alternative Considered**: Weighted linear combination (e.g., 0.6*vector + 0.4*fts)
- **Rejected**: Requires tuning weights (adds complexity, no clear "right" answer)
- **Rejected**: RRF proven effective in production systems (Elasticsearch, etc.)

### 4. Graceful Fallback Strategy

**Decision**: Wrap FTS search in try/except, fall back to vector-only on failure.

**Implementation**:
```python
def retrieve(self, query: str, n_results: int = 5):
    query_vector = self._embed([query])[0]
    table = self.db.open_table(self.table_name)

    # Vector search (always works)
    vec_results = table.search(query_vector).limit(n_results * 2).to_list()

    # FTS search (may fail if index doesn't exist)
    try:
        fts_results = table.search(query, query_type="fts").limit(n_results * 2).to_list()
        results = self._rrf_merge(vec_results, fts_results)[:n_results]
        logger.debug(f"Hybrid search: {len(vec_results)} vec + {len(fts_results)} fts → {len(results)} merged")
    except Exception as e:
        logger.warning(f"FTS search failed, falling back to vector-only: {e}")
        results = vec_results[:n_results]

    return [self._build_chunk(r) for r in results]
```

**Rationale**:
- **Robustness**: System never breaks even if FTS unavailable
- **Upgrade path**: Old indexes without FTS continue working
- **Debugging**: Logging shows when fallback happens

**Trade-off**: Users won't know FTS is missing unless they check logs
- Acceptable: System still works, just not optimal
- Can add metric/warning in future if needed

### 5. Search Result Limit Strategy

**Decision**: Fetch **2x n_results** from each search, then truncate after RRF merge.

**Rationale**:
- More candidates → better RRF fusion quality
- Slight overhead (2x API calls) but still fast
- Ensures we don't miss good results that rank differently in each search

**Example**: User requests n_results=5
- Vector search: fetch 10 results
- FTS search: fetch 10 results
- RRF merge: combine and re-rank all ~20 unique items
- Return: top 5 from merged ranking

**Alternative Considered**: Fetch exactly n_results from each
- **Rejected**: RRF may be dominated by one search mode if candidate pool too small
- **Rejected**: Better to over-fetch then truncate

### 6. FTS Query Strategy

**Decision**: Use raw query string for FTS, same as vector query.

**Current behavior**: `Retriever` builds query from extracted symbols:
```python
symbols = self._extract_symbols_from_diff(diff)
query = " ".join(list(symbols)[:10])
```

**Proposed**: Pass this exact query to both vector and FTS searches.

**Rationale**:
- Simplicity: no query transformation needed
- Symbol names (identifiers) work well with FTS
- Consistent semantics between both search modes

**Future Enhancement** (out of scope for now):
- Could use boolean FTS queries (e.g., `calculate_risk_score OR risk OR score`)
- Could apply different tokenization for FTS
- Defer until we have data showing current approach insufficient

## Performance Considerations

### Latency

**Impact**: Hybrid search adds ~50-100% overhead vs vector-only
- Vector embedding: ~10-30ms
- Vector search: ~5-20ms
- FTS search: ~5-15ms (fast, indexed)
- RRF merge: <1ms (in-memory)

**Total**: ~20-50ms → ~30-80ms (still acceptable for code review context)

### Storage

**Impact**: FTS index adds ~10-30% to disk usage
- Vector index: dominant cost (768-dim embeddings)
- FTS index: compressed text index, relatively small

**Example**: 1000 chunks × 500 chars avg = ~500KB text → ~50-150KB FTS index

### Memory

**Impact**: Minimal (FTS index stays on disk, loaded on-demand by LanceDB)

## Testing Strategy

### Unit Tests

1. **RRF Algorithm Tests** (`test_lancedb_store.py`)
   - Identical rankings → preserve order
   - Disjoint rankings → interleave fairly
   - Overlapping rankings → boost duplicates
   - Empty inputs → handle gracefully

2. **Hybrid Retrieval Tests**
   - Mock both vector and FTS searches
   - Verify both are called
   - Verify RRF merge applied
   - Verify results limited to n_results

3. **Fallback Tests**
   - Mock FTS failure → verify vector-only fallback
   - Verify logging when fallback happens

### Integration Tests

1. **End-to-End Retrieval** (`test_retriever.py`)
   - Index real code chunks
   - Query with symbol names
   - Verify hybrid results more relevant than vector-only

2. **Upgrade Path**
   - Load old index without FTS
   - Verify graceful fallback works

## Risks and Mitigations

### Risk 1: FTS Quality Issues

**Risk**: FTS may return too many irrelevant results (over-matching)
**Mitigation**: RRF balances with vector search — bad FTS results rank lower
**Monitoring**: Can log FTS result quality metrics in future

### Risk 2: LanceDB API Changes

**Risk**: LanceDB FTS API may change in future versions
**Mitigation**: Try/except ensures system stays stable, version pinning in requirements
**Monitoring**: Unit tests will catch API breakage

### Risk 3: Performance Regression

**Risk**: 2x search overhead may be too slow for large indexes
**Mitigation**: Benchmark shows <100ms overhead acceptable for code review use case
**Monitoring**: Can add retrieval latency metrics if needed

## Future Enhancements (Out of Scope)

1. **Query Expansion**: Expand symbol queries with synonyms/related terms
2. **Custom FTS Analyzers**: Language-specific tokenization (Python, C#, etc.)
3. **Result Caching**: Cache frequent queries (e.g., common symbols)
4. **Adaptive Weighting**: Learn optimal RRF k value from feedback
5. **Multi-Field FTS**: Index file_path, metadata separately for richer matching

## References

- [Reciprocal Rank Fusion Paper](https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf)
- [LanceDB FTS Docs](https://lancedb.github.io/lancedb/fts/)
- [Th0th Hybrid Search Case Study](https://www.tabnews.com.br/S1LV4/como-reduzi-em-98-por-cento-o-uso-de-contexto-e-os-custos-de-ia-no-meu-workflow)
