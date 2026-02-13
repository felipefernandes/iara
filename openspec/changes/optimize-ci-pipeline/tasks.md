# Tasks

1. [ ] **Docker Optimization**
    - [x] Create `.github/workflows/publish-docker.yml` to build and push to GHCR.
    - [x] Update `action.yml` to use `docker://ghcr.io/felipefernandes/iara-reviewer:latest`.
    - [ ] Verify action runs successfully with pre-built image.

2. [ ] **Indexing Optimization**
    - [ ] Modify `iara/memory/indexer.py` to implement incremental indexing (hash/mtime check).
    - [ ] Update `iara/cli.py` to support incremental indexing flag (or make it default).

3. [ ] **Performance Tuning**
    - [x] Refactor imports in `iara/memory/lancedb_store.py` to lazy load `torch`/`transformers`.
    - [x] Verify startup time of `iara --help` is < 1s.
