# Pre-built Docker Image for CI/CD

## Motivation
This design document describes the architectural changes required to shift from installing the Iara bot in a raw `ubuntu-latest` GitHub Actions runner to using a pre-built Docker image hosted on the GitHub Container Registry (GHCR).

## Overview
1.  **Docker image base**: A lightweight base image (e.g., `python:3.11-slim-bookworm`) is chosen. The project is installed via `pip install -e .[rag]`.
2.  **Publishing Workflow**: We will create a `docker-publish.yml` that will be responsible for building and pushing the Docker image to GHCR whenever a release is published.
3.  **Using the public image**: The GitHub action `action.yml` uses the `docker://` syntax, taking advantage of the pre-built GHCR image. By pointing directly to the public registry, GitHub Actions pulls the image rather than executing bash scripts to construct the environment for every review.

## Technical Details

### 1. `Dockerfile` Structure
This will contain the necessary layers:
- Base image: `python:3.11-slim-bookworm` (or similar).
- System dependencies (if required).
- App source code (`iara/`, `setup.py`, etc.).
- `pip install --no-cache-dir .[rag]` command to install the Iara application.
- Entrypoint script (e.g., `run_iara.sh` or a custom python entry terminal command).

### 2. GitHub Actions Setup (`action.yml`)
The workflow needs to alter `using: 'composite'` to `using: 'docker'`. 
```yaml
runs:
  using: 'docker'
  image: 'docker://ghcr.io/gazeus/iara:latest'
```
*Note*: Care must be taken so we can still pass inputs like `openrouter_api_key`, `config_path`, etc. By using `using: docker`, GitHub Actions handles mounting the workspace (`/github/workspace`) automatically and passing `INPUT_*` variables into the environment.

### 3. CI/CD Publishing Pipeline (`.github/workflows/docker-publish.yml`)
A new workflow triggered on `release: types: [published]` or pushed tags. It will:
1. Log in to the Docker registry (GHCR).
2. Use Docker Buildx to build for standard architectures.
3. Push to `ghcr.io/gazeus/iara:<tag>` and `ghcr.io/gazeus/iara:latest`.

## Testing
- Locally build the Dockerfile.
- Run it locally simulating the environment variables expected by the action (`GITHUB_WORKSPACE`, `INPUT_OPENROUTER_API_KEY`, etc.).
- Ensure that Python can resolve paths when the workspace is mounted. 

## Rollout Plan
1. Merge the `Dockerfile` and publishing workflow (letting it push).
2. Test the pushed image separately.
3. Once validated, update `action.yml` to utilize the new docker image and cut a new minor release.
4. Update existing README.md usage examples.
