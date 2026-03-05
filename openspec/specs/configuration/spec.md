# configuration Specification

## Purpose
TBD - created by archiving change generalize-iara. Update Purpose after archive.
## Requirements
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

### Requirement: Tech Stack Customization
The system SHALL adapt its review rules based on the configured technology stack.

#### Scenario: Unity Stack
- **WHEN** `tech_stack` includes "Unity"
- **THEN** the system prompt MUST include C# and Unity-specific optimization rules (e.g., "Avoid `GetComponent` in Update").

### Requirement: Provider Configuration
The system SHALL allow configuring the provider in `.iara.json` with a default of `openrouter`.

#### Scenario: Default provider
- **WHEN** `model.provider` is not set in `.iara.json`
- **THEN** Iara MUST default to `openrouter`.

#### Scenario: Configured provider
- **WHEN** `model.provider` is set (e.g., `anthropic`)
- **THEN** Iara MUST use that provider for the review.

### Requirement: Provider API Key Resolution
The system SHALL resolve API keys based on the selected provider with backward compatibility for existing OpenRouter configs.

#### Scenario: Provider environment variable
- **WHEN** the provider is `openai` and `OPENAI_API_KEY` is set
- **THEN** Iara MUST use that key and treat it as the highest priority source.

#### Scenario: Provider config key with fallback
- **WHEN** the provider is `openrouter` and `openrouter_api_key` is not present in global config
- **THEN** Iara MUST fall back to the legacy `api_key` field.

