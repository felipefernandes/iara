"""
Iara extension for Unity (C#) analysis.
Regex-based detection of common performance and memory issues.
"""

import re

class UnityReviewer:
    def __init__(self):
        self.triggers = [
            {
                "id": "UNITY-001",
                "pattern": r"GetComponent<.*?>\(\)",
                "context_required": ["Update", "FixedUpdate", "LateUpdate"],
                "message": "⚠️ **Performance**: Avoid calling `GetComponent` inside Update loops. Cache it in `Start` or `Awake`.",
                "severity": "Medium"
            },
            {
                "id": "UNITY-002",
                "pattern": r"Find\(.*?\)",
                "context_required": ["Update", "FixedUpdate", "LateUpdate"],
                "message": "⚠️ **Performance**: `GameObject.Find` is very slow. Avoid using it in Updates.",
                "severity": "High"
            },
            {
                "id": "UNITY-003",
                "pattern": r"new\s+string",
                "context_required": ["Update", "FixedUpdate", "LateUpdate"],
                "message": "⚠️ **GC Alloc**: String allocation in Update causes Garbage Collection. Use `StringBuilder`.",
                "severity": "Low"
            },
             {
                "id": "UNITY-004",
                "pattern": r"Debug\.Log",
                "context_required": ["Update", "FixedUpdate", "LateUpdate"],
                "message": "⚠️ **Performance**: `Debug.Log` in Update kills performance (I/O). Remove or use conditionally.",
                "severity": "Medium"
            }
        ]

    def scan(self, content: str, filename: str) -> list:
        """
        Scan file content for problematic patterns.
        Returns a list of issue strings.
        """
        issues = []

        # MVP: If the file defines Update and a problematic line exists, flag it.
        has_update = bool(re.search(r"void\s+(Update|FixedUpdate|LateUpdate)", content))

        for rule in self.triggers:
            if rule.get("context_required") and not has_update:
                continue

            matches = re.finditer(rule["pattern"], content)
            for match in matches:
                issues.append(f"{rule['message']} (Detected in {filename})")

        return issues
