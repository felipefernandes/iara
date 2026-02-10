"""Interface de linha de comando da Iara."""

import os
import sys
import argparse

from iara.config import load_config
from iara.reviewer import review_code
from iara.scanner import scan_directory
from iara.auth import resolve_api_key


def main():
    """Ponto de entrada principal."""
    parser = argparse.ArgumentParser(
        description="Iara - AI Code Reviewer",
        usage="iara [command] [options]"
    )

    # Argumentos top-level (retrocompatibilidade)
    parser.add_argument("--scan", help="Diretório para escanear (Modo Scan)", default=None)
    parser.add_argument("--diff", help="Arquivo de diff (opcional, lê de stdin por padrão)", default=None)

    # Subcomandos
    subparsers = parser.add_subparsers(dest="command")
    subparsers.required = False

    # iara init
    subparsers.add_parser("init", help="Setup interativo (API key + config do projeto)")

    # iara auth
    auth_parser = subparsers.add_parser("auth", help="Gerenciamento de autenticacao")
    auth_sub = auth_parser.add_subparsers(dest="auth_command")
    auth_sub.required = False
    auth_sub.add_parser("status", help="Verificar status da autenticacao")

    args = parser.parse_args()

    # --- Roteamento de subcomandos ---
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

    # --- Fluxo existente de review (sem subcomando) ---
    api_key, source = resolve_api_key()
    if not api_key:
        print("❌ Erro: API key não configurada.", file=sys.stderr)
        print("Execute 'iara init' para configurar, ou defina OPENROUTER_API_KEY.", file=sys.stderr)
        sys.exit(1)

    # Carrega configuracoes
    config = load_config()

    # Modo Scan
    if args.scan:
        if not os.path.isdir(args.scan):
             print("❌ Erro: Diretório '%s' não encontrado." % args.scan, file=sys.stderr)
             sys.exit(1)

        print("🚀 Iniciando modo SCAN em: %s" % args.scan, file=sys.stderr)
        result = scan_directory(args.scan, config)
        print(result)
        return

    # Modo Diff (Legacy/Default)
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
        print("ℹ️ Nenhuma entrada de código detectada (stdin vazio, sem PR_DIFF, sem --scan).", file=sys.stderr)
        print("Use: `git diff | iara` ou `iara --scan <dir>` ou `iara init`", file=sys.stderr)
        sys.exit(0)

    review = review_code(diff, api_key, config)
    print(review)
