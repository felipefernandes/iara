# Optimization of CI Pipeline

## Problem
The current CI pipeline is slow (~8 minutes per run) due to:
1.  **Docker Build**: The `action.yml` builds the Docker image from source on every run (~4 mins).
2.  **Indexing/Analysis**: Deep learning dependencies (`torch`, `sentence-transformers`) take time to load, and indexing code is expensive (~4 mins).

## Solution
1.  **Pre-built Docker Image**: Publish the Docker image to GitHub Container Registry (GHCR) and update `action.yml` to pull it instead of building.
2.  **Dependency Caching**: Encourage users to cache the `.iara` directory (not easily doable inside a Docker action, but we can document it or switch to composite).
3.  **Lazy Loading**: Ensure heavy ML libraries are only imported when RAG is actually enabled/used.

## Proposal Metadata
- **Change ID**: `optimize-ci-pipeline`
- **Type**: `enhancement`
- **Status**: `proposal`

