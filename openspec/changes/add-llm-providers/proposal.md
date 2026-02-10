# Change: Add Multiple LLM Providers

## Why

Iara currently depends on OpenRouter only. Users want to connect directly to OpenAI, Google Gemini, and Anthropic while keeping OpenRouter as the default.

## What Changes

- Add provider selection (`openrouter`, `openai`, `gemini`, `anthropic`) via config and env override.
- Route requests using provider-specific endpoints and authentication headers.
- Support OpenAI-compatible responses and Anthropic native responses.
- Resolve provider-specific API keys with backward compatibility for existing OpenRouter config.
- Update CLI, init wizard, GitHub Action inputs, and examples accordingly.

## Impact

- Affected specs: `specs/model-provider/spec.md`, `specs/configuration/spec.md`, `specs/ci-integration/spec.md`
- Affected code: `iara/models.py`, `iara/reviewer.py`, `iara/auth.py`, `iara/config.py`, `iara/cli.py`, `iara/init.py`, `iara/auth_status.py`, `action.yml`, `entrypoint.sh`, `iara-example.json`, tests
