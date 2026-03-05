# ci-integration Specification

## Purpose
TBD - created by archiving change add-unity-and-gitlab-support. Update Purpose after archive.
## Requirements
### Requirement: GitLab CI Integration
The system SHALL provide a compatible configuration for running inside GitLab CI pipelines.

#### Scenario: GitLab Environment Variables
- **WHEN** running in GitLab CI
- **THEN** the system MUST be able to read `CI_MERGE_REQUEST_DIFF_BASE_SHA` or similar variables if `git diff` logic allows, OR simply rely on `PR_DIFF` being piped from a `before_script`. (Design decision: keep it simple, pipe is standard).

#### Scenario: Exit Codes
- **WHEN** critical bugs are found
- **THEN** the system MAY optionally exit with non-zero code if configured to block the pipeline (Future scope, for now just report).

### Requirement: GitHub Action Provider Inputs
The system SHALL allow selecting the provider and supplying provider-specific API keys in the GitHub Action inputs.

#### Scenario: Default provider in GitHub Action
- **WHEN** the `provider` input is omitted
- **THEN** the action MUST default to `openrouter` and use `openrouter_api_key` if provided.

#### Scenario: OpenAI provider input
- **WHEN** the `provider` input is `openai` and `openai_api_key` is set
- **THEN** the action MUST export `OPENAI_API_KEY` and `IARA_PROVIDER=openai` before running Iara.

