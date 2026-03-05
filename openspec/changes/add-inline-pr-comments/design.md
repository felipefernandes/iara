# Design: Inline PR Comments with Platform Adapters

## Overview

This design adds inline code review comments for GitHub and GitLab by introducing a platform adapter pattern, structured LLM output, and graceful fallback to summary comments.

## Architecture

### Current State

```
run_iara.sh → iara reviewer → markdown text → GitHub Issues API → single comment
```

**Limitation**: No line-level anchoring, all feedback in one block comment

### Proposed State

```
run_iara.sh → detect platform from .iara.json
             → iara reviewer (with inline prompt if enabled)
             → JSON output (inline mode) or markdown (summary mode)
             → Platform Adapter (GitHub/GitLab)
             → API calls (PR Review/MR Discussions)
             → Inline comments on specific lines OR fallback summary
```

## Key Design Decisions

### 1. Platform Detection and Configuration

**Decision**: Require explicit `ci.platform` in `.iara.json` rather than auto-detection.

**Rationale**:
- **Explicit > Implicit**: Users understand what mode they're running in
- **Environment variability**: GitHub Actions, GitLab CI, and Jenkins have different env vars
- **Testing**: Easier to test when platform is explicit config
- **Future-proof**: Can add platforms without breaking existing logic

**Example:**
```json
{
  "ci": {
    "platform": "github",
    "review_mode": "inline"
  }
}
```

**Alternative Considered**: Auto-detect from environment variables
- **Rejected**: Too fragile, env vars vary across CI systems
- **Rejected**: Hard to test, debug, and override

### 2. Review Mode (Inline vs Summary)

**Decision**: Default to `summary` mode for backward compatibility.

**Rationale**:
- **Non-breaking**: Existing users see no change
- **Opt-in**: Inline mode requires setup (platform config, API permissions)
- **Graceful degradation**: If inline fails, summary still works

**Modes**:
- `summary` (default): Current behavior, single markdown comment
- `inline`: Structured JSON output, line-level comments

**Alternative Considered**: Always try inline, fallback to summary
- **Rejected**: Changes default behavior, may surprise users
- **Rejected**: Inline requires different LLM prompt (different token usage)

### 3. Structured Output Format

**Decision**: Use JSON with `{summary, comments: [{file, line, severity, message}]}` schema.

**Schema**:
```json
{
  "summary": "Brief overview of findings",
  "comments": [
    {
      "file": "relative/path/to/file.py",
      "line": 42,
      "severity": "bug|security|performance|style|other",
      "message": "Detailed feedback with context"
    }
  ]
}
```

**Rationale**:
- **Simple**: Easy to parse and validate
- **Flexible**: Can add fields later (e.g., `suggested_fix`, `confidence`)
- **Severity**: Helps prioritize issues and apply icons (🐛🔒⚡✨)
- **Line-based**: Maps cleanly to both GitHub and GitLab APIs

**Alternative Considered**: Return only array of comments (no summary)
- **Rejected**: Summary is useful for PR-level context
- **Rejected**: Harder to fall back if all inline comments fail

### 4. Platform Adapter Pattern

**Decision**: Create abstract `PlatformAdapter` interface with GitHub/GitLab implementations.

**Structure**:
```
iara/
  platforms/
    base.py         # PlatformAdapter interface
    github.py       # GitHubAdapter(PlatformAdapter)
    gitlab.py       # GitLabAdapter(PlatformAdapter)
    factory.py      # get_adapter(platform) → Adapter instance
```

**Interface**:
```python
class PlatformAdapter:
    def post_inline_comments(self, pr_id: str, commit_sha: str, comments: List[Comment]) -> bool:
        """Post inline comments. Returns True if successful."""
        raise NotImplementedError

    def post_summary_comment(self, pr_id: str, body: str) -> bool:
        """Fallback: post single comment. Returns True if successful."""
        raise NotImplementedError
```

**Rationale**:
- **Extensibility**: Easy to add Bitbucket, Azure DevOps later
- **Testability**: Mock adapters for unit tests
- **Separation**: Platform-specific logic isolated from core review

**Alternative Considered**: If/else in run_iara.sh for each platform
- **Rejected**: Hard to test, maintain, and extend
- **Rejected**: Mixing concerns (shell script doing API calls)

### 5. API Integration Points

**GitHub**:
```bash
POST /repos/{owner}/{repo}/pulls/{pr_number}/reviews
{
  "commit_id": "${HEAD_SHA}",
  "event": "COMMENT",
  "comments": [
    {
      "path": "file.py",
      "line": 10,
      "body": "🐛 Bug: ..."
    }
  ]
}
```

**GitLab**:
```bash
POST /projects/{id}/merge_requests/{mr_iid}/discussions
{
  "body": "🐛 Bug: ...",
  "position": {
    "base_sha": "...",
    "start_sha": "...",
    "head_sha": "...",
    "position_type": "text",
    "new_path": "file.py",
    "new_line": 10
  }
}
```

**Key Difference**: GitHub uses batch review API, GitLab posts individual discussions.

**Implication**: GitLab adapter needs to make multiple API calls (one per comment) or batch via threads.

### 6. Prompt Engineering for Structured Output

**Decision**: Modify system prompt to request JSON when `review_mode: inline`.

**Inline Prompt Addition**:
```
OUTPUT FORMAT:
Return your review as a JSON object with this exact structure:
{
  "summary": "Brief overview of findings (1-2 sentences)",
  "comments": [
    {
      "file": "path/to/file.py",
      "line": 42,
      "severity": "bug|security|performance|style|other",
      "message": "Detailed feedback with emoji prefix (🐛 for bugs, 🔒 for security, etc.)"
    }
  ]
}

IMPORTANT:
- Only include issues that are anchored to specific lines in the diff
- Use relative file paths exactly as they appear in the diff
- Line numbers must match the NEW file (post-patch) line numbers
- If no issues found, return {"summary": "No issues found", "comments": []}
```

**Rationale**:
- **Explicit**: LLM knows exactly what format to return
- **Validated**: JSON schema is strict, easy to validate
- **Examples**: Can add few-shot examples in prompt for better adherence

**Risk**: LLM may return markdown instead of JSON (hallucination/prompt jailbreak)
- **Mitigation**: Try to parse JSON, fall back to summary mode if invalid

### 7. Fallback Strategy

**Decision**: Multi-level fallback to ensure comments are always posted.

**Fallback Levels**:
1. **Primary**: Inline comments via platform adapter
2. **Secondary**: Parse JSON but post as summary comment (with line numbers)
3. **Tertiary**: LLM returned markdown → post as summary
4. **Ultimate**: Generic "Review failed" message with stderr logs

**Implementation**:
```python
try:
    # Level 1: Try inline mode
    if review_mode == "inline":
        result = llm.generate(inline_prompt)
        data = json.loads(result)
        adapter.post_inline_comments(data["comments"])
except (json.JSONDecodeError, KeyError):
    # Level 2: Invalid JSON → format as summary with line numbers
    summary = format_inline_as_summary(result)
    adapter.post_summary_comment(summary)
except APIError:
    # Level 3: API failure → try summary mode
    adapter.post_summary_comment(format_summary(result))
except Exception:
    # Level 4: Complete failure → log error
    log_error("Review failed completely")
```

**Rationale**:
- **Reliability**: Users always get *some* feedback
- **Debugging**: Logs show which fallback level was used
- **Graceful degradation**: Inline → summary → error is smooth

### 8. Line Number Mapping

**Decision**: Use **NEW file line numbers** (post-patch) for inline comments.

**Rationale**:
- **GitHub/GitLab APIs**: Both expect line numbers from the NEW version of the file
- **Diff format**: `@@` hunks show old/new line numbers
- **LLM context**: Diff already shows `+` lines with their numbers

**Risk**: If LLM provides OLD line numbers, comments will be misplaced
- **Mitigation**: Prompt explicitly states "NEW file line numbers"
- **Validation**: Check if line number is within diff hunk range (optional enhancement)

### 9. Permissions and Security

**Decision**: Require `pull-requests: write` (GitHub) or `api` scope (GitLab).

**GitHub Actions**:
```yaml
permissions:
  pull-requests: write  # Required for PR Review Comments API
```

**GitLab CI**:
```yaml
variables:
  GITLAB_TOKEN: $CI_JOB_TOKEN  # Or personal access token with 'api' scope
```

**Security Considerations**:
- **Token exposure**: Never log tokens, use secret masking
- **Scope minimization**: Only request write permissions needed
- **Audit**: Log which API was called (review vs comment)

## Performance Considerations

### Latency Impact

**Inline Mode**:
- **LLM call**: +10-20% tokens (structured JSON overhead)
- **API calls**: GitHub = 1 batch call, GitLab = N individual calls
- **Total**: ~10-30% slower than summary mode

**Acceptable**: Code review is not latency-critical, UX benefit outweighs cost.

### Token Usage

**Prompt overhead**: ~200-300 tokens for JSON schema instructions

**Trade-off**: Inline mode costs more but provides better UX.

**Mitigation**: Allow users to choose via `review_mode` config.

## Testing Strategy

### Unit Tests

1. **Platform Adapters** (`test_platforms.py`)
   - Mock API calls for GitHub/GitLab
   - Test comment batching and formatting
   - Test error handling and retries

2. **JSON Parsing** (`test_inline_parser.py`)
   - Valid JSON → extract comments
   - Invalid JSON → fallback to summary
   - Edge cases (empty comments, missing fields)

3. **Prompt Generation** (`test_inline_prompt.py`)
   - Inline mode adds JSON schema to prompt
   - Summary mode uses markdown prompt

### Integration Tests

1. **GitHub E2E** (`test_github_inline.py`)
   - Create test PR with real diff
   - Post inline comments via API
   - Verify comments appear on correct lines

2. **GitLab E2E** (`test_gitlab_inline.py`)
   - Create test MR with real diff
   - Post discussions via API
   - Verify discussions appear on correct lines

3. **Fallback Flow** (`test_fallback.py`)
   - Trigger JSON parse errors → verify summary posted
   - Trigger API errors → verify fallback summary posted

## Risks and Mitigations

### Risk 1: LLM Returns Invalid JSON

**Risk**: LLM ignores JSON schema and returns markdown.

**Likelihood**: Medium (prompt adherence varies by model)

**Mitigation**:
- Explicit JSON schema in prompt with examples
- JSON validation with clear error messages
- Graceful fallback to summary mode
- Log invalid JSON for debugging

### Risk 2: Line Number Mismatches

**Risk**: LLM provides wrong line numbers, comments appear on wrong lines.

**Likelihood**: Low (diff context is clear)

**Mitigation**:
- Prompt explicitly requests NEW file line numbers
- Validate line numbers are within diff hunks (optional)
- Document issue in troubleshooting guide

### Risk 3: API Rate Limiting

**Risk**: GitLab adapter makes many API calls (one per comment), hits rate limits.

**Likelihood**: Low (typical PR has <20 comments)

**Mitigation**:
- Implement exponential backoff and retry
- Log rate limit headers for debugging
- Consider batching (future enhancement)

### Risk 4: Platform API Changes

**Risk**: GitHub/GitLab changes API, breaking integration.

**Likelihood**: Low (stable APIs with versioning)

**Mitigation**:
- Pin API versions in requests (`Accept: application/vnd.github.v3+json`)
- Monitor deprecation notices
- Unit tests catch API schema changes

## Future Enhancements (Out of Scope)

1. **Auto-platform detection**: Detect GitHub/GitLab from environment variables
2. **Bitbucket/Azure DevOps**: Add adapters for more platforms
3. **Comment threading**: Group related comments into threads
4. **Suggested fixes**: Include code suggestions in comments (`suggestion` feature in GitHub)
5. **Comment persistence**: Update comments instead of creating new ones on re-review
6. **Severity icons**: Custom emoji/badges per platform
7. **Confidence scores**: Show confidence level for each finding

## References

- [GitHub Pull Request Review Comments API](https://docs.github.com/en/rest/pulls/comments)
- [GitLab Merge Request Discussions API](https://docs.gitlab.com/ee/api/discussions.html)
- [OpenAI Structured Outputs](https://platform.openai.com/docs/guides/structured-outputs)
- [CodeClimate Inline Comments](https://docs.codeclimate.com/docs/github-pull-requests)
