## ADDED Requirements
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
