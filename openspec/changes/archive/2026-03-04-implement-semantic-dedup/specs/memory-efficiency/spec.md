# Retriever Semantic Deduplication Specification

## Context
The `Retriever` fetches code chunks from the RAG store to supply to the LLM system prompt. Since the model relies on chunks of context, fetching extremely similar code bits causes the prompt context to become saturated with redundant information.

## ADDED Requirements

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
