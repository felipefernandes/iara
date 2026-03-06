# ci-optimization Specification

## Purpose
Optimize the CI pipeline execution time by transitioning to a pre-built Docker image.

## ADDED Requirements

### Requirement: Pre-built Docker Image for CI
The Code Review Action MUST support pulling a pre-built Docker image instead of installing dependencies at runtime.

#### Scenario: Pre-built Docker Image for CI
- **GIVEN** a CI/CD environment like GitHub Actions
- **AND** a pull request triggers the analysis
- **WHEN** the code review action runs
- **THEN** it should download a pre-built Docker image (`ghcr.io/gazeus/iara:latest`) instead of installing dependencies dynamically in a raw container
- **AND** execution time should be significantly faster by avoiding package building.

### Requirement: Portability across CI/CD Providers
The Iara Docker image MUST be portable to enable execution from various CI platforms without custom shimming.

#### Scenario: Portability across CI/CD Providers
- **GIVEN** a user employing diverse CI/CD like GitLab CI, Jenkins, or Bitbucket Pipelines
- **WHEN** they need to run the Iara code reviewer
- **THEN** they should be able to run it using the same publicly available Docker image
- **AND** the image should easily accept the codebase volume mount and environment variables.
