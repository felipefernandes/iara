# memory-efficiency Specification

## Purpose
TBD - created by archiving change optimize-indexer-memory. Update Purpose after archive.
## Requirements
### Requirement: Configurable Max File Size for Indexing
The system extracts AST and line blocks as chunks when indexing repository files, but MUST skip parsing very large files completely based on a configurable threshold.

#### Scenario: Attempting to index a file that exceeds the default configured maximum size limit
Given a repository containing a file over the default `max_index_file_size` (1MB).
When the index runs on the project root path.
Then the system skips the file completely without allocating memory to read its content.
And a debug level message is logged about avoiding the oversized file.

#### Scenario: User customizes the limit in .iara.json to allow larger files
Given a repository containing a 5MB file.
And the user sets `review.max_index_file_size` to `10000000` (10MB) in `.iara.json`.
When the index runs on the project root path.
Then the system successfully reads the 5MB file into memory and indexes its chunks.

### Requirement: Eliminate redundant chunks from system prompt
The retriever MUST apply a similarity-based deduplication filter to retrieved chunks, removing redundant context blocks over a given threshold.

#### Scenario: RAG retrieval fetches duplicative records
- **Given** a diff query matching multiple redundant modules
- **When** the `memory.encoder` outputs a matrix comparing `chunk.content`
- **And** two chunks possess a cosine similarity greater than `memory.dedup_threshold` (default 0.92)
- **Then** the redundant chunks MUST be discarded
- **And** a log string MUST be emitted reflecting stats

#### Scenario: Fallback missing encoder
- **Given** no valid RAG embedding model or missing `encoder` property
- **When** `_deduplicate_chunks` encounters missing dependencies
- **Then** all chunks are kept and the deduplication returns no change

### Requirement: Language-Specific Smart Chunking
The indexer MUST use language-specific strategies (AST or regex) to chunk code accurately by logical boundaries (functions, classes) instead of falling back to raw line chunks prematurely.

#### Scenario: Python chunks using AST
- **Given** a `.py` file
- **When** the file is indexed
- **Then** it is chunked using Python's AST parser to extract functions and classes

#### Scenario: JavaScript and TypeScript chunks using Regex
- **Given** a `.js` or `.ts` file
- **When** the file is indexed
- **Then** it is chunked using Regex to extract functions, classes, and arrow functions
- **And** the chunks represent complete logical blocks rather than arbitrary lines

#### Scenario: C# chunks using Regex
- **Given** a `.cs` file
- **When** the file is indexed
- **Then** it is chunked using Regex to extract methods and classes
- **And** the chunks represent complete logical blocks

#### Scenario: Fallback chunking for unsupported languages
- **Given** a file with an unsupported extension (e.g., `.txt`, `.md`)
- **When** the file is indexed
- **Then** it falls back to a plain text chunking strategy of maximum 100 lines per chunk

