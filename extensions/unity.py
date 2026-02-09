"""
Extensão da Iara para Análise de Unity (C#).
Possui lógica de regex para detectar problemas comuns de performance e memória.
"""

import re

class UnityReviewer:
    def __init__(self):
        self.triggers = [
            {
                "id": "UNITY-001",
                "pattern": r"GetComponent<.*?>\(\)",
                "context_required": ["Update", "FixedUpdate", "LateUpdate"],
                "message": "⚠️ **Performance**: Evite chamar `GetComponent` dentro de loops de Update. Faça cache no `Start` ou `Awake`.",
                "severity": "Medium"
            },
            {
                "id": "UNITY-002",
                "pattern": r"Find\(.*?\)",
                "context_required": ["Update", "FixedUpdate", "LateUpdate"],
                "message": "⚠️ **Performance**: `GameObject.Find` é muito lento. Evite usar em Updates.",
                "severity": "High"
            },
            {
                "id": "UNITY-003",
                "pattern": r"new\s+string",
                "context_required": ["Update", "FixedUpdate", "LateUpdate"],
                "message": "⚠️ **GC Alloc**: Criação de strings em Update gera Garbage Collection. Use `StringBuilder`.",
                "severity": "Low"
            },
             {
                "id": "UNITY-004",
                "pattern": r"Debug\.Log",
                "context_required": ["Update", "FixedUpdate", "LateUpdate"],
                "message": "⚠️ **Performance**: `Debug.Log` em Update detona a performance (I/O). Remova ou use condicionalmente.",
                "severity": "Medium"
            }
        ]

    def scan(self, content: str, filename: str) -> list:
        """
        Escaneia o conteúdo do arquivo em busca de padrões problemáticos.
        Retorna uma lista de strings (issues).
        """
        issues = []
        
        # Otimização simples: Se não tem "Update", muitas regras não se aplicam
        # (Mas vamos varrer tudo por enquanto para ser seguro)
        
        # Divide em métodos para saber se está dentro de um Update? 
        # Regex puro é frágil para escopo. 
        # Abordagem simplificada: Se o arquivo tem "void Update" E o padrão aparece, flagar (com aviso de falso positivo).
        # Melhoria: Tentar identificar se a linha está dentro de um bloco Update (difícil com regex).
        
        # Para MVP: Se o arquivo define Update e a linha problemática existe, avisamos.
        has_update = bool(re.search(r"void\s+(Update|FixedUpdate|LateUpdate)", content))
        
        for rule in self.triggers:
            if rule.get("context_required") and not has_update:
                continue
                
            matches = re.finditer(rule["pattern"], content)
            for match in matches:
                # Se achou o padrão, e estamos num arquivo com Update (pressuposto fraco, mas válido para MVP de scan rápido)
                # Idealmente checaríamos a linha.
                issues.append(f"{rule['message']} (Detectado em {filename})")
                
        return issues

