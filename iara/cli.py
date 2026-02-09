"""Interface de linha de comando da Iara."""

import os
import sys
import argparse

from iara.config import load_config
from iara.reviewer import review_code
from iara.scanner import scan_directory


def main():
    """Ponto de entrada principal."""
    parser = argparse.ArgumentParser(description="Iara - AI Code Reviewer")
    parser.add_argument("--scan", help="Diretório para escanear (Modo Scan)", default=None)
    parser.add_argument("--diff", help="Arquivo de diff (opcional, lê de stdin por padrão)", default=None)
    args = parser.parse_args()

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ Erro: OPENROUTER_API_KEY não configurada.", file=sys.stderr)
        sys.exit(1)

    # Carrega configuracoes
    config = load_config()

    # Modo Scan
    if args.scan:
        if not os.path.isdir(args.scan):
             print(f"❌ Erro: Diretório '{args.scan}' não encontrado.", file=sys.stderr)
             sys.exit(1)

        print(f"🚀 Iniciando modo SCAN em: {args.scan}", file=sys.stderr)
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
        print("Use: `git diff | iara` ou `iara --scan <dir>`", file=sys.stderr)
        sys.exit(0)

    review = review_code(diff, api_key, config)
    print(review)
