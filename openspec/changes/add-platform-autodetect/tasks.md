## 1. Core — Platform detection function
- [ ] 1.1 Add `detect_platform() -> Optional[str]` to `iara/platforms/factory.py`
  - Returns `"github"` when `GITHUB_ACTIONS == "true"`
  - Returns `"gitlab"` when `GITLAB_CI == "true"`
  - Returns `None` otherwise (no recognized CI environment)

## 2. Core — Config validation update
- [ ] 2.1 Remove the `ValueError` in `config.py` that rejects `review_mode == "inline"` when `platform is None`
- [ ] 2.2 Expand `valid_platforms` list with `"azure-devops"` and `"bitbucket"` so future adapters can be added without touching validation

## 3. Core — post_comment refactor
- [ ] 3.1 Replace the inline `GITLAB_CI` env var check in `post_comment.py` with a call to `detect_platform()` from `factory.py`
- [ ] 3.2 Apply auto-detected platform only when config `ci.platform` is `None` (explicit config always wins)

## 4. Docs and examples
- [ ] 4.1 `docs/ci-integration.md`: fix the GitLab section (remove broken CLI flags, update template to working form, add self-hosted note, document platform auto-detection)
- [ ] 4.2 `docs/configuration.md`: add `ci` block documentation, mark `platform` as optional override
- [ ] 4.3 `examples/iara-example-inline.json`: remove hardcoded `"platform"` field
- [ ] 4.4 `CHANGELOG.md`: add entry for this change

## 5. Tests
- [ ] 5.1 Unit test `detect_platform()`: GitHub env, GitLab env, no env, both env (GitHub wins)
- [ ] 5.2 Verify existing config validation tests still pass after removing the inline-mode platform requirement

## Dependencies / sequencing
- Tasks 1 → 3 must be done in order (3 depends on 1)
- Tasks 2 and 4 are independent and can be done in parallel with 1–3
- Task 5 can be done after 1–3
