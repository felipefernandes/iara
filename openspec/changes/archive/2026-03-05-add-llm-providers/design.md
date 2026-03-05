## Context
Iara currently speaks only OpenRouter's OpenAI-compatible endpoint. We need to add direct provider support for OpenAI, Google Gemini (OpenAI-compatible endpoint), and Anthropic (native messages API), while keeping OpenRouter as default.

## Goals / Non-Goals
- Goals: Provider selection, provider-specific auth, correct request/response handling, backward compatibility for existing OpenRouter configs.
- Non-Goals: Self-hosted providers (e.g., Ollama) and local model routing.

## Decisions
- Decision: Represent providers via `PROVIDER_CONFIGS` with base URL, auth scheme, and extra headers.
- Decision: Treat OpenRouter/OpenAI/Gemini as OpenAI-compatible; Anthropic uses `/v1/messages` with `anthropic-version` header.
- Decision: Disable fallback to OpenRouter free models when provider is not `openrouter`.

## Risks / Trade-offs
- Risk: Provider APIs may diverge in subtle fields. Mitigation: keep payload minimal and add targeted tests for response parsing.
- Risk: Users may misconfigure provider keys. Mitigation: clear error messages pointing to the expected env var.

## Migration Plan
- No data migration required. Existing configs remain valid; OpenRouter remains default.

## Open Questions
- None for this iteration.
