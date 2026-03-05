# Tasks: Add Inline PR Comments

All tasks should be completed in order. Mark with `[x]` when done.

## Phase 1: Configuration and Infrastructure

- [x] **Add `ci` section to config schema**
  - Modify `iara/config.py` to load `ci.platform` and `ci.review_mode` from `.iara.json`
  - Add validation: platform must be `github` or `gitlab`
  - Add validation: review_mode must be `inline` or `summary`
  - Default: `platform=None`, `review_mode="summary"` (backward compatible)
  - Update `.iara.json` example with new section

- [x] **Create platform adapter interface**
  - Create `iara/platforms/base.py` with `PlatformAdapter` abstract class
  - Define methods: `post_inline_comments()`, `post_summary_comment()`
  - Add docstrings with parameter types and return values

- [x] **Implement GitHub platform adapter**
  - Create `iara/platforms/github.py` with `GitHubAdapter(PlatformAdapter)`
  - Implement `post_inline_comments()` using PR Review Comments API
  - Implement `post_summary_comment()` using Issues Comments API
  - Add error handling with logging

- [x] **Implement GitLab platform adapter**
  - Create `iara/platforms/gitlab.py` with `GitLabAdapter(PlatformAdapter)`
  - Implement `post_inline_comments()` using MR Discussions API
  - Implement `post_summary_comment()` using MR Notes API
  - Add error handling with logging

- [x] **Create platform factory**
  - Create `iara/platforms/factory.py` with `get_adapter(platform, token, repo, pr_id)` function
  - Return appropriate adapter based on platform string
  - Raise clear error if platform unsupported

## Phase 2: Prompt Engineering and LLM Integration

- [x] **Modify prompt for inline mode**
  - Update `iara/prompt.py` to accept `review_mode` parameter
  - When `review_mode="inline"`, append JSON schema instructions to system prompt
  - Include few-shot examples of valid JSON output
  - Keep existing markdown prompt for `review_mode="summary"`

- [x] **Create inline output parser**
  - Create `iara/parsers/inline_parser.py` with `parse_inline_review(text)` function
  - Parse JSON and validate schema (summary, comments array)
  - Validate comment fields (file, line, severity, message)
  - Raise `ValueError` with clear message if invalid

- [x] **Add severity icons mapping**
  - Create `iara/parsers/severity.py` with severity → emoji mapping
  - Map: `bug`→🐛, `security`→🔒, `performance`→⚡, `style`→✨, `other`→💡
  - Use in comment formatting

## Phase 3: Script Integration

- [x] **Update `run_iara.sh` to detect platform**
  - Parse `.iara.json` to extract `ci.platform` and `ci.review_mode`
  - Set environment variables: `IARA_PLATFORM` and `IARA_REVIEW_MODE`
  - Pass to Python reviewer

- [x] **Modify `iara/reviewer.py` to support inline mode**
  - Accept `review_mode` parameter in `review_code_with_model()`
  - Generate appropriate prompt based on review_mode
  - Return JSON or markdown based on mode

- [x] **Update `run_iara.sh` to call platform adapter**
  - After review generation, check review_mode
  - If `inline`: parse JSON and call `adapter.post_inline_comments()`
  - If `summary` or fallback: call `adapter.post_summary_comment()`
  - Add try/except for fallback logic

## Phase 4: Testing

- [x] **Unit tests for config loading**
  - Test `ci` section parsing from `.iara.json`
  - Test defaults when `ci` section missing
  - Test validation errors for invalid platform/mode

- [x] **Unit tests for platform adapters**
  - Mock GitHub API calls in `test_github_adapter.py`
  - Mock GitLab API calls in `test_gitlab_adapter.py`
  - Test successful posting and error handling

- [x] **Unit tests for inline parser**
  - Test valid JSON parsing in `test_inline_parser.py`
  - Test invalid JSON handling (missing fields, wrong types)
  - Test edge cases (empty comments, special characters)

- [x] **Unit tests for prompt generation**
  - Test inline mode adds JSON schema to prompt
  - Test summary mode uses markdown prompt
  - Verify prompt length doesn't exceed limits

- [ ] **Integration test for GitHub inline flow**
  - Create test PR with real diff (or mock)
  - Generate inline review with test LLM
  - Verify comments posted via GitHub API (or mock)
  - *Note: Deferred to manual testing phase*

- [ ] **Integration test for GitLab inline flow**
  - Create test MR with real diff (or mock)
  - Generate inline review with test LLM
  - Verify discussions posted via GitLab API (or mock)
  - *Note: Deferred to manual testing phase*

- [ ] **Integration test for fallback flow**
  - Trigger JSON parse error → verify summary posted
  - Trigger API error → verify fallback summary posted
  - Verify logs show fallback reason
  - *Note: Deferred to manual testing phase*

## Phase 5: Documentation

- [x] **Update README with inline mode instructions**
  - Add section "Inline PR Comments (Optional)"
  - Explain `.iara.json` configuration
  - Show GitHub and GitLab setup examples
  - Note permissions required (`pull-requests: write` for GitHub)

- [ ] **Create inline mode troubleshooting guide**
  - Document common issues (JSON validation, line number mismatches)
  - Explain fallback behavior
  - Add FAQ section
  - *Note: Can be done as follow-up work*

- [x] **Update example `.iara.json` files**
  - Add commented example with `ci` section
  - Include both GitHub and GitLab examples
  - Show both inline and summary mode configs
  - Created `iara-example-inline.json` with inline mode configuration

- [ ] **Add inline mode to action.yml inputs**
  - Add `review_mode` input (optional, default: `summary`)
  - Update action description to mention inline mode
  - Add usage examples in action README
  - *Note: Can be done as follow-up work*

## Phase 6: Validation and Polish

- [x] **Run full test suite**
  - Execute `pytest tests/` and ensure all tests pass
  - Check test coverage for new modules (target >80%)
  - ✅ All 223 tests passing!

- [ ] **Manual testing with GitHub**
  - Deploy to test GitHub repo
  - Create PR with various code changes
  - Verify inline comments appear correctly
  - Test fallback scenarios
  - *Note: Ready for manual testing by user*

- [ ] **Manual testing with GitLab**
  - Deploy to test GitLab repo
  - Create MR with various code changes
  - Verify discussions appear correctly
  - Test fallback scenarios
  - *Note: Ready for manual testing by user*

- [ ] **Update CHANGELOG**
  - Add entry for inline PR comments feature
  - Note breaking changes (none expected)
  - Credit contributors
  - *Note: Can be done when ready to release*

## Dependencies

- Phase 1 tasks must complete before Phase 2
- Phase 2 tasks must complete before Phase 3
- Phase 3 tasks must complete before Phase 4
- Phases 4, 5, 6 can overlap once Phase 3 is complete
- Testing tasks can run in parallel
- Documentation tasks can run in parallel
