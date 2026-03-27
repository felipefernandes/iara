## MODIFIED Requirements

### Requirement: GitLab CI Integration
The system SHALL provide native support for running inside GitLab CI pipelines, with automatic detection of the GitLab CI environment via the `GITLAB_CI` predefined variable.

#### Scenario: GitLab environment auto-detected
- **WHEN** `GITLAB_CI=true` is present in the environment and `ci.platform` is not set in `.iara.json`
- **THEN** Iara MUST automatically select the GitLab platform adapter without requiring explicit configuration

#### Scenario: Explicit platform config overrides auto-detection
- **WHEN** `ci.platform` is explicitly set in `.iara.json`
- **THEN** Iara MUST use that value regardless of what CI environment variables are present

#### Scenario: Exit Codes
- **WHEN** critical bugs are found
- **THEN** the system MAY optionally exit with non-zero code if configured to block the pipeline (Future scope, for now just report).

## ADDED Requirements

### Requirement: GitHub Actions Platform Auto-Detection
The system SHALL automatically detect when it is running inside GitHub Actions and configure itself accordingly, without requiring `ci.platform` to be set in `.iara.json`.

#### Scenario: GitHub Actions environment auto-detected
- **WHEN** `GITHUB_ACTIONS=true` is present in the environment and `ci.platform` is not set in `.iara.json`
- **THEN** Iara MUST automatically select the GitHub platform adapter

### Requirement: Platform Detection Precedence
The system SHALL follow a deterministic precedence order when resolving the active CI platform.

#### Scenario: Explicit config takes highest priority
- **WHEN** `ci.platform` is set in `.iara.json` to a recognized value
- **THEN** the system MUST use that value, ignoring any CI environment variables

#### Scenario: Auto-detection is the fallback
- **WHEN** `ci.platform` is absent or `null` in `.iara.json`
- **THEN** the system MUST attempt to detect the platform from standard CI environment variables (`GITHUB_ACTIONS`, `GITLAB_CI`)

#### Scenario: Graceful no-op when platform is unresolvable
- **WHEN** `ci.platform` is absent and no recognized CI environment variable is set
- **THEN** the system MUST log a clear error message and return a non-zero exit code from `post_comment`
