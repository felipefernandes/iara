#!/usr/bin/env python3
"""
Iara - Revisora de Código
Script para revisão automatizada de código usando IA via OpenRouter (Modelos Gratuitos).
"""

import os
import sys
import json
import urllib.request
import urllib.error
import time
import re

# Configuração da API OpenRouter
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Lista simplificada de modelos gratuitos e meta-modelos
FREE_MODELS = [
    "google/gemini-2.0-flash-exp:free", # Modelo experimental rápido e gratuito
    "google/gemini-2.0-pro-exp-02-05:free", # Modelo Pro experimental
    "meta-llama/llama-3.2-3b-instruct:free", # Llama 3.2 (leve e rápido)
    "microsoft/phi-3-mini-128k-instruct:free", # Phi-3 (backup)
    "openrouter/free" # Meta-modelo como última opção
]

# Configuração Padrão (Genérica)
DEFAULT_CONFIG = {
    "project": {
        "name": "Projeto Genérico",
        "description": "Um projeto de software.",
        "tech_stack": ["Python"]
    },
    "review": {
        "focus_areas": ["Logic", "Security", "Performance"],
        "ignore_patterns": []
    },
    "model": {
        "preferred": None,
        "fallback_enabled": True
    }
}

def load_config(config_path: str = ".iara.json") -> dict:
    """Carrega a configuração do arquivo JSON ou retorna o padrão."""
    if not os.path.exists(config_path):
        return DEFAULT_CONFIG
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            user_config = json.load(f)
            # Merge superficial (pode ser melhorado para deep merge futuramente)
            config = DEFAULT_CONFIG.copy()
            config.update(user_config)
            return config
    except json.JSONDecodeError:
        print(f"⚠️ Erro ao ler {config_path}. Usando configuração padrão.", file=sys.stderr)
        return DEFAULT_CONFIG

def generate_system_prompt(config: dict) -> str:
    """Gera o prompt do sistema dinamicamente com base na configuração."""
    project = config.get("project", {})
    name = project.get("name", "Projeto Desconhecido")
    desc = project.get("description", "Sem descrição.")
    stack = project.get("tech_stack", [])
    
    # Construção das regras específicas por stack
    stack_rules = ""
    if "Unity" in stack or "C#" in stack:
        stack_rules += "- **Unity/C#**: Evite `GetComponent` em `Update`. Use `StringBuilder` para strings. Cuidado com Garbage Collection.\n"
    if "Python" in stack:
        stack_rules += "- **Python**: Siga PEP 8. Use `with` para lidar com arquivos. Evite imports circulares.\n"
    if "Raspberry Pi" in stack:
        stack_rules += "- **IoT/Raspberry Pi**: Otimize para hardware limitado (1GB RAM). Evite dependências pesadas.\n"

    return f"""Você é Iara, a revisora de código oficial do projeto **{name}**.
Sua missão é revisar código focando em **Lógica, Segurança e Performance**.

## CONTEXTO DO PROJETO:
{desc}

## TECNOLOGIAS E REGRAS:
Stack: {', '.join(stack)}
{stack_rules}

## CHECKLIST DE REVISÃO:

### 🐛 BUGS REAIS (Foco Principal)
- Erros de lógica (ex: contas erradas, condições inatingíveis).
- Tratamento de exceções ausente.
- Deadlocks ou loops infinitos.

### 🔒 SEGURANÇA
- Secrets hardcoded.
- Injection flaws (SQL, Command).
- Validação de entrada de usuário ausente.

### ⚡ PERFORMANCE
- Loops ineficientes.
- Queries N+1.
- Uso excessivo de memória.

### ❌ O QUE IGNORAR (Falsos Positivos):
- Não reclame de estilo se não afetar a legibilidade gravemente.
- Não reclame de variáveis globais se forem convenção do projeto (ex: configs).

## FORMATO DA RESPOSTA:
Seja direta e objetiva. Use emojis para categorizar.
- 🐛 **Bug**: Problema lógico.
- 🔒 **Segurança**: Risco de segurança.
- ⚡ **Performance**: Ineficiência.
- 🧹 **Clean Code**: Sugestão de legibilidade (opcional).

✅ **Se estiver tudo ok**: "✅ **Aprovação Iara**: Código robusto e alinhado ao projeto {name}. Pode mergear! 🧜‍♀️✨"
"""


def review_code_with_model(diff: str, api_key: str, model: str, system_prompt: str) -> str:
    """Tenta revisar com um modelo específico."""
    max_chars = 15000
    if len(diff) > max_chars:
        diff = diff[:max_chars] + "\n\n[... diff truncado por limite de tamanho ...]"
    
    # Payload simplificado
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Revise o seguinte diff de código:\n\n```diff\n{diff}\n```"}
        ],
        "temperature": 0.3, # Baixa temperatura é seguro
        "max_tokens": 6000, # Limite aumentado para evitar cortes (suporta DeepSeek R1 e Llama 3)
        # Headers HTTP Referer e X-Title são passados nos headers da request, não no payload json
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://github.com/felipefernandes/curupira",
        "X-Title": "Curupira Iara Reviewer"
    }
    
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(OPENROUTER_API_URL, data=data, headers=headers)
        
        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))
            if "error" in result:
                 raise Exception(f"API Error: {result['error']}")
            
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
                
                # Strip <think> blocks (Common in DeepSeek R1)
                content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
                
                if not content:
                    raise ValueError("Modelo retornou conteúdo vazio (ou apenas tags <think>).")

                return content
            else:
                raise ValueError("API retornou sucesso mas sem 'choices'.")

    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        raise Exception(f"HTTP Error {e.code}: {error_body}")


def review_code(diff: str, api_key: str, config: dict) -> str:
    """
    Executa a revisão de código tentando o modelo configurado ou fallback.
    """
    if not diff.strip():
        return "✅ Nenhuma alteração de código para revisar."
    
    system_prompt = generate_system_prompt(config)
    
    # Determina qual modelo usar
    preferred_model = os.environ.get("IARA_MODEL") or config.get("model", {}).get("preferred")
    fallback_enabled = config.get("model", {}).get("fallback_enabled", True)
    
    models_to_try = []
    
    if preferred_model:
        models_to_try.append(preferred_model)
    
    if fallback_enabled or not preferred_model:
        # Adiciona modelos gratuitos apenas se ainda não estiverem na lista (evita duplicatas e garante ordem)
        for m in FREE_MODELS:
            if m not in models_to_try:
                models_to_try.append(m)
    
    # Se o usuário forçou um modelo via ENV e fallback está desativado (implícito se preferido falhar? Não, spec diz 'bypassing default fallback list')
    # Ajuste: Se IARA_MODEL via ENV estiver setado, a spec diz: "MUST attempt to use ONLY that model"
    # Então vamos refinar a lógica acima.
    
    env_model = os.environ.get("IARA_MODEL")
    if env_model:
        models_to_try = [env_model] # Override total
    
    errors = []
    
    print(f"🔄 Iniciando revisão. Modelos na fila: {models_to_try}", file=sys.stderr)
    
    for model in models_to_try:
        try:
            print(f"🔄 Tentando modelo: {model}...", file=sys.stderr)
            return review_code_with_model(diff, api_key, model, system_prompt)
        except (urllib.error.HTTPError, urllib.error.URLError) as e:
            error_msg = str(e)
            print(f"⚠️ Falha de conexão/HTTP no modelo {model}: {error_msg}", file=sys.stderr)
            errors.append(f"{model}: {error_msg}")
            time.sleep(1)
        except Exception as e:
            error_msg = str(e)
            print(f"⚠️ Erro inesperado no modelo {model}: {error_msg}", file=sys.stderr)
            errors.append(f"{model}: {error_msg}")
            time.sleep(1)
            
            # Se for o modelo forçado via ENV, não devemos continuar tentando outros (a menos que a lista tenha outros, mas no caso de ENV override só tem 1)
            if env_model:
                break
            
    return f"❌ Não foi possível revisar com nenhum modelo disponível.\nErros:\n" + "\n".join(errors)




def scan_directory(directory: str, config: dict) -> str:
    """
    Escaneia um diretório recursivamente buscando arquivos relevantes
    e aplicando regras de análise estática (Regex) ou LLM (se configurado).
    """
    project_stack = config.get("project", {}).get("tech_stack", [])
    
    # Determina extensões a buscar com base na stack
    extensions = []
    if "Unity" in project_stack or "C#" in project_stack:
        extensions.append(".cs")
    if "Python" in project_stack:
        extensions.append(".py")
    
    if not extensions:
        return "⚠️ Nenhuma extensão relevante configurada para análise de scan (baseado na tech_stack)."
    
    # 3. Scanning Loop (Novo)
    # -----------------------
    issues = []
    
    # Carrega extensões
    extensions_loaded = []
    if ".cs" in extensions:
        # Importação dinâmica simples para MVP
        try:
            from extensions.unity import UnityReviewer
            extensions_loaded.append(UnityReviewer())
        except ImportError:
            print("⚠️ Extensão 'extensions.unity' não encontrada.", file=sys.stderr)
    
    # scan
    for root, _, files in os.walk(directory):
        for file in files:
            filepath = os.path.join(root, file)
            
            # UNITY /.CS
            if file.endswith(".cs") and ".cs" in extensions:
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    for ext in extensions_loaded:
                        if hasattr(ext, 'scan'): # Duck typing
                            found_issues = ext.scan(content, file)
                            issues.extend(found_issues)
                            
                except Exception as e:
                     print(f"Erro ao ler {filepath}: {e}", file=sys.stderr)

    if not issues:
        return "✅ Nenhum problema crítico encontrado durante o scan."
    
    return "🚨 **Resultados do Scan:**\n\n" + "\n".join(issues)

def main():
    """Ponto de entrada principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Iara - AI Code Reviewer")
    parser.add_argument("--scan", help="Diretório para escanear (Modo Scan)", default=None)
    parser.add_argument("--diff", help="Arquivo de diff (opcional, lê de stdin por padrão)", default=None)
    args = parser.parse_args()

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ Erro: OPENROUTER_API_KEY não configurada.", file=sys.stderr)
        sys.exit(1)
        
    # Carrega configurações
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
             diff = args.diff # Treat as raw string if file doesn't exist? No, probably a file path
    
    if not diff:
        # Check if stdin has data
        if not sys.stdin.isatty():
            diff = sys.stdin.read()
    
    # If still no diff, check config or just exit
    if not diff:
        print("ℹ️ Nenhuma entrada de código detectada (stdin vazio, sem PR_DIFF, sem --scan).", file=sys.stderr)
        print("Use: `git diff | python ai-codereview.py` ou `python ai-codereview.py --scan <dir>`", file=sys.stderr)
        sys.exit(0)
    
    review = review_code(diff, api_key, config)
    print(review)


if __name__ == "__main__":
    main()
