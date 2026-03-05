# model-provider Specification

## Purpose
TBD - created by archiving change generalize-iara. Update Purpose after archive.
## Requirements
### Requirement: Dynamic Model Selection
The system SHALL allow selecting a specific AI model via configuration or environment variables.

#### Scenario: Environment Variable Override
- **WHEN** `IARA_MODEL` environment variable is set (e.g., `google/gemini-1.5-pro`)
- **THEN** Iara MUST attempt to use ONLY that model, bypassing the default fallback list.
- **AND** if that model fails, it MUST report the error and stop (no fallback to free models if explicit model requested).

#### Scenario: Configured Preferred Model
- **WHEN** `model.preferred` is set in `.iara.json` AND `IARA_MODEL` is NOT set
- **THEN** Iara MUST attempt that model first.

### Requirement: Fallback Strategy control
The system SHALL allow enabling/disabling the fallback to free models and MUST only attempt the default `FREE_MODELS` list when the provider is `openrouter`.

#### Scenario: Disable Fallback
- **WHEN** `model.fallback_enabled` is set to `false`
- **THEN** Iara MUST NOT iterate through the default `FREE_MODELS` list if the primary model fails.

#### Scenario: Provider is not OpenRouter
- **WHEN** `model.provider` is not `openrouter`
- **THEN** Iara MUST NOT attempt the default `FREE_MODELS` list even if fallback is enabled.

### Requirement: LLM Provider Selection
The system SHALL allow selecting an LLM provider via configuration or environment variables.

#### Scenario: Configured provider selection
- **WHEN** `model.provider` is set in `.iara.json` (e.g., `openai`)
- **THEN** Iara MUST route requests to that provider and resolve the provider-specific API key.

#### Scenario: Environment override
- **WHEN** `IARA_PROVIDER` is set
- **THEN** Iara MUST override the configured provider for that run.

### Requirement: Provider-Specific Protocols
The system SHALL support both OpenAI-compatible and Anthropic-native request/response formats.

#### Scenario: OpenAI-compatible providers
- **WHEN** the provider is `openrouter`, `openai`, or `gemini`
- **THEN** Iara MUST use the OpenAI-compatible chat completions payload and parse `choices[0].message.content`.

#### Scenario: Anthropic provider
- **WHEN** the provider is `anthropic`
- **THEN** Iara MUST call `/v1/messages`, include `anthropic-version`, require `max_tokens`, and parse `content[0].text`.

