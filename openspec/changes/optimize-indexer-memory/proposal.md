# Optimize Indexer Memory

## Overview
Optimize memory usage during project indexing by skipping excessively large files before attempting to read them entirely into memory. This prevents high memory consumption and potential Out Of Memory (OOM) crashes in lightweight environments (like Raspberry Pi or constrained CI runners).

## Motivation
Currently, `iara.memory.indexer.Indexer` reads the entire content of every file into memory using `f.read()` before evaluating if the file has changed (via hashing) and before chunking. For very large files (e.g., generated code, large textual data files, minified bundles), this causes a significant spike in memory usage, which goes against the Diet Code manifesto and the hardware constraints of the project.

Since not all users run Iara on highly constrained environments like a Raspberry Pi, this threshold will be fully configurable via `.iara.json`, avoiding unnecessary constraints for users running in capable environments.

## Scope
### In Scope
- Introduction of a configurable maximum file size limit for indexing (defaulting to 1MB).
- Adding the parameter `max_index_file_size` under the `review` section in `.iara.json`'s configuration schema.
- Checking the file size of candidate files before opening and reading them.
- Skipping files that exceed the configured threshold and logging the action.

### Out of Scope
- Streaming hash computation for large files (we simply skip them for now to maintain simplicity).
- Incremental parsing of the AST.
