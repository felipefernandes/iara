"""Severity icons mapping for code review comments."""

# Severity to emoji mapping
SEVERITY_ICONS = {
    "bug": "🐛",
    "security": "🔒",
    "performance": "⚡",
    "style": "✨",
    "other": "💡"
}


def get_severity_icon(severity: str) -> str:
    """Get emoji icon for a given severity level.

    Args:
        severity: Severity string (bug, security, performance, style, other)

    Returns:
        Emoji string for the severity, or 💡 if severity is unknown
    """
    return SEVERITY_ICONS.get(severity.lower(), "💡")


def format_comment_with_icon(severity: str, message: str) -> str:
    """Format a comment with appropriate severity icon.

    If message already starts with an emoji, use it as-is.
    Otherwise, prepend the severity icon.

    Args:
        severity: Severity string (bug, security, performance, style, other)
        message: Comment message text

    Returns:
        Formatted message with icon
    """
    message = message.strip()

    # Check if message already starts with an emoji (common case)
    # Most emojis are in the range U+1F300 to U+1F9FF
    if message and ord(message[0]) > 0x1F000:
        return message

    # Prepend severity icon
    icon = get_severity_icon(severity)
    return f"{icon} {message}"
