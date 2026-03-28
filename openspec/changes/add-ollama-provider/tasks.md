## 1. OpenSpec
- [x] 1.1 Create proposal.md
- [x] 1.2 Create tasks.md
- [x] 1.3 Create spec delta for model-provider
- [x] 1.4 Validate with `openspec validate add-ollama-provider --strict`

## 2. iara/models.py
- [ ] 2.1 Add `"ollama"` entry to `PROVIDER_CONFIGS` with `auth_type: "none"`
- [ ] 2.2 Add `"ollama"` entry to `SUGGESTED_MODELS` with recommended local models

## 3. iara/auth.py
- [ ] 3.1 Add `NO_AUTH_PROVIDERS = {"ollama"}` constant
- [ ] 3.2 Expand `SUPPORTED_PROVIDERS` to include `NO_AUTH_PROVIDERS`
- [ ] 3.3 Add `get_ollama_base_url()` function
- [ ] 3.4 Update `resolve_api_key()` to return `(None, "none")` for Ollama
- [ ] 3.5 Update `validate_api_key()` to ping Ollama's `/api/tags` endpoint

## 4. iara/reviewer.py
- [ ] 4.1 Update `_build_headers()` to handle `auth_type: "none"`
- [ ] 4.2 Update `_extract_content()` to parse Ollama's `message.content` format
- [ ] 4.3 Add `_get_ollama_models()` helper to fetch available local models
- [ ] 4.4 Update `review_code_with_model()` to resolve Ollama base_url dynamically
- [ ] 4.5 Update `review_code()` to auto-detect Ollama models and show friendly error if not running

## 5. iara/init.py
- [ ] 5.1 Add `"ollama"` to `PROVIDER_OPTIONS`
- [ ] 5.2 Update `_step_provider()` to mention Ollama as local option
- [ ] 5.3 Add `_step_ollama_setup()` function (check connectivity, list models)
- [ ] 5.4 Update `_step_api_key()` to redirect to `_step_ollama_setup()` for Ollama
- [ ] 5.5 Update `_save_configs()` to skip saving api_key for Ollama

## 6. Documentation
- [ ] 6.1 Add Ollama section to `docs/configuration.md`
- [ ] 6.2 Add Ollama provider to `README.md` provider table and usage examples
