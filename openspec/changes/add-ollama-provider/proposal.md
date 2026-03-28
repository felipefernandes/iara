# Change: Add Ollama provider for local LLM code reviews

## Why
Enterprises and regulated industries (GDPR, HIPAA, PCI-DSS) need 100% local inference where code never leaves their infrastructure. Ollama enables free, offline, privacy-first code reviews with no API keys required. This resolves issue #76.

## What Changes
- Add `ollama` as a 6th LLM provider with `auth_type: "none"` (no API key required)
- Support `OLLAMA_BASE_URL` env var to configure the Ollama endpoint (default: `http://localhost:11434`)
- Auto-detect available local models from Ollama's `/api/tags` endpoint
- Skip API key step in `iara init` for Ollama; show available models instead
- Handle Ollama's response format (`message.content` vs OpenAI's `choices[0].message.content`)
- Graceful error messaging when Ollama is not running
- Add Ollama installation guide and hardware requirements to documentation

## Impact
- Affected specs: `model-provider`, `configuration`
- Affected code: `iara/models.py`, `iara/auth.py`, `iara/reviewer.py`, `iara/init.py`
- No breaking changes: all existing providers continue working unchanged
