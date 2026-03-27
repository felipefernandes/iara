"""Configuration loading and default values."""

import os
import sys
import json

# Default Configuration
DEFAULT_CONFIG = {
    "project": {
        "name": "Generic Project",
        "description": "A software project.",
        "tech_stack": ["Python"]
    },
    "review": {
        "focus_areas": ["Logic", "Security", "Performance"],
        "ignore_patterns": [],
        "max_index_file_size": 1048576,
        "max_diff_tokens": 12000
    },
    "model": {
        "preferred": None,
        "fallback_enabled": True,
        "provider": "openrouter"
    },
    "memory": {
        "dedup_threshold": 0.92
    },
    "ci": {
        "platform": None,
        "review_mode": "summary"
    },
    "language": "en"
}

def deep_merge(base, override):
    """Recursive dict merge. Returns new dict."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config(config_path=".iara.json"):
    """Load configuration from JSON file or return defaults.

    Raises:
        ValueError: If configuration is invalid
    """
    if not os.path.exists(config_path):
        config = DEFAULT_CONFIG.copy()
        validate_ci_config(config)
        return config

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            user_config = json.load(f)
            config = deep_merge(DEFAULT_CONFIG, user_config)
            validate_ci_config(config)
            return config
    except json.JSONDecodeError:
        print("⚠️ Error reading %s. Using default config." % config_path, file=sys.stderr)
        return DEFAULT_CONFIG.copy()


def validate_ci_config(config):
    """Validate CI configuration section.

    Raises:
        ValueError: If configuration is invalid
    """
    ci = config.get("ci", {})
    platform = ci.get("platform")
    review_mode = ci.get("review_mode", "summary")

    # Validate platform (None = auto-detect at runtime from CI environment)
    valid_platforms = [None, "github", "gitlab", "azure-devops", "bitbucket"]
    if platform not in valid_platforms:
        raise ValueError(
            f"Invalid ci.platform: '{platform}'. "
            f"Must be one of: {', '.join(repr(p) for p in valid_platforms if p is not None)}"
        )

    # Validate review_mode
    valid_modes = ["summary", "inline"]
    if review_mode not in valid_modes:
        raise ValueError(
            f"Invalid ci.review_mode: '{review_mode}'. "
            f"Must be one of: {', '.join(valid_modes)}"
        )

    # Platform is optional — resolved at runtime via detect_platform() when absent

    return True


def save_config(config, config_path=".iara.json"):
    """Save configuration to JSON file."""
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
