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
        "max_index_file_size": 1048576
    },
    "model": {
        "preferred": None,
        "fallback_enabled": True,
        "provider": "openrouter"
    },
    "memory": {
        "dedup_threshold": 0.92
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
    """Load configuration from JSON file or return defaults."""
    if not os.path.exists(config_path):
        return DEFAULT_CONFIG.copy()

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            user_config = json.load(f)
            return deep_merge(DEFAULT_CONFIG, user_config)
    except json.JSONDecodeError:
        print("⚠️ Error reading %s. Using default config." % config_path, file=sys.stderr)
        return DEFAULT_CONFIG.copy()


def save_config(config, config_path=".iara.json"):
    """Save configuration to JSON file."""
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
