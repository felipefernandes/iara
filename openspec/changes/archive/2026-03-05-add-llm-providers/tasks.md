## 1. Implementation
- [x] 1.1 Add provider configs and suggested models in `iara/models.py`.
- [x] 1.2 Extend API key resolution for provider-specific env/config in `iara/auth.py`.
- [x] 1.3 Add `model.provider` default to `iara/config.py` and example config.
- [x] 1.4 Update `iara/reviewer.py` for provider-specific request/response handling.
- [x] 1.5 Wire provider selection and env override in `iara/cli.py` and `iara/auth_status.py`.
- [x] 1.6 Update init wizard to select provider and capture provider key in `iara/init.py`.
- [x] 1.7 Update GitHub Action inputs and entrypoint to export provider-specific keys.

## 2. Tests
- [x] 2.1 Add/adjust unit tests for provider key resolution in `tests/test_auth.py`.
- [x] 2.2 Add unit tests for Anthropic request/response parsing in `tests/test_reviewer.py`.
- [x] 2.3 Update init tests for provider step and saved config in `tests/test_init.py`.

## 3. Verification
- [x] 3.1 Run `python -m unittest discover tests`.
