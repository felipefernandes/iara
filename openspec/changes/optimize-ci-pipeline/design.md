# Design: CI Pipeline Optimization

## Architecture Changes

### 1. Docker Image Distribution
- **Current**: Image built from `Dockerfile` at runtime by GitHub Actions runner.
- **New**: 
    - Workflow `publish-docker.yml` builds and pushes `ghcr.io/felipefernandes/iara-reviewer:latest` (and semantic tags) on push to `main` and tags.
    - `action.yml` refers to `docker://ghcr.io/felipefernandes/iara-reviewer:latest` (or pinned version).

### 2. Action Implementation
- **Current**: `runs: using: 'docker', image: 'Dockerfile'`
- **New**: `runs: using: 'docker', image: 'docker://ghcr.io/felipefernandes/iara-reviewer:v1'` (pinned to major version for stability, or specific tag).

### 3. Impact Analysis
- **Build Time**: Reduced from ~4m to seconds (image pull).
- **Maintenance**: Need to ensure `publish-docker.yml` is reliable.
- **Security**: Image is public; ensure no secrets are baked in (codebase is public anyway).

## RAG Optimization
- **Lazy Imports**: Modify `iara/memory/lancedb_store.py` to defer imports of `sentence_transformers` and `torch` until `__init__` is called, OR ensure `__init__` is only called when RAG is enabled.
- **Incremental Indexing**: (Future) Check file hashes before re-indexing.
