"""Parser for inline review JSON output."""

import json
import logging
import re
from typing import Dict, List, Any


logger = logging.getLogger(__name__)


VALID_SEVERITIES = {"bug", "security", "performance", "style", "other"}


def parse_inline_review(text: str) -> Dict[str, Any]:
    """Parse and validate inline review JSON output from LLM.

    Expected schema:
    {
      "summary": "Brief overview",
      "comments": [
        {
          "file": "path/to/file.py",
          "line": 42,
          "severity": "bug|security|performance|style|other",
          "message": "Detailed feedback"
        }
      ]
    }

    Args:
        text: Raw text output from LLM (should be JSON)

    Returns:
        Validated dictionary with 'summary' and 'comments' keys

    Raises:
        ValueError: If JSON is invalid or schema doesn't match
    """
    # Extract JSON if it's wrapped in markdown blocks ANYWHERE in the text
    match = re.search(r'```(?:json)?\s*(.*?)\s*```', text, flags=re.IGNORECASE | re.DOTALL)
    if match:
        text = match.group(1).strip()
    else:
        # Fallback: Extract from the first '{' to the last '}'
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1 and end > start:
            text = text[start:end+1]

    # Try to parse JSON
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON output from LLM: {e}")

    # Validate top-level schema
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object at root, got {type(data).__name__}")

    if "summary" not in data:
        raise ValueError("Missing required field: 'summary'")

    if "comments" not in data:
        raise ValueError("Missing required field: 'comments'")

    if not isinstance(data["summary"], str):
        raise ValueError(f"Field 'summary' must be string, got {type(data['summary']).__name__}")

    if not isinstance(data["comments"], list):
        raise ValueError(f"Field 'comments' must be array, got {type(data['comments']).__name__}")

    # Validate each comment
    for i, comment in enumerate(data["comments"]):
        if not isinstance(comment, dict):
            raise ValueError(f"Comment [{i}] must be object, got {type(comment).__name__}")

        # Check required fields
        required_fields = ["file", "line", "severity", "message"]
        for field in required_fields:
            if field not in comment:
                raise ValueError(f"Comment [{i}] missing required field: '{field}'")

        # Validate field types
        if not isinstance(comment["file"], str):
            raise ValueError(
                f"Comment [{i}] field 'file' must be string, got {type(comment['file']).__name__}"
            )

        if not isinstance(comment["line"], int):
            raise ValueError(
                f"Comment [{i}] field 'line' must be integer, got {type(comment['line']).__name__}"
            )

        if not isinstance(comment["severity"], str):
            raise ValueError(
                f"Comment [{i}] field 'severity' must be string, got {type(comment['severity']).__name__}"
            )

        if not isinstance(comment["message"], str):
            raise ValueError(
                f"Comment [{i}] field 'message' must be string, got {type(comment['message']).__name__}"
            )

        # Validate severity value (case-insensitive)
        # Note: We intentionally coerce invalid severities to "other" instead of raising an exception.
        # This prevents open-source LLMs that hallucinate unsupported severities (e.g., "config")
        # from crashing the entire inline review parsing process.
        if comment["severity"].lower() not in VALID_SEVERITIES:
            logger.warning(
                f"Comment [{i}] invalid severity: '{comment['severity']}'. Coercing to 'other'."
            )
            comment["severity"] = "other"

        # Validate line number is positive
        if comment["line"] <= 0:
            raise ValueError(f"Comment [{i}] line number must be positive, got {comment['line']}")

    logger.info(f"Successfully parsed inline review: {len(data['comments'])} comments")
    return data
