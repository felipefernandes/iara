## ADDED Requirements
### Requirement: Project Configuration
The system SHALL support loading configuration from a JSON file to customize the review context.

#### Scenario: Load configuration from file
- **WHEN** a `.iara.json` file exists in the working directory
- **THEN** Iara MUST read the project name, description, and settings from it.

#### Scenario: Default configuration
- **WHEN** no configuration file is found
- **THEN** Iara MUST default to the internal "Curupira" settings to preserve backward compatibility.

### Requirement: Tech Stack Customization
The system SHALL adapt its review rules based on the configured technology stack.

#### Scenario: Unity Stack
- **WHEN** `tech_stack` includes "Unity"
- **THEN** the system prompt MUST include C# and Unity-specific optimization rules (e.g., "Avoid `GetComponent` in Update").
