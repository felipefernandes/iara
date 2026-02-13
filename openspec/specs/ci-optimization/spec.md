# ci-optimization Specification

## Purpose
TBD - created by archiving change optimize-ci-pipeline. Update Purpose after archive.
## Requirements
### Requirement: Pre-built Docker Execution
The system SHALL use a pre-built Docker image from a registry instead of building from source in CI pipelines, to reduce execution time.

#### Scenario: Build and Publish Image
Given a push to `main` or a tag release
When the `publish-docker.yml` workflow runs
Then a Docker image should be built and pushed to GHCR
And the image should be tagged with `latest` and the version tag (if applicable)

#### Scenario: Use Pre-built Image in Action
Given the `action.yml` configuration
When a user runs the action
Then it should use the pre-built Docker image from GHCR
And it should NOT build the image from source
And the execution time for the setup step should be significantly reduced

### Requirement: Efficient Indexing
The system SHALL optimize the indexing process to avoid redundant work and reduce resource usage.

#### Scenario: Incremental Indexing
Given a project with an existing `.iara/data` index
When `iara memory index` is run
Then it should only re-index files that have changed since the last index
And it should skip unchanged files
And it should remove chunks for deleted files

#### Scenario: Lazy Loading of Dependencies
Given the Iara CLI
When running non-RAG commands (e.g., `iara init`, `iara auth`)
Then it should NOT import heavy dependencies like `torch` or `sentence-transformers`
And the startup time should be fast (< 1s)

