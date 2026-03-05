## ADDED Requirements
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

## MODIFIED Requirements
### Requirement: Fallback Strategy control
The system SHALL allow enabling/disabling the fallback to free models and MUST only attempt the default `FREE_MODELS` list when the provider is `openrouter`.

#### Scenario: Disable Fallback
- **WHEN** `model.fallback_enabled` is set to `false`
- **THEN** Iara MUST NOT iterate through the default `FREE_MODELS` list if the primary model fails.

#### Scenario: Provider is not OpenRouter
- **WHEN** `model.provider` is not `openrouter`
- **THEN** Iara MUST NOT attempt the default `FREE_MODELS` list even if fallback is enabled.
