## ADDED Requirements

### Requirement: Ollama Local Provider
The system SHALL support Ollama as a local LLM provider that requires no API key and runs entirely on the user's infrastructure.

#### Scenario: Ollama provider selected with no API key
- **WHEN** `model.provider` is set to `"ollama"` in `.iara.json` or `IARA_PROVIDER=ollama`
- **THEN** Iara MUST send requests to `http://localhost:11434/api/chat` (or `OLLAMA_BASE_URL/api/chat` if set)
- **AND** MUST NOT require or send any API key or Authorization header

#### Scenario: Custom Ollama endpoint via environment variable
- **WHEN** `OLLAMA_BASE_URL` is set (e.g., `http://my-server:11434`)
- **THEN** Iara MUST use that base URL for all Ollama requests instead of the default

#### Scenario: Auto-detect available local models
- **WHEN** no `model.preferred` or `IARA_MODEL` is configured and provider is `ollama`
- **THEN** Iara MUST query `{OLLAMA_BASE_URL}/api/tags` to discover locally installed models
- **AND** attempt the review using the first available model

#### Scenario: Ollama not running
- **WHEN** Iara cannot connect to the Ollama endpoint
- **THEN** Iara MUST return a user-friendly error message explaining that Ollama is not running
- **AND** MUST suggest the command to start it (`ollama serve`)

## MODIFIED Requirements

### Requirement: Provider-Specific Protocols
The system SHALL support OpenAI-compatible, Anthropic-native, and Ollama request/response formats.

#### Scenario: OpenAI-compatible providers
- **WHEN** the provider is `openrouter`, `openai`, `gemini`, or `groq`
- **THEN** Iara MUST use the OpenAI-compatible chat completions payload and parse `choices[0].message.content`.

#### Scenario: Anthropic provider
- **WHEN** the provider is `anthropic`
- **THEN** Iara MUST call `/v1/messages`, include `anthropic-version`, require `max_tokens`, and parse `content[0].text`.

#### Scenario: Ollama provider
- **WHEN** the provider is `ollama`
- **THEN** Iara MUST use the OpenAI-compatible messages array payload (same as non-Anthropic)
- **AND** MUST parse the response from `message.content` (not `choices[0].message.content`)
- **AND** MUST NOT include any Authorization header in the request
