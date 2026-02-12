"""Interactive setup wizard for Iara."""

import os
import sys
import json
import getpass

from iara.auth import validate_api_key, save_global_config, resolve_api_key, PROVIDER_ENV_VARS, _load_global_config
from iara.config import save_config
from iara.prompt import LANGUAGE_MAP


KNOWN_STACKS = ["Python", "C#", "Unity", "JavaScript", "TypeScript",
                "Java", "Go", "Rust", "Ruby", "PHP"]

KNOWN_FOCUS_AREAS = ["Logic", "Security", "Performance", "Clean Code",
                     "Error Handling", "Testing"]

SUGGESTED_LANGUAGES = ["en", "pt-br", "es", "fr", "de", "ja", "zh"]
PROVIDER_OPTIONS = ["openrouter", "openai", "gemini", "anthropic"]
PROVIDER_KEY_URLS = {
    "openrouter": "https://openrouter.ai/keys",
    "openai": "https://platform.openai.com/api-keys",
    "gemini": "https://aistudio.google.com/app/apikey",
    "anthropic": "https://console.anthropic.com/keys"
}


def run_init():
    """Run the interactive setup wizard."""
    print()
    print("  Iara - AI Code Reviewer Setup")
    print("  " + "=" * 30)

    # --- Step 1: Language ---
    language = _step_language()

    # --- Step 2: Provider ---
    provider = _step_provider()

    # --- Step 3: API Key ---
    api_key = _step_api_key(provider)

    # --- Step 4: Project Config ---
    project_config = _step_project_config()

    # --- Step 5: Review Preferences ---
    review_config = _step_review_config()

    # --- Save ---
    _save_configs(api_key, provider, language, project_config, review_config)

    # --- Next steps ---
    _show_next_steps()


def _step_api_key(provider):
    """Prompt and validate the API key."""
    print()
    print("  Step 3: API Key")
    key_url = PROVIDER_KEY_URLS.get(provider, PROVIDER_KEY_URLS["openrouter"])
    print("  Get your key at: %s" % key_url)
    print()

    # Check if key already exists
    existing_key, source = resolve_api_key(provider)
    if existing_key:
        masked = _mask_key(existing_key)
        env_label = PROVIDER_ENV_VARS.get(provider, "OPENROUTER_API_KEY")
        source_label = env_label if source == "env" else "config"
        print("  Key found (%s): %s" % (source_label, masked))
        response = input("  Use existing key? [Y/n]: ").strip().lower()
        if response not in ("n", "no"):
            return existing_key
        print()

    # Ask for new key
    while True:
        try:
            prompt_label = provider.upper()
            api_key = getpass.getpass("  Enter your %s API key: " % prompt_label).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            print("  Setup cancelled.")
            sys.exit(0)

        if not api_key:
            print("  Key cannot be empty. Try again.")
            continue

        print("  Validating...", end=" ", flush=True)
        is_valid, error = validate_api_key(api_key, provider)
        if is_valid:
            print("OK")
            return api_key
        else:
            print("FAILED (%s)" % error)
            retry = input("  Try again? [Y/n]: ").strip().lower()
            if retry in ("n", "no"):
                print("  Continuing with unvalidated key...")
                return api_key


def _step_language():
    """Select review output language."""
    print()
    print("  Step 1: Review Language")
    print()

    lang_display = ", ".join("%s (%s)" % (code, LANGUAGE_MAP.get(code, code)) for code in SUGGESTED_LANGUAGES)
    print("  Options: %s" % lang_display)
    lang_input = input("  Review language [en]: ").strip().lower()
    return lang_input if lang_input else "en"


def _step_provider():
    """Select LLM provider."""
    print()
    print("  Step 2: LLM Provider")
    print()

    options = "openrouter (default, free), openai, gemini, anthropic"
    print("  Options: %s" % options)

    while True:
        provider_input = input("  Provider [openrouter]: ").strip().lower()
        provider = provider_input if provider_input else "openrouter"
        if provider in PROVIDER_OPTIONS:
            return provider
        print("  Invalid provider. Choose from: %s" % ", ".join(PROVIDER_OPTIONS))


def _step_project_config():
    """Prompt for project configuration."""
    print()
    print("  Step 4: Project Configuration")
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
    """Prompt for review preferences."""
    print()
    print("  Step 5: Review Preferences")
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


def _save_configs(api_key, provider, language, project, review):
    """Save local and global configs."""
    print()

    # 1. Save local .iara.json
    local_config = {
        "project": project,
        "review": review,
        "model": {
            "preferred": None,
            "fallback_enabled": True,
            "provider": provider
        },
        "language": language
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

    # 2. Save API key in global config (merge with existing to preserve other providers' keys)
    global_config = _load_global_config()
    global_config[f"{provider}_api_key"] = api_key
    if provider == "openrouter":
        global_config["api_key"] = api_key
    save_global_config(global_config)
    print("  Saved API key to ~/.iara/config.json")


def _show_next_steps():
    """Show next steps."""
    print()
    print("  Setup complete!")
    print()
    print("  Next steps:")
    print("    git diff main | iara          # Review a diff")
    print("    iara --scan ./src             # Scan a directory")
    print("    iara auth status              # Check auth status")
    
    # Check for RAG support
    try:
        import iara.memory.lancedb_store  # noqa
        print("    iara memory index             # Index codebase for Context-Aware Reviews 🧠")
    except ImportError:
        print("    pip install iara-reviewer[rag] # Enable Context-Aware Reviews (RAG) 🧠")
    print()


def _mask_key(key):
    """Mask key for display."""
    if len(key) > 12:
        return key[:8] + "..." + key[-4:]
    return "***"
