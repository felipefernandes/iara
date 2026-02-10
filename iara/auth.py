"""API key resolution and global configuration management."""

import os
import json
import stat

GLOBAL_CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".iara")
GLOBAL_CONFIG_PATH = os.path.join(GLOBAL_CONFIG_DIR, "config.json")


def resolve_api_key():
    """
    Resolve API key by priority order.
    Returns (api_key, source) where source is 'env', 'config', or 'none'.
    """
    # 1. Environment variable (highest priority - CI/CD)
    env_key = os.environ.get("OPENROUTER_API_KEY")
    if env_key:
        return env_key, "env"

    # 2. Global config (~/.iara/config.json)
    config_key = _load_global_config().get("api_key")
    if config_key:
        return config_key, "config"

    # 3. Not found
    return None, "none"


def _load_global_config():
    """Load global config from ~/.iara/config.json."""
    if not os.path.exists(GLOBAL_CONFIG_PATH):
        return {}
    try:
        with open(GLOBAL_CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_global_config(config):
    """Save config to ~/.iara/config.json with restricted permissions."""
    os.makedirs(GLOBAL_CONFIG_DIR, exist_ok=True)

    with open(GLOBAL_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

    # Restricted permissions (Unix only, ignored on Windows)
    try:
        os.chmod(GLOBAL_CONFIG_PATH, stat.S_IRUSR | stat.S_IWUSR)
    except (OSError, AttributeError):
        pass


def validate_api_key(api_key):
    """
    Validate an API key by calling OpenRouter /api/v1/models.
    Returns (is_valid, error_message).
    """
    import urllib.request
    import urllib.error

    url = "https://openrouter.ai/api/v1/models"
    headers = {
        "Authorization": "Bearer " + api_key,
        "HTTP-Referer": "https://github.com/felipefernandes/iara",
        "X-Title": "Iara Code Reviewer"
    }

    try:
        req = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=15) as response:
            if response.status == 200:
                return True, None
            return False, "Unexpected status: %d" % response.status
    except urllib.error.HTTPError as e:
        if e.code == 401:
            return False, "Invalid API key (401 Unauthorized)"
        return False, "HTTP Error %d" % e.code
    except urllib.error.URLError as e:
        return False, "Connection error: %s" % e.reason
    except Exception as e:
        return False, "Unexpected error: %s" % e
