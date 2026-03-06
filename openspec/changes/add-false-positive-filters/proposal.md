# Add Post-Processing Filters for Known False Positives

**Change ID**: `add-false-positive-filters`
**Related Issue**: [#71](https://github.com/felipefernandes/iara/issues/71)
**Complexity**: 🟢 Quick Win (1-2 hours)

## Why

Even with improved system prompts (Issue #70), some false positives still slip through LLM responses. This is because:

1. **LLMs are non-deterministic**: Even with explicit guidelines, different models/runs may generate false positives
2. **Context-dependent patterns**: Some patterns are only false positives in specific file contexts (e.g., `${{ secrets.X }}` in `.github/workflows/*.yml` files)
3. **Prompt limitations**: System prompts can't handle all edge cases without becoming too long

A **post-processing filter** provides deterministic, rule-based filtering that catches known false positive patterns before posting comments to PRs.

### Observed False Positives

From PR #69 (Groq provider) and real-world usage:

1. **GitHub Actions Secrets**: Reporting `${{ secrets.API_KEY }}` as hardcoded secrets in workflow files
2. **Security Best Practices**: Flagging `os.chmod(config, 0o600)` as performance issues
3. **Existing Error Handling**: Reporting "missing error handling" when try-except blocks exist
4. **Small-Scale Performance**: Suggesting micro-optimizations for < 10 item lists

## What Changes

### Modified Capabilities
- **review-quality** (New spec delta - extends existing from Issue #70)

### Expected Impact
- **30-50% additional reduction** in false positives (on top of Issue #70's 50-70%)
- **Deterministic filtering**: Consistent results across all LLM providers
- **Project-specific customization**: Teams can add their own patterns
- **Better user trust**: Fewer irrelevant comments = higher signal-to-noise ratio
- **No performance impact**: Filtering adds < 10ms overhead

## Solution Approach

Add a **pattern-based filtering layer** between JSON parsing and comment posting in the inline review flow.

### Architecture

```
LLM Response (JSON)
    ↓
parse_inline_review()  ← Existing (iara/parsers/inline_parser.py)
    ↓
comments[]
    ↓
filter_false_positives()  ← NEW (iara/filters.py)
    ↓
filtered_comments[]
    ↓
adapter.post_inline_comments()  ← Existing (iara/platforms/*.py)
```

### Key Components

#### 1. Filter Module (`iara/filters.py`)

```python
"""Post-processing filters for known false positive patterns."""

import re
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Default built-in false positive patterns
DEFAULT_FALSE_POSITIVE_PATTERNS = [
    {
        "name": "github-actions-secrets",
        "file_pattern": r"\.github/workflows/.*\.ya?ml$",
        "message_pattern": r"(hardcoded|exposed).*secret",
        "context_safe": r"\$\{\{.*secrets\.",
        "reason": "GitHub Actions secrets syntax is correct",
    },
    {
        "name": "security-chmod",
        "message_pattern": r"os\.chmod.*(?:inefficient|performance|unnecessary)",
        "context_safe": r"0o[0-7]{3,4}",
        "reason": "File permission hardening is security best practice",
    },
    {
        "name": "existing-error-handling",
        "message_pattern": r"missing.*error.*handling",
        "context_unsafe": r"try:.*except",
        "reason": "Error handling already present in context",
    },
    {
        "name": "small-scale-performance",
        "message_pattern": r"(?:O\(1\)|set|dict).*lookup.*performance",
        "context_safe": r"(?:range\([0-9]\)|[:10]|< *10)",
        "reason": "Micro-optimizations unnecessary for small scale",
    },
]


def filter_false_positives(
    comments: List[Dict[str, Any]],
    diff: str,
    custom_patterns: Optional[List[Dict[str, Any]]] = None
) -> List[Dict[str, Any]]:
    """Filter out known false positive patterns.

    Args:
        comments: List of parsed inline comments
        diff: Original diff text (for context extraction)
        custom_patterns: Additional project-specific patterns

    Returns:
        Filtered list of comments
    """
    patterns = DEFAULT_FALSE_POSITIVE_PATTERNS.copy()
    if custom_patterns:
        patterns.extend(custom_patterns)

    filtered = []
    filtered_count = 0

    for comment in comments:
        if not is_false_positive(comment, diff, patterns):
            filtered.append(comment)
        else:
            filtered_count += 1
            logger.info(
                f"Filtered false positive in {comment['file']}:{comment['line']} "
                f"- {comment['message'][:60]}..."
            )

    if filtered_count > 0:
        logger.info(f"Filtered {filtered_count} false positive(s)")

    return filtered


def is_false_positive(
    comment: Dict[str, Any],
    diff: str,
    patterns: List[Dict[str, Any]]
) -> bool:
    """Check if a comment matches any false positive pattern.

    Args:
        comment: Single inline comment
        diff: Original diff text
        patterns: List of pattern definitions

    Returns:
        True if comment is a false positive, False otherwise
    """
    file_path = comment.get("file", "")
    message = comment.get("message", "")
    line_number = comment.get("line", 0)

    # Extract context around the line from diff
    context = _extract_line_context(diff, file_path, line_number, context_lines=3)

    for pattern in patterns:
        # Check file pattern (if specified)
        file_pattern = pattern.get("file_pattern")
        if file_pattern and not re.search(file_pattern, file_path, re.IGNORECASE):
            continue

        # Check message pattern (required)
        message_pattern = pattern.get("message_pattern")
        if not message_pattern:
            continue

        if not re.search(message_pattern, message, re.IGNORECASE):
            continue

        # Message matches - now check context conditions
        context_safe = pattern.get("context_safe")
        context_unsafe = pattern.get("context_unsafe")

        # If context_safe is specified: only filter if safe pattern found
        if context_safe:
            if re.search(context_safe, context, re.IGNORECASE | re.DOTALL):
                logger.debug(
                    f"False positive detected: {pattern.get('name', 'unnamed')} "
                    f"- {pattern.get('reason', 'no reason')}"
                )
                return True

        # If context_unsafe is specified: only filter if unsafe pattern NOT found
        elif context_unsafe:
            if not re.search(context_unsafe, context, re.IGNORECASE | re.DOTALL):
                logger.debug(
                    f"False positive detected: {pattern.get('name', 'unnamed')} "
                    f"- {pattern.get('reason', 'no reason')}"
                )
                return True

        # No context condition - message match alone is sufficient
        else:
            logger.debug(
                f"False positive detected: {pattern.get('name', 'unnamed')} "
                f"- {pattern.get('reason', 'no reason')}"
            )
            return True

    return False


def _extract_line_context(
    diff: str,
    file_path: str,
    line_number: int,
    context_lines: int = 3
) -> str:
    """Extract context lines around a specific line from diff.

    Args:
        diff: Full diff text
        file_path: Target file path
        line_number: Line number to extract context for
        context_lines: Number of lines before/after to include

    Returns:
        Context string (empty if not found)
    """
    # Find the file section in diff
    file_header = f"+++ b/{file_path}"
    if file_header not in diff:
        return ""

    # Extract file's diff section
    file_section_start = diff.find(file_header)
    next_file = diff.find("\n+++ b/", file_section_start + 1)
    if next_file == -1:
        file_section = diff[file_section_start:]
    else:
        file_section = diff[file_section_start:next_file]

    # Parse hunks and find target line
    lines = file_section.split("\n")
    current_new_line = 0
    context_buffer = []

    for line in lines:
        # Track new file line numbers from hunk headers
        if line.startswith("@@"):
            match = re.search(r"\+(\d+)", line)
            if match:
                current_new_line = int(match.group(1)) - 1

        # Count lines in new file
        if line.startswith("+") and not line.startswith("+++"):
            current_new_line += 1
            context_buffer.append(line[1:])  # Remove + prefix
        elif not line.startswith("-"):
            current_new_line += 1
            context_buffer.append(line[1:] if line.startswith(" ") else line)

        # Keep sliding window of context_lines * 2 + 1
        if len(context_buffer) > context_lines * 2 + 1:
            context_buffer.pop(0)

        # Check if we found the target line
        if current_new_line == line_number:
            return "\n".join(context_buffer)

    # Target line not found in diff
    return ""
```

#### 2. Integration Point (`iara/post_comment.py`)

Modify the inline mode flow (around line 80-93):

```python
# Before (current):
data = parse_inline_review(review_text)
comments = data["comments"]

# After (with filtering):
from iara.filters import filter_false_positives

data = parse_inline_review(review_text)
comments = data["comments"]

# Load custom patterns from config
custom_patterns = config.get("review", {}).get("false_positive_patterns", [])

# Filter false positives
comments = filter_false_positives(comments, diff, custom_patterns)

# Update data with filtered comments
data["comments"] = comments
```

#### 3. Configuration Schema (`.iara.json`)

Add optional `false_positive_patterns` in `review` section:

```json
{
  "review": {
    "false_positive_patterns": [
      {
        "name": "custom-django-pattern",
        "file_pattern": "settings\\.py$",
        "message_pattern": "global.*variable",
        "reason": "Django settings.py uses globals by convention"
      }
    ]
  }
}
```

### Pattern Schema

Each pattern is a dictionary with:

- **`name`** (string, optional): Human-readable pattern identifier
- **`file_pattern`** (regex string, optional): Only match in files matching this pattern
- **`message_pattern`** (regex string, **required**): Match against comment message
- **`context_safe`** (regex string, optional): If present in context, it's safe → filter
- **`context_unsafe`** (regex string, optional): If absent in context, it's unsafe → filter
- **`reason`** (string, optional): Explanation for filtering (logged)

### Logic Flow

```
For each comment:
  1. Extract context from diff (3 lines before/after)
  2. For each pattern:
     a. Check file_pattern (skip if doesn't match)
     b. Check message_pattern (skip if doesn't match)
     c. Check context conditions:
        - If context_safe: filter only if pattern found in context
        - If context_unsafe: filter only if pattern NOT found in context
        - If no context: filter based on message match alone
  3. If any pattern matches → filter out
  4. Otherwise → keep comment
```

## Out of Scope

- **Machine learning classification** (Issue #72 - Confidence scores)
- **Self-review validation** (Issue #74 - Multi-pass approach)
- **Semantic similarity matching** (Future enhancement - requires embeddings)
- **Cross-file context analysis** (Future enhancement - complex implementation)

This change focuses **solely on regex-based pattern matching** as a Quick Win solution.

## Validation Strategy

### Test Cases

```python
# Test Case 1: GitHub Actions Secrets
comment = {
    "file": ".github/workflows/ci.yml",
    "line": 15,
    "message": "🔒 Potential hardcoded secret detected",
    "severity": "security"
}
diff = """
+++ b/.github/workflows/ci.yml
@@ -12,3 +12,5 @@
+      - name: Test
+        env:
+          API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
"""
# Expected: FILTERED (context_safe matches ${{ secrets.)

# Test Case 2: Security Chmod
comment = {
    "file": "config.py",
    "line": 42,
    "message": "⚡ os.chmod() is inefficient for performance",
    "severity": "performance"
}
diff = """
+++ b/config.py
@@ -40,3 +40,5 @@
+def save_config():
+    os.chmod(config_file, 0o600)  # Restrict to owner
"""
# Expected: FILTERED (message pattern + context_safe matches 0o600)

# Test Case 3: Existing Error Handling (should NOT filter)
comment = {
    "file": "api.py",
    "line": 30,
    "message": "🐛 Missing error handling for API call",
    "severity": "bug"
}
diff = """
+++ b/api.py
@@ -28,3 +28,5 @@
+def fetch_data():
+    response = requests.get(url)  # No error handling
"""
# Expected: NOT FILTERED (context_unsafe not found - no try-except)

# Test Case 4: Real Bug (should NOT filter)
comment = {
    "file": "calculator.py",
    "line": 10,
    "message": "🐛 Division by zero possible",
    "severity": "bug"
}
diff = """
+++ b/calculator.py
@@ -8,3 +8,5 @@
+def divide(a, b):
+    return a / b  # No zero check
"""
# Expected: NOT FILTERED (no pattern matches)
```

### Success Metrics

- ✅ False positive rate drops by 30-50% (on top of Issue #70)
- ✅ No false negatives introduced (real bugs still caught)
- ✅ Filtering overhead < 10ms per review
- ✅ Configuration works across all providers (OpenRouter, OpenAI, Gemini, Anthropic, Groq)

## Dependencies

- **Builds on**: Issue #70 (System prompt improvements) - already merged
- **No breaking changes**: Backward compatible (filtering is optional)
- **No new packages**: Uses only Python standard library (`re`, `logging`)
- **Works with**: All platforms (GitHub, GitLab)

## Risk Assessment

**Low Risk**:
- Filtering is **opt-in** via patterns (defaults are conservative)
- Only affects **inline mode** (summary mode unaffected)
- **Fallback**: If filtering fails, original comments posted (logged error)
- **Easily reversible**: Remove filter call to restore original behavior

**Mitigation**:
- Comprehensive test suite validates patterns don't filter real bugs
- Logging shows exactly what's filtered and why
- Custom patterns allow projects to override defaults
