# Memory Efficiency

## MODIFIED Requirements

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
