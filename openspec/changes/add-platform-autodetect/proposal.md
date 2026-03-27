# Change: Add CI platform auto-detection

## Why

The current `ci.platform` field in `.iara.json` forces users to hardcode a platform name (`"github"` or `"gitlab"`) in a file that is committed to the repository. This creates two problems: (1) the config is not portable — a repo mirrored across GitHub and GitLab requires different `.iara.json` values; (2) inline mode validation rejects any config where `platform` is absent, even though the runtime environment can be unambiguously detected from standard CI env vars (`GITHUB_ACTIONS`, `GITLAB_CI`).

## What Changes

- Add `detect_platform()` to `iara/platforms/factory.py`: reads `GITHUB_ACTIONS` and `GITLAB_CI` env vars, returns the platform string or `None` when ambiguous
- `post_comment.py`: replace the scattered inline `os.environ.get("GITLAB_CI")` checks with a single call to `detect_platform()`, using the config value as an explicit override when provided
- `config.py`: remove the `ValueError` that rejects inline mode when `ci.platform` is `None` — platform is now resolved at runtime, not at config-load time
- `config.py`: expand `valid_platforms` to include future platforms (`"azure-devops"`, `"bitbucket"`) so the validator doesn't reject them when support arrives
- Docs + examples: remove hardcoded `"platform"` from all inline-mode examples; document that the field is an optional override

## Impact

- Affected specs: `ci-integration`, `configuration`
- Affected code: `iara/platforms/factory.py`, `iara/post_comment.py`, `iara/config.py`, `docs/`, `examples/`
- **Backward compatible**: existing configs with `"platform": "github"` or `"platform": "gitlab"` continue to work unchanged; the explicit value takes precedence over auto-detection
