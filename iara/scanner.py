"""Directory scanning with static analysis via extensions."""

import os
import sys
import re


def scan_directory(directory: str, config: dict) -> str:
    """
    Recursively scan a directory for relevant files
    and apply static analysis rules (Regex) or LLM (if configured).
    """
    project_stack = config.get("project", {}).get("tech_stack", [])

    # Determine file extensions to search based on stack
    extensions = []
    if "Unity" in project_stack or "C#" in project_stack:
        extensions.append(".cs")
    if "Python" in project_stack:
        extensions.append(".py")

    if not extensions:
        return "⚠️ No relevant extensions configured for scan analysis (based on tech_stack)."

    # Scanning Loop
    issues = []

    # Load extensions
    extensions_loaded = []
    if ".cs" in extensions:
        try:
            from iara.extensions.unity import UnityReviewer
            extensions_loaded.append(UnityReviewer())
        except ImportError:
            print("⚠️ Extension 'iara.extensions.unity' not found.", file=sys.stderr)

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
                     print(f"Error reading {filepath}: {e}", file=sys.stderr)

    if not issues:
        return "✅ No critical issues found during scan."

    return "🚨 **Scan Results:**\n\n" + "\n".join(issues)
