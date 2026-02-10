"""Carregamento de configuracao e valores padrao."""

import os
import sys
import json

# Configuracao Padrao (Generica)
DEFAULT_CONFIG = {
    "project": {
        "name": "Generic Project",
        "description": "A software project.",
        "tech_stack": ["Python"]
    },
    "review": {
        "focus_areas": ["Logic", "Security", "Performance"],
        "ignore_patterns": []
    },
    "model": {
        "preferred": None,
        "fallback_enabled": True
    },
    "language": "en"
}

def deep_merge(base, override):
    """Merge recursivo de dicts. Retorna novo dict."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config(config_path=".iara.json"):
    """Carrega a configuracao do arquivo JSON ou retorna o padrao."""
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
    """Salva configuracao em arquivo JSON."""
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
