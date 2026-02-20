# Indexer Memory Optimization Architecture

## Context
When indexing a project, Iara scans the workspace recursively. Previously, each file was unconditionally read into memory, leading to memory bloat for non-code textual artifacts like bundles or data files that had not been excluded by extensions.

## Constraints
- Max 1GB RAM on typical target devices (Raspberry PIs, small containers).
- Must adhere to the Diet Code philosophy. 
- Fast, deterministic fail-safe.
- Provide sensible defaults but allow capable machines to exceed arbitrary low memory constraints based on user configuration.

## Proposed Design
We will introduce `max_index_file_size` in the `DEFAULT_CONFIG["review"]` dictionary inside `iara.config`, with a default value of `1048576` (1MB). 

During the `os.walk` iteration, before opening a file to verify binary/UTF-8 content or reading it into the `content` string, we will use `os.path.getsize(file_path)` to determine its size in a fast system-call manner. 

We will compare this size against the configured limit:
`config.get("review", {}).get("max_index_file_size", 1048576)`

If `file_size > configured_limit`:
- Log a debugging notice avoiding unnecessary noise.
- `continue` to the next file in the directory.

This guarantees we never hold an arbitrary large blob string in memory, but puts the control directly in the user's hand (`.iara.json`).

## Trade-offs
**Skipping over Streaming:**
We could implement a streaming hash digest reading chunks of 8KB, but the files we skip are usually huge textual files (like 10MB generated JS files or localization files map) which would be problematic to pass cleanly through AST chunking regardless of changes.
By directly skipping large files, we immediately mitigate OOM exceptions and latency, without writing complex file buffered parsers.
