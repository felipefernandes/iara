# Proposal: Add Inline PR Comments

## Why

Currently, Iara posts code reviews as a **single summary comment** on the PR using the GitHub Issues Comments API. This approach has a significant UX limitation: developers must mentally cross-reference Iara's feedback with the actual code changes in the diff.

**Current flow:**
```
Iara review → Single comment → "In file reviewer.py, line 103, there's a bug..."
```

This is acceptable but not optimal. Professional code review tools (CodeClimate, SonarCloud, human reviewers) use **inline comments anchored to specific lines** in the diff, making feedback immediately actionable.

**Example UX difference:**
- ❌ **Today**: "No arquivo `reviewer.py`, linha 103, há um potencial bug de segurança..."
- ✅ **With inline**: Comment appears directly on line 103 of `reviewer.py` in the PR diff view

## What Changes

This proposal adds **optional inline PR comment support** for GitHub and GitLab, while maintaining backward compatibility with the current summary comment mode.

### Key Components:

1. **Platform Configuration** (`.iara.json`)
   - New `ci` section to specify platform (`github` or `gitlab`)
   - New `review_mode` option (`inline` or `summary`, default: `summary`)

2. **Structured Review Output**
   - When `review_mode: inline`, LLM returns structured JSON with file/line/severity/message
   - When `review_mode: summary`, LLM returns markdown text (current behavior)

3. **Platform Adapters**
   - GitHub adapter: Uses [Pull Request Review Comments API](https://docs.github.com/en/rest/pulls/comments)
   - GitLab adapter: Uses [Merge Request Discussions API](https://docs.gitlab.com/ee/api/discussions.html)
   - Base interface for future platforms

4. **Graceful Fallback**
   - If inline mode fails (invalid JSON, API error), fall back to summary comment
   - If platform not supported, use summary mode with warning

### Example Configuration:

```json
{
  "ci": {
    "platform": "github",
    "review_mode": "inline"
  },
  "review": {
    "focus_areas": ["Logic", "Security"]
  }
}
```

### Example Inline Output (JSON):

```json
{
  "summary": "Found 2 critical issues and 1 performance suggestion",
  "comments": [
    {
      "file": "iara/reviewer.py",
      "line": 103,
      "severity": "bug",
      "message": "🐛 Potential SQL injection vulnerability..."
    },
    {
      "file": "iara/config.py",
      "line": 27,
      "severity": "performance",
      "message": "⚡ This loop could be optimized..."
    }
  ]
}
```

## Acceptance Criteria

- [ ] `.iara.json` supports `ci.platform` (`github`|`gitlab`) and `ci.review_mode` (`inline`|`summary`)
- [ ] When `review_mode: inline`, LLM prompt requests structured JSON output
- [ ] GitHub adapter posts inline comments using PR Review Comments API
- [ ] GitLab adapter posts inline comments using MR Discussions API
- [ ] Fallback to summary mode if inline posting fails or JSON is invalid
- [ ] `run_iara.sh` detects platform and uses appropriate adapter
- [ ] Documentation clearly states inline mode is optional and platform-specific
- [ ] Tests cover both inline and summary modes for GitHub and GitLab
- [ ] Backward compatibility: existing configs without `ci` section use summary mode

## Out of Scope

- Support for Bitbucket, Azure DevOps (future work)
- Automatic platform detection (requires explicit config)
- Custom severity icons/formatting per platform
- Threaded comment discussions
- Comment editing/updating on subsequent reviews

## Impact

This is potentially the **most significant UX improvement** for Iara. Inline comments are the industry standard for professional code review tools and dramatically improve developer experience by providing contextual, actionable feedback directly where it matters.

## Complexity

🔴 **High** — Requires:
- Prompt engineering for structured output
- Multi-platform abstraction layer
- Robust JSON parsing and validation
- API integration for GitHub and GitLab
- Comprehensive fallback logic
- Cross-platform testing
