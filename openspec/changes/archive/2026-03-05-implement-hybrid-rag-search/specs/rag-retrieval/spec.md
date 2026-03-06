# rag-retrieval Specification Delta

## ADDED Requirements

### Requirement: Hybrid Search with Vector and Full-Text Search
When retrieving context chunks from memory, the system MUST use hybrid search combining vector similarity (semantic) and full-text search (lexical) to maximize retrieval precision and recall. This ensures both semantic understanding and exact symbol matching for code context.

- **Dual Search Execution:** Both vector search and FTS search must be executed in parallel, each fetching 2x the requested result count to provide sufficient candidates for fusion.
- **Reciprocal Rank Fusion (RRF):** Results from both searches must be merged using the RRF algorithm with k=60, which combines rankings without requiring manual weight tuning.
- **Result Truncation:** After RRF fusion, the combined results must be truncated to the originally requested `n_results` limit.

#### Scenario: Retrieving context with exact symbol match
Given a code chunk index containing a function `calculate_risk_score()`
And the function is indexed with both vector embeddings and FTS index
When a query is made for "calculate_risk_score"
Then the vector search returns semantically similar functions
And the FTS search returns exact symbol matches including `calculate_risk_score()`
And RRF fusion ranks the exact match higher due to dual presence
And the exact function appears in the top results

#### Scenario: Retrieving context with semantic similarity only
Given a code chunk index containing risk-related functions
And a query for "financial risk assessment"
When the query does not match any exact symbols
Then the vector search returns semantically relevant chunks
And the FTS search may return few or no results
And RRF fusion preserves vector search ranking
And semantically relevant chunks are returned

#### Scenario: Hybrid search combines both modes
Given an index with functions `calculate_risk()`, `assess_risk()`, and `risk_score()`
And a query for "risk calculation"
When hybrid search is executed
Then vector search ranks by semantic similarity
And FTS search ranks by term overlap ("risk")
And RRF fusion boosts chunks appearing in both rankings
And the result set combines semantic and lexical relevance

### Requirement: FTS Index Creation During Indexing
When code chunks are indexed into LanceDB, a Full-Text Search (FTS) index MUST be created on the `content` field to enable lexical search. This index enables fast text matching for symbol names and code patterns.

- **Index Creation Timing:** FTS index must be created immediately after table creation (for new tables) to ensure availability for all subsequent retrievals.
- **Persistence:** The FTS index is persisted by LanceDB and does not need recreation on restart.
- **Logging:** Index creation must be logged at INFO level to confirm successful setup.

#### Scenario: Creating FTS index for new table
Given no existing LanceDB table for code chunks
When code chunks are indexed for the first time
Then a new table is created with the chunks
And an FTS index is created on the "content" field
And a log message confirms "Created FTS index on 'content' field"

#### Scenario: Adding chunks to existing table
Given an existing LanceDB table with FTS index already created
When new code chunks are added to the table
Then chunks are appended to the existing table
And the FTS index is automatically updated by LanceDB
And no redundant index creation is attempted

### Requirement: Graceful Fallback to Vector-Only Search
When Full-Text Search fails or is unavailable, the system MUST gracefully fall back to vector-only search to ensure retrieval always succeeds. This handles upgrade scenarios where old indexes lack FTS or when FTS encounters errors.

- **Error Handling:** FTS search failures must be caught and logged as warnings, not errors that halt retrieval.
- **Fallback Behavior:** When FTS fails, the system must use vector search results directly without RRF fusion.
- **Logging:** Fallback events must be logged at WARNING level with the specific error reason.

#### Scenario: FTS index missing (upgrade scenario)
Given a LanceDB table created before FTS support
And the table has no FTS index on the "content" field
When a hybrid search is attempted
Then the FTS search raises an exception
And the system logs a warning about fallback to vector-only
And vector search results are returned successfully
And retrieval does not fail

#### Scenario: FTS search error during retrieval
Given a LanceDB table with corrupted FTS index
When a hybrid search query is executed
Then the FTS search raises an exception during execution
And the error is caught and logged as a warning
And vector search proceeds normally
And results are returned from vector search only

#### Scenario: Successful hybrid search (no fallback)
Given a LanceDB table with valid FTS index
When a hybrid search is executed
Then both vector and FTS searches complete successfully
And no fallback warning is logged
And RRF fusion combines both result sets

### Requirement: RRF Algorithm Implementation
The Reciprocal Rank Fusion (RRF) algorithm MUST correctly merge two ranked result lists (vector and FTS) into a single unified ranking. This algorithm combines independent rankings without requiring weight calibration.

- **Scoring Formula:** Each item's RRF score is computed as sum of `1 / (k + rank + 1)` across all result lists where it appears, with k=60.
- **Deduplication:** Items appearing in both result lists must have their scores combined (summed), not duplicated in output.
- **Ranking:** Final results must be sorted by RRF score in descending order (highest score first).

#### Scenario: RRF merges identical rankings
Given vector search results [A, B, C] (ranked in order)
And FTS search results [A, B, C] (same ranking)
When RRF fusion is applied with k=60
Then item A appears in both lists and receives score 1/(60+1) + 1/(60+1) = ~0.0328
And item B receives score 1/(60+2) + 1/(60+2) = ~0.0323
And the final ranking remains [A, B, C]
And no duplicates appear in output

#### Scenario: RRF merges disjoint rankings
Given vector search results [A, B, C]
And FTS search results [D, E, F]
When RRF fusion is applied
Then items A, B, C receive scores from vector ranking only
And items D, E, F receive scores from FTS ranking only
And final ranking interleaves both lists based on score
And all 6 unique items appear in output

#### Scenario: RRF boosts items in both rankings
Given vector search results [A, B, C, D]
And FTS search results [B, A, E, F]
When RRF fusion is applied
Then item A appears 1st in vector and 2nd in FTS → high combined score
And item B appears 2nd in vector and 1st in FTS → high combined score
And items A and B rank higher than C, D, E, F in final output
And items appearing in only one list rank lower

#### Scenario: RRF handles empty inputs
Given vector search results []
And FTS search results [A, B, C]
When RRF fusion is applied
Then the output contains only FTS results [A, B, C]
And no error is raised

## MODIFIED Requirements

None — this is a new capability being added.

## REMOVED Requirements

None — no existing requirements are being removed.
