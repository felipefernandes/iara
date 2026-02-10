"""Comando de status de autenticacao da Iara."""

import sys
from iara.auth import resolve_api_key, validate_api_key


def run_auth_status():
    """Mostra o status atual de autenticacao."""
    api_key, source = resolve_api_key()

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
        print("    export OPENROUTER_API_KEY='sk-or-...'")
        print()
        sys.exit(1)

    # Mascara a key
    if len(api_key) > 12:
        masked = api_key[:8] + "..." + api_key[-4:]
    else:
        masked = "***"

    source_labels = {
        "env": "Environment variable (OPENROUTER_API_KEY)",
        "config": "Global config (~/.iara/config.json)"
    }

    print("  Key:    %s" % masked)
    print("  Source: %s" % source_labels.get(source, source))
    print()

    # Valida
    print("  Validating...", end=" ", flush=True)
    is_valid, error = validate_api_key(api_key)
    if is_valid:
        print("VALID")
    else:
        print("INVALID (%s)" % error)
        sys.exit(1)

    print()
