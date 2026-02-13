"""Command-line interface for Iara."""

import os
import sys
import argparse

# Try loading .env if it exists
if os.path.exists(".env"):
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print("⚠️ Warning: .env file detected but 'python-dotenv' is not installed. Variables may not be loaded.", file=sys.stderr)
        print("   Run: pip install python-dotenv", file=sys.stderr)

from iara.config import load_config
from iara.reviewer import review_code
from iara.scanner import scan_directory
from iara.auth import resolve_api_key, PROVIDER_ENV_VARS, normalize_provider, SUPPORTED_PROVIDERS


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Iara - AI Code Reviewer",
        usage="iara [command] [options]"
    )

    # Top-level arguments (backward compatibility)
    parser.add_argument("--scan", help="Directory to scan (Scan Mode)", default=None)
    parser.add_argument("--diff", help="Diff file (optional, reads from stdin by default)", default=None)

    # Subcommands
    subparsers = parser.add_subparsers(dest="command")
    subparsers.required = False

    # iara init
    subparsers.add_parser("init", help="Interactive setup (API key + project config)")

    # iara auth
    auth_parser = subparsers.add_parser("auth", help="Authentication management")
    auth_sub = auth_parser.add_subparsers(dest="auth_command")
    auth_sub.required = False
    auth_sub.add_parser("status", help="Check authentication status")

    # iara memory
    memory_parser = subparsers.add_parser("memory", help="Memory management (RAG)")
    memory_sub = memory_parser.add_subparsers(dest="memory_command")
    memory_sub.required = False
    memory_sub.add_parser("index", help="Index the current directory").add_argument("--force", action="store_true", help="Force re-indexing of all files")
    memory_sub.add_parser("clear", help="Clear the memory index")

    args = parser.parse_args()


    # --- Subcommand routing ---
    if args.command == "init":
        from iara.init import run_init
        run_init()
        return

    if args.command == "auth":
        if args.auth_command == "status":
            from iara.auth_status import run_auth_status
            run_auth_status()
            return
        else:
            auth_parser.print_help()
            return




    if args.command == "memory":
        try:
            from iara.memory.lancedb_store import LanceDBMemory
            from iara.memory.indexer import Indexer
            
            # TODO: Make persistence path configurable via .iara.json
            memory = LanceDBMemory()
        except ImportError:
            print("❌ RAG dependencies not installed. Run `pip install iara-reviewer[rag]`", file=sys.stderr)
            sys.exit(1)

        if args.memory_command == "index":
            indexer = Indexer(memory)
            print(f"🧠 Indexing codebase in {os.getcwd()}...", file=sys.stderr)
            indexer.index_project(os.getcwd(), force=getattr(args, 'force', False))
            print("✅ Indexing complete.", file=sys.stderr)
        elif args.memory_command == "clear":
            memory.clear()
            print("🗑️ Memory cleared.", file=sys.stderr)
        else:
            memory_parser.print_help()
        return

    # Load config
    config = load_config()

    # Provider override from env var if set
    env_provider = os.environ.get("IARA_PROVIDER")
    if env_provider:
        config.setdefault("model", {})["provider"] = env_provider

    # Override language from env var if set
    env_lang = os.environ.get("IARA_LANGUAGE")
    if env_lang:
        config["language"] = env_lang

    # Resolve API key for selected provider
    provider = config.get("model", {}).get("provider", "openrouter")
    provider = normalize_provider(provider)
    if not provider:
        supported = ", ".join(sorted(SUPPORTED_PROVIDERS))
        print("❌ Error: Invalid provider configured.", file=sys.stderr)
        print("Supported providers: %s" % supported, file=sys.stderr)
        sys.exit(1)

    api_key, source = resolve_api_key(provider)
    if not api_key:
        env_var = PROVIDER_ENV_VARS.get(provider, "OPENROUTER_API_KEY")
        print("❌ Error: API key not configured.", file=sys.stderr)
        print("Run 'iara init' to set up, or set %s." % env_var, file=sys.stderr)
        sys.exit(1)

    # Scan Mode
    if args.scan:
        if not os.path.isdir(args.scan):
             print("❌ Error: Directory '%s' not found." % args.scan, file=sys.stderr)
             sys.exit(1)

        print("🚀 Starting SCAN mode on: %s" % args.scan, file=sys.stderr)
        result = scan_directory(args.scan, config)
        print(result)
        return

    # Diff Mode (Legacy/Default)
    diff = os.environ.get("PR_DIFF", "")
    if args.diff:
         if os.path.exists(args.diff):
             with open(args.diff, "r", encoding="utf-8") as f:
                 diff = f.read()
         else:
             diff = args.diff

    if not diff:
        # Check if stdin has data
        if not sys.stdin.isatty():
            diff = sys.stdin.read()

    if not diff:
        print("ℹ️ No code input detected (empty stdin, no PR_DIFF, no --scan).", file=sys.stderr)
        print("Use: `git diff | iara` or `iara --scan <dir>` or `iara init`", file=sys.stderr)
        sys.exit(0)

    review = review_code(diff, api_key, config)
    print(review)
