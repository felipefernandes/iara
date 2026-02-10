"""Authentication status command for Iara."""

import os
import sys
from iara.auth import resolve_api_key, validate_api_key, PROVIDER_ENV_VARS
from iara.config import load_config


def run_auth_status():
    """Show current authentication status."""
    config = load_config()
    env_provider = os.environ.get("IARA_PROVIDER")
    provider = env_provider.lower() if env_provider else config.get("model", {}).get("provider", "openrouter")

    api_key, source = resolve_api_key(provider)

    print()
    print("  Iara Auth Status")
    print("  " + "=" * 20)
    print()

    if not api_key:
        print("  Status: NOT CONFIGURED")
        print()
        print("  To configure, run:")
        print("    iara init")
        print("  Or set the environment variable:")
        env_var = PROVIDER_ENV_VARS.get(provider, "OPENROUTER_API_KEY")
        print("    export %s='sk-...'" % env_var)
        print()
        sys.exit(1)

    # Mask the key
    if len(api_key) > 12:
        masked = api_key[:8] + "..." + api_key[-4:]
    else:
        masked = "***"

    env_var = PROVIDER_ENV_VARS.get(provider, "OPENROUTER_API_KEY")
    source_labels = {
        "env": "Environment variable (%s)" % env_var,
        "config": "Global config (~/.iara/config.json)"
    }

    print("  Provider: %s" % provider)
    print("  Key:      %s" % masked)
    print("  Source:   %s" % source_labels.get(source, source))
    print()

    # Validate
    if provider == "openrouter":
        print("  Validating...", end=" ", flush=True)
        is_valid, error = validate_api_key(api_key, provider)
        if is_valid:
            print("VALID")
        else:
            print("INVALID (%s)" % error)
            sys.exit(1)
    else:
        print("  Validation: SKIPPED (provider not validated locally)")

    print()
