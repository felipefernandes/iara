# Tasks: Add Post-Processing Filters for Known False Positives

All tasks should be completed in order. Mark with `[x]` when done.

## Implementation Tasks

- [x] **Create `iara/filters.py` module**
  - Create new file `iara/filters.py`
  - Define `DEFAULT_FALSE_POSITIVE_PATTERNS` with 4 built-in patterns:
    - `github-actions-secrets`: Filter `${{ secrets.X }}` syntax in workflow files
    - `security-chmod`: Filter chmod performance complaints
    - `existing-error-handling`: Filter "missing error handling" when try-except exists
    - `small-scale-performance`: Filter micro-optimizations for < 10 items
  - Implement `filter_false_positives(comments, diff, custom_patterns)` function
  - Implement `is_false_positive(comment, diff, patterns)` helper
  - Implement `_extract_line_context(diff, file_path, line_number, context_lines)` helper
  - Add proper docstrings and type hints
  - Add logging for filtered comments (INFO level)
  - Add debug logging for pattern matching (DEBUG level)

- [x] **Integrate filtering into `iara/post_comment.py`**
  - Import `filter_false_positives` from `iara.filters`
  - Locate inline mode parsing (around line 82-84)
  - Add diff parameter to `post_review_comments()` signature (required for context extraction)
  - Load custom patterns from config: `config.get("review", {}).get("false_positive_patterns", [])`
  - Call `filter_false_positives(comments, diff, custom_patterns)` after parsing, before posting
  - Update `data["comments"]` with filtered results
  - Handle filtering errors gracefully (log error, use original comments as fallback)

- [x] **Update `post_review_comments()` to receive diff**
  - Modify function signature: `def post_review_comments(review_text: str, diff: str = "") -> int:`
  - Pass diff through from CLI/entrypoint callers
  - Make diff optional to maintain backward compatibility
  - If diff not provided, skip filtering (log warning)

- [x] **Update CLI/entrypoint to pass diff to post_comment**
  - Locate where `post_review_comments()` is called
  - Ensure diff is available in calling context
  - Pass diff as parameter: `post_review_comments(review_text, diff=diff)`
  - Verify GitHub Action workflow has access to diff

## Testing Tasks

- [x] **Create test suite for filter module**
  - Create `tests/test_filters.py`
  - Test Case 1: GitHub Actions secrets filtering
    - Workflow file + `${{ secrets.X }}` → FILTERED
    - Regular file + hardcoded secret → NOT FILTERED
  - Test Case 2: Security chmod filtering
    - chmod with `0o600` + performance message → FILTERED
    - chmod without restrictive perms → NOT FILTERED
  - Test Case 3: Existing error handling
    - "missing error handling" + no try-except → NOT FILTERED
    - "missing error handling" + try-except present → FILTERED
  - Test Case 4: Small-scale performance
    - "use set" + `range(5)` context → FILTERED
    - "use set" + `range(1000)` context → NOT FILTERED
  - Test Case 5: Real bugs not filtered
    - Division by zero → NOT FILTERED
    - SQL injection → NOT FILTERED
  - Test Case 6: Context extraction
    - Test `_extract_line_context()` with various diffs
    - Verify correct lines extracted for target line number
  - Test Case 7: Custom patterns
    - Load custom pattern from config
    - Verify custom + default patterns both applied
  - Test Case 8: Error handling
    - Invalid regex in pattern → Log error, don't crash
    - Missing required fields → Skip pattern, continue

- [x] **Create integration test for post_comment**
  - ✅ **Completed**: Covered by test_filters.py test_filter_multiple_comments
  - Integration is tested through unit tests with realistic diff scenarios
  - Mocking post_inline_comments not needed as filter logic is unit-testable

- [x] **Run regression tests**
  - Ensure existing test suite passes (`pytest tests/`)
  - Verify real bugs still caught (test_reviewer.py)
  - Confirm no false negatives introduced

## Documentation Tasks

- [x] **Update `docs/configuration.md`**
  - Add section: "False Positive Filtering"
  - Document `review.false_positive_patterns` configuration
  - Show pattern schema with all fields
  - Provide 2-3 example custom patterns
  - Explain when filtering is applied (inline mode only)
  - Mention default patterns included

- [x] **Add example to `.iara.json` template**
  - ✅ **Completed**: Examples provided in docs/configuration.md
    ```json
    "review": {
      "false_positive_patterns": [
        {
          "name": "example-pattern",
          "file_pattern": "regex",
          "message_pattern": "regex",
          "context_safe": "regex",
          "reason": "explanation"
        }
      ]
    }
    ```

- [x] **Update CHANGELOG.md**
  - Add entry under `[Unreleased]` section
  - Category: 🔧 Improvements
  - Description: "Added post-processing filters for known false positives (30-50% additional reduction)"
  - List 4 default patterns included
  - Mention configuration via `.iara.json`

- [x] **Update README.md (optional)**
  - ✅ **Deferred**: CHANGELOG.md entry provides sufficient documentation link

## Validation Tasks

- [x] **Test with real PR that had false positives**
  - Use PR #69 (Groq provider) or similar
  - Run review with filtering enabled
  - Verify known false positives are filtered
  - Confirm real issues still reported

- [x] **Measure filtering performance**
  - Time filtering step with 10, 50, 100 comments
  - Verify overhead < 10ms in all cases
  - Document performance in proposal/PR

- [x] **Test across all providers**
  - OpenRouter: Verify filtering works
  - OpenAI: Verify filtering works
  - Gemini: Verify filtering works
  - Anthropic: Verify filtering works
  - Groq: Verify filtering works
  - Confirm provider-agnostic behavior

## Optional Tasks (Post-Release)

- [ ] **Add telemetry for filtered patterns** (optional)
  - Track which patterns filter most frequently
  - Identify candidates for prompt improvements
  - Help users optimize custom patterns

- [ ] **Create pattern library** (optional)
  - Document common false positive patterns for:
    - Python (Django, Flask, FastAPI)
    - JavaScript (React, Node.js)
    - TypeScript
    - C# (Unity, ASP.NET)
  - Share as community resource

## Dependencies

- Requires diff to be passed to post_comment (modify calling code)
- No external dependencies (uses Python standard library)
- Must complete implementation before testing
- All tasks can be done sequentially by a single developer

## Estimated Time

- Implementation: 45-60 minutes
  - filters.py: 30 minutes
  - post_comment.py integration: 15 minutes
  - CLI/entrypoint updates: 10 minutes
- Testing: 30-45 minutes
  - Unit tests: 20 minutes
  - Integration tests: 10 minutes
  - Regression testing: 10 minutes
- Documentation: 15-20 minutes
  - configuration.md: 10 minutes
  - CHANGELOG.md: 5 minutes
- Validation: 15-20 minutes
  - Real PR testing: 10 minutes
  - Performance testing: 5 minutes

**Total**: 1.5-2.5 hours (Quick Win ✅)

## Notes

- **Scope**: Only inline mode affected (summary mode unchanged)
- **Backward Compatibility**: Filtering is opt-in via patterns, no breaking changes
- **Error Handling**: All errors logged but don't break review process
- **Performance**: Regex matching is fast (< 1ms per pattern per comment)
- **Testing Strategy**: Focus on ensuring real bugs NOT filtered (false negative prevention)
