## MODIFIED Requirements
### Requirement: Project Configuration
The system SHALL support loading configuration from a JSON file to customize the review context.

#### Scenario: Load configuration from file
- **WHEN** a `.iara.json` file exists in the working directory
- **THEN** Iara MUST read the project name, description, and settings from it.

#### Scenario: Default configuration
- **WHEN** no configuration file is found
- **THEN** Iara MUST default to the internal "Curupira" settings to preserve backward compatibility.

#### Scenario: Custom indexer ignore patterns
- **WHEN** `review.ignore_patterns` is provided in the configuration file
- **THEN** the system MUST merge these custom patterns with its default ignore list so that the directory tree scan ignores them.
