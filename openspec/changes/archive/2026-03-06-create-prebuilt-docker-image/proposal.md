# Proposal: Create Pre-built Docker Image for CI/CD

## Motivation
Currently, Iara runs in a raw `ubuntu-latest` environment via GitHub Actions, where it installs all dependencies and Python packages at runtime using `pip install`. This drastically slows down the execution time of the code review. Providing a pre-built Docker image will significantly speed up this process and allow Iara to be easily used in other CI/CD environments (e.g., GitLab CI, Jenkins, Bitbucket Pipelines) out-of-the-box. Issue: #60.

## What Changes
1. **Dockerize**: Create a `Dockerfile` based on a lightweight Python image (e.g., `python:3.11-slim` or `python:3.11-slim-bookworm`).
2. **GitHub Actions for Publishing**: Add a new GitHub Actions workflow to build and push this image to the GitHub Container Registry (GHCR). This workflow will be triggered on new releases.
3. **CI/CD Simplification**: Update `action.yml` to support pulling the pre-built Docker image or document how to use the `docker://` approach for composite actions to avoid building the image during the PR review run.
4. **Documentation**: Update the README.md and other docs showing how to integrate the Docker image in GitHub Actions, GitLab CI, Jenkins, etc.

## Why
A pre-built image saves significant setup time in CI/CD platforms by bypassing redundant installation processes on every run and encapsulates environment specifics safely, which yields portability among distinct pipeline managers (Jenkins, Bitbucket, Gitlab, GitHub).

## Impact
- **Performance**: Review startup time will drop from minutes (dependency installation) to seconds (image pulling).
- **Portability**: The image will be vendor-agnostic, usable in any system that supports Docker.
- **Maintenance**: Simplifies the CI/CD execution context.

## Risks & Mitigations
- **Authentication**: Ensuring that injected secrets (OpenRouter API key, GitHub token) are properly passed into the Docker container. 
    - *Mitigation*: Use standard environment variables injected at runtime.
- **Diff Access**: The container needs access to the PR context (diff files). 
    - *Mitigation*: Mount the current workspace inside the container.
