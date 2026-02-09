"""Scanning de diretorio com analise estatica via extensoes."""

import os
import sys
import re


def scan_directory(directory: str, config: dict) -> str:
    """
    Escaneia um diretorio recursivamente buscando arquivos relevantes
    e aplicando regras de analise estatica (Regex) ou LLM (se configurado).
    """
    project_stack = config.get("project", {}).get("tech_stack", [])

    # Determina extensoes a buscar com base na stack
    extensions = []
    if "Unity" in project_stack or "C#" in project_stack:
        extensions.append(".cs")
    if "Python" in project_stack:
        extensions.append(".py")

    if not extensions:
        return "⚠️ Nenhuma extensão relevante configurada para análise de scan (baseado na tech_stack)."

    # Scanning Loop
    issues = []

    # Carrega extensoes
    extensions_loaded = []
    if ".cs" in extensions:
        try:
            from iara.extensions.unity import UnityReviewer
            extensions_loaded.append(UnityReviewer())
        except ImportError:
            print("⚠️ Extensão 'iara.extensions.unity' não encontrada.", file=sys.stderr)

    # scan
    for root, _, files in os.walk(directory):
        for file in files:
            filepath = os.path.join(root, file)

            # UNITY / .CS
            if file.endswith(".cs") and ".cs" in extensions:
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()

                    for ext in extensions_loaded:
                        if hasattr(ext, 'scan'):
                            found_issues = ext.scan(content, file)
                            issues.extend(found_issues)

                except Exception as e:
                     print(f"Erro ao ler {filepath}: {e}", file=sys.stderr)

    if not issues:
        return "✅ Nenhum problema crítico encontrado durante o scan."

    return "🚨 **Resultados do Scan:**\n\n" + "\n".join(issues)
