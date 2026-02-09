## ADDED Requirements
### Requirement: GitLab CI Integration
The system SHALL provide a compatible configuration for running inside GitLab CI pipelines.

#### Scenario: GitLab Environment Variables
- **WHEN** running in GitLab CI
- **THEN** the system MUST be able to read `CI_MERGE_REQUEST_DIFF_BASE_SHA` or similar variables if `git diff` logic allows, OR simply rely on `PR_DIFF` being piped from a `before_script`. (Design decision: keep it simple, pipe is standard).

#### Scenario: Exit Codes
- **WHEN** critical bugs are found
- **THEN** the system MAY optionally exit with non-zero code if configured to block the pipeline (Future scope, for now just report).
