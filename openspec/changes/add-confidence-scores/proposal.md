# Add Confidence Scores to Inline Comments

**Change ID**: `add-confidence-scores`
**Related Issue**: [#72](https://github.com/felipefernandes/iara/issues/72)
**Complexity**: Medium (1 day)

## Why

Not all LLM-reported issues are equally certain. Some are speculative while others are clear bugs, yet every parsed inline comment is posted today. A per-comment confidence score (0.0 to 1.0) lets Iara filter speculative reports and lets teams tune sensitivity vs. precision per project.

## What Changes

- **JSON schema**: every inline comment gains a `confidence` field (number, 0.0 to 1.0)
- **Parser**: `iara/parsers/inline_parser.py` validates presence of `confidence` and that `0.0 <= confidence <= 1.0` (out-of-range values are clamped with a warning)
- **Prompt**: `iara/prompt.py` instructs the LLM to rate confidence on each comment using a 0.0-1.0 rubric
- **Filtering**: `iara/post_comment.py` drops inline comments below the configured threshold before posting
- **Configuration**: new optional `review.min_confidence` in `.iara.json` (default `0.7`)

## Impact

- Affected specs: `review-quality`
- Affected code: `iara/prompt.py`, `iara/parsers/inline_parser.py`, `iara/post_comment.py`, `.iara.json`, docs
- No breaking changes: `min_confidence: 0.0` restores the previous behavior of posting every comment

## Solution Approach

### Data Flow

    LLM Response (JSON with per-comment confidence)
        |
    parse_inline_review()   <- validates presence + 0.0-1.0 range
        |
    comments[]
        |
    filter_by_confidence()  <- NEW: keeps comments with confidence >= min_confidence
        |
    adapter.post_inline_comments()

### Prompt Rubric

    Rate your confidence in each issue (0.0 to 1.0):
    - 0.9-1.0: Definite bug/issue
    - 0.7-0.9: Highly likely issue
    - 0.5-0.7: Possible issue worth reviewing
    - 0.3-0.5: Speculative suggestion
    - 0.0-0.3: Low confidence observation

### Parser Validation

- `confidence` is required on every inline comment (missing => treated as 0.0 and logged)
- Must be a number (int/float, not bool)
- Values outside 0.0-1.0 are clamped into range with a warning (fail-safe: never crash the review)

### Filtering (inline mode only)

    min_confidence = config.get("review", {}).get("min_confidence", 0.7)
    comments = [c for c in comments if c.get("confidence", 0.0) >= min_confidence]

- Threshold comparison is inclusive (`>=`)
- Filtered count is logged at INFO level
- Filtering failure falls back to posting all comments (fail-safe)
- Summary mode is unaffected

### Configuration

    {
      "review": {
        "min_confidence": 0.7
      }
    }

| Value   | Behavior                              |
| :------ | :------------------------------------ |
| `0.9`   | Only definite bugs/issues             |
| `0.7`   | Highly likely issues (default)        |
| `0.5`   | Possible issues worth reviewing       |
| `0.0`   | Post everything (disables the filter) |

## Out of Scope

- Per-severity thresholds (single global threshold only)
- Adaptive thresholds by model/provider
- Self-review validation (Issue #74)
- False-positive pattern filtering (Issue #71, separate change)

## Validation Strategy

1. `confidence: 0.9` with `min_confidence: 0.7` -> posted
2. `confidence: 0.3` with `min_confidence: 0.7` -> filtered and logged
3. `confidence: 0.7` with `min_confidence: 0.7` -> posted (inclusive boundary)
4. `min_confidence: 0.0` -> all comments posted
5. `confidence: 1.4` -> clamped to 1.0 with warning
6. `confidence: -0.2` -> clamped to 0.0 (filtered by default threshold)
7. missing `confidence` -> treated as 0.0 (filtered by default threshold)

## Dependencies

- Related: Issue #70 (System prompt), Issue #71 (Post-processing filters)
- No new packages: Python standard library only
- Works with all providers and platforms (GitHub, GitLab)
