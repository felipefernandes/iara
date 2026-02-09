## 1. Preparation
- [ ] 1.1 Create `tests/test_config.py` to test configuration loading (TDD approach)
- [ ] 1.2 Create `tests/test_prompt.py` to test prompt generation

## 2. Configuration Implementation
- [ ] 2.1 Implement `load_config(path: str)` function in `ai-codereview.py` checks `.iara.json`
- [ ] 2.2 Define default "Curupira" config dictionary to use when file is missing (Backward Compatibility)

## 3. Dynamic Prompting
- [ ] 3.1 Refactor `SYSTEM_PROMPT` into a `generate_system_prompt(config)` function
- [ ] 3.2 Implement simple template substitution for Project Name, Stack, and Rules

## 4. Model Selection Logic
- [ ] 4.1 Refactor `review_code` to accept a generic `model_list` or `preferred_model`
- [ ] 4.2 Update `main()` to parse `IARA_MODEL` env var and pass to `review_code`

## 5. Verification
- [ ] 5.1 Run review on the Iara repo itself using a new `.iara.json`
- [ ] 5.2 specific test with a "Unity" dummy config to verify prompt adaptation
