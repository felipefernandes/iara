## MODIFIED Requirements

### Requirement: Project Configuration
The system SHALL support loading configuration from a JSON file to customize the review context. The `ci.platform` field is optional; when omitted, Iara resolves the platform automatically from the runtime environment.

#### Scenario: Load configuration from file
- **WHEN** a `.iara.json` file exists in the working directory
- **THEN** Iara MUST read the project name, description, and settings from it.

#### Scenario: Default configuration
- **WHEN** no configuration file is found
- **THEN** Iara MUST default to the internal "Curupira" settings to preserve backward compatibility.

#### Scenario: Custom indexer ignore patterns
- **WHEN** `review.ignore_patterns` is provided in the configuration file
- **THEN** the system MUST merge these custom patterns with its default ignore list so that the directory tree scan ignores them.

#### Scenario: Platform field is optional
- **WHEN** `ci.platform` is absent from `.iara.json`
- **THEN** the system MUST NOT raise a validation error; it MUST attempt runtime auto-detection instead

#### Scenario: Inline mode without explicit platform
- **WHEN** `ci.review_mode` is `"inline"` and `ci.platform` is absent
- **THEN** the system MUST proceed, relying on runtime auto-detection to resolve the platform; validation at config-load time MUST NOT fail

## ADDED Requirements

### Requirement: Platform-Agnostic Configuration
The `.iara.json` configuration file SHALL be portable across CI platforms without modification. Hardcoding a platform value MUST NOT be required for any review mode.

#### Scenario: Same config works on GitHub and GitLab
- **WHEN** a repository with `ci.review_mode: "inline"` and no `ci.platform` is cloned and used on both GitHub Actions and GitLab CI
- **THEN** Iara MUST post inline comments correctly on each platform without any change to `.iara.json`

#### Scenario: Explicit platform overrides auto-detection
- **WHEN** `ci.platform` is set to `"github"` in `.iara.json` and the pipeline runs on GitLab CI
- **THEN** Iara MUST use the GitHub adapter (explicit config wins over environment detection)
