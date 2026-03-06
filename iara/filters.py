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
        "context_safe": r"0o[0-6][0-7]{2,3}",  # Only restrictive perms (0o600, 0o400, etc, not 0o777)
        "reason": "File permission hardening is security best practice",
    },
    {
        "name": "existing-error-handling",
        "message_pattern": r"missing.*error.*handling",
        "context_safe": r"try:.*except",  # If try-except exists, error handling is present → filter
        "reason": "Error handling already present in context",
    },
    {
        "name": "small-scale-performance",
        "message_pattern": r"(?:O\(1\)|set|dict).*lookup.*performance",
        "context_safe": r"(?:range\([0-9]\)|\[:\s*[0-9]\]|<\s*10\b)",  # range(5), [:5], [:10], or < 10
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

    target_found = False
    lines_after_target = 0

    for line in lines:
        # Track new file line numbers from hunk headers
        if line.startswith("@@"):
            match = re.search(r"\+(\d+)", line)
            if match:
                current_new_line = int(match.group(1)) - 1
            continue  # Skip hunk headers

        # Skip file headers
        if line.startswith("+++") or line.startswith("---") or line.startswith("diff "):
            continue

        # Count lines in new file
        if line.startswith("+"):
            current_new_line += 1
            context_buffer.append(line[1:])  # Remove + prefix
        elif line.startswith(" "):
            current_new_line += 1
            context_buffer.append(line[1:])  # Remove leading space
        elif line.startswith("-"):
            # Deleted lines don't affect new file line numbering
            continue
        else:
            # Empty lines or other lines
            continue

        # Keep sliding window before finding target
        if not target_found and len(context_buffer) > context_lines * 2 + 1:
            context_buffer.pop(0)

        # Check if we found the target line
        if current_new_line == line_number and not target_found:
            target_found = True

        # After finding target, collect more lines for context_lines
        if target_found:
            lines_after_target += 1
            if lines_after_target > context_lines:
                return "\n".join(context_buffer)

    # Return what we have if target was found but not enough lines after
    if target_found:
        return "\n".join(context_buffer)

    # Target line not found in diff
    return ""
