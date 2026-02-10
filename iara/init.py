"""Wizard interativo de setup da Iara."""

import os
import sys
import json
import getpass

from iara.auth import validate_api_key, save_global_config, resolve_api_key
from iara.config import DEFAULT_CONFIG, save_config


KNOWN_STACKS = ["Python", "C#", "Unity", "JavaScript", "TypeScript",
                "Java", "Go", "Rust", "Ruby", "PHP"]

KNOWN_FOCUS_AREAS = ["Logic", "Security", "Performance", "Clean Code",
                     "Error Handling", "Testing"]


def run_init():
    """Executa o wizard interativo de setup."""
    print()
    print("  Iara - AI Code Reviewer Setup")
    print("  " + "=" * 30)

    # --- Step 1: API Key ---
    api_key = _step_api_key()

    # --- Step 2: Project Config ---
    project_config = _step_project_config()

    # --- Step 3: Review Preferences ---
    review_config = _step_review_config()

    # --- Save ---
    _save_configs(api_key, project_config, review_config)

    # --- Next steps ---
    _show_next_steps()


def _step_api_key():
    """Solicita e valida a API key."""
    print()
    print("  Step 1: API Key")
    print("  Get your free key at: https://openrouter.ai/keys")
    print()

    # Verifica se key ja existe
    existing_key, source = resolve_api_key()
    if existing_key:
        masked = _mask_key(existing_key)
        source_label = "env var" if source == "env" else "config"
        print("  Key found (%s): %s" % (source_label, masked))
        response = input("  Use existing key? [Y/n]: ").strip().lower()
        if response not in ("n", "no"):
            return existing_key
        print()

    # Solicita nova key
    while True:
        try:
            api_key = getpass.getpass("  Enter your OpenRouter API key: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            print("  Setup cancelled.")
            sys.exit(0)

        if not api_key:
            print("  Key cannot be empty. Try again.")
            continue

        print("  Validating...", end=" ", flush=True)
        is_valid, error = validate_api_key(api_key)
        if is_valid:
            print("OK")
            return api_key
        else:
            print("FAILED (%s)" % error)
            retry = input("  Try again? [Y/n]: ").strip().lower()
            if retry in ("n", "no"):
                print("  Continuing with unvalidated key...")
                return api_key


def _step_project_config():
    """Solicita configuracao do projeto."""
    print()
    print("  Step 2: Project Configuration")
    print()

    default_name = os.path.basename(os.getcwd())

    name = input("  Project name [%s]: " % default_name).strip() or default_name

    print("  Known stacks: %s" % ", ".join(KNOWN_STACKS))
    stack_input = input("  Tech stack (comma-separated) [Python]: ").strip()
    tech_stack = [s.strip() for s in stack_input.split(",") if s.strip()] if stack_input else ["Python"]

    description = input("  Description [A software project.]: ").strip() or "A software project."

    return {
        "name": name,
        "description": description,
        "tech_stack": tech_stack
    }


def _step_review_config():
    """Solicita preferencias de review."""
    print()
    print("  Step 3: Review Preferences")
    print()

    print("  Available: %s, All" % ", ".join(KNOWN_FOCUS_AREAS))
    focus_input = input("  Focus areas (comma-separated) [All]: ").strip()
    if not focus_input or focus_input.lower() == "all":
        focus_areas = list(KNOWN_FOCUS_AREAS)
    else:
        focus_areas = [s.strip() for s in focus_input.split(",") if s.strip()]

    ignore_input = input("  Ignore patterns (comma-separated) []: ").strip()
    ignore_patterns = [s.strip() for s in ignore_input.split(",") if s.strip()] if ignore_input else []

    return {
        "focus_areas": focus_areas,
        "ignore_patterns": ignore_patterns
    }


def _save_configs(api_key, project, review):
    """Salva configs local e global."""
    print()

    # 1. Salva .iara.json local
    local_config = {
        "project": project,
        "review": review,
        "model": {
            "preferred": None,
            "fallback_enabled": True
        }
    }

    config_path = os.path.join(os.getcwd(), ".iara.json")

    if os.path.exists(config_path):
        overwrite = input("  .iara.json already exists. Overwrite? [y/N]: ").strip().lower()
        if overwrite in ("y", "yes"):
            save_config(local_config, config_path)
            print("  Saved .iara.json in current directory.")
        else:
            print("  Kept existing .iara.json.")
    else:
        save_config(local_config, config_path)
        print("  Saved .iara.json in current directory.")

    # 2. Salva API key no config global
    save_global_config({"api_key": api_key})
    print("  Saved API key to ~/.iara/config.json")


def _show_next_steps():
    """Mostra proximos passos."""
    print()
    print("  Setup complete!")
    print()
    print("  Next steps:")
    print("    git diff main | iara          # Review a diff")
    print("    iara --scan ./src             # Scan a directory")
    print("    iara auth status              # Check auth status")
    print()


def _mask_key(key):
    """Mascara a key para exibicao."""
    if len(key) > 12:
        return key[:8] + "..." + key[-4:]
    return "***"
