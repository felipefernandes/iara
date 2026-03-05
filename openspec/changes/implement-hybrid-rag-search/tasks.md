# Tasks: Implement Hybrid RAG Search

All tasks should be completed in order. Mark with `[x]` when done.

## Implementation Tasks

- [x] **Add FTS index creation in `LanceDBMemory.index_chunks()`**
  - Modify `iara/memory/lancedb_store.py` to call `table.create_fts_index("content")` after table creation
  - Handle case where table already exists (check if FTS index exists before creating)
  - Add logging when FTS index is created successfully

- [x] **Implement `_rrf_merge()` helper in `LanceDBMemory`**
  - Add private method to combine two result sets using Reciprocal Rank Fusion
  - Default k=60 parameter (standard RRF constant)
  - Handle edge cases: empty results, duplicate IDs across searches
  - Return unified list sorted by combined RRF score

- [x] **Modify `LanceDBMemory.retrieve()` for hybrid search**
  - Execute vector search with limit=n_results*2 (to get more candidates)
  - Execute FTS search with same limit
  - Merge results using `_rrf_merge()`
  - Truncate final list to n_results
  - Add try/except for FTS failures → graceful fallback to vector-only

- [x] **Add unit tests for RRF algorithm**
  - Test `_rrf_merge()` with two identical rankings (should preserve order)
  - Test with disjoint rankings (both should be represented)
  - Test with overlapping rankings (duplicates removed, scores combined)
  - Test with empty inputs (returns empty list)
  - Test k parameter variations

- [x] **Add integration tests for hybrid retrieval**
  - Mock LanceDB table with both vector and FTS search methods
  - Verify both searches are called when FTS available
  - Verify fallback to vector-only when FTS raises exception
  - Verify final results combine both search modes

- [x] **Update existing retriever tests**
  - Ensure `test_retriever.py` still passes with hybrid search
  - Update mocks if needed to support dual search paths
  - Verify deduplication logic works with hybrid results

- [x] **Add logging for hybrid search diagnostics**
  - Log when FTS index is missing (fallback to vector-only)
  - Log result counts from vector vs FTS searches (debug level)
  - Log when RRF merges results (info level with counts)

## Validation Tasks

- [x] **Run full test suite**
  - Execute `pytest tests/` and ensure all tests pass
  - Pay special attention to `test_lancedb_store.py` and `test_retriever.py`

- [ ] **Manual testing with real codebase**
  - Index a real codebase (e.g., iara-bot-reviewer itself)
  - Create test diffs with exact function names
  - Verify hybrid search returns more relevant results than vector-only
  - Compare retrieval quality before/after

- [ ] **Performance benchmark**
  - Measure retrieval latency before/after hybrid search
  - Ensure overhead is < 2x (acceptable for better quality)
  - Document findings in PR or issue comment

## Documentation Tasks

- [ ] **Update RAG documentation**
  - Document hybrid search in README or docs/
  - Explain FTS index creation and RRF fusion
  - Note graceful degradation behavior

- [ ] **Update CHANGELOG**
  - Add entry for hybrid search feature
  - Note performance and quality improvements

## Dependencies

- Tasks 1-3 are sequential (must complete in order)
- Tasks 4-6 can be done in parallel after task 3
- Task 7 should be done last (requires all implementation complete)
- Validation tasks can run in parallel after implementation complete
