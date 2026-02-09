"""Carregamento de configuracao e valores padrao."""

import os
import sys
import json

# Configuracao Padrao (Generica)
DEFAULT_CONFIG = {
    "project": {
        "name": "Projeto Genérico",
        "description": "Um projeto de software.",
        "tech_stack": ["Python"]
    },
    "review": {
        "focus_areas": ["Logic", "Security", "Performance"],
        "ignore_patterns": []
    },
    "model": {
        "preferred": None,
        "fallback_enabled": True
    }
}

def load_config(config_path: str = ".iara.json") -> dict:
    """Carrega a configuracao do arquivo JSON ou retorna o padrao."""
    if not os.path.exists(config_path):
        return DEFAULT_CONFIG

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            user_config = json.load(f)
            # Merge superficial (pode ser melhorado para deep merge futuramente)
            config = DEFAULT_CONFIG.copy()
            config.update(user_config)
            return config
    except json.JSONDecodeError:
        print(f"⚠️ Erro ao ler {config_path}. Usando configuração padrão.", file=sys.stderr)
        return DEFAULT_CONFIG
