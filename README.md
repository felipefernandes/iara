# Iara - AI Code Reviewer 🧜‍♀️

Iara é uma ferramenta de revisão de código automatizada, agnóstica a projetos e configurável, projetada para rodar em pipelines de CI/CD ou localmente via CLI. Ela utiliza a API OpenRouter para acessar diversos modelos de LLM (Llama 3, Gemini 2.0, etc.) gratuitamente ou em planos pagos.

## 🚀 Funcionalidades

- **Agnóstica**: Configure o contexto do seu projeto (Tech Stack, Regras) via JSON.
- **Multi-Modelo**: Suporte a múltiplos provedores via OpenRouter.
- **Fallback Inteligente**: Tenta modelos gratuitos automaticamente se o preferido falhar.
- **Rules-Based (Estático)**: Identifica padrões perigosos instantaneamente sem gastar tokens (ex: `GetComponent` em loops no Unity).
- **LLM-Based (Inteligente)**: Usa IA para entender a lógica, segurança e contexto, indo além da sintaxe.

## 🧠 Capacidades

A Iara combina diferentes tipos de análise para uma revisão completa:

| Tipo | O que faz? | A Iara cobre? | Como? |
| :--- | :--- | :--- | :--- |
| **Análise Estática** | Caça bugs lendo o código (rápido). | ✅ **Sim** | Via Extensões (Regex) e LLM. |
| **Linting** | Corrige estilo e formatação. | ✅ **Sim** | LLM pode sugerir *Clean Code*. |
| **SAST** | Caça falhas de segurança no código. | ✅ **Sim** | Foco primário na busca por vulnerabilidades. |
| **Análise Dinâmica** | Caça bugs rodando o app (lento). | ❌ Não | Foco em CI/CD rápido (Code Review). |

### O que ela detecta?

1.  **Unity / Game Dev**:
    - Uso de APIs lentas (`Find`, `GetComponent`) em loops críticos (`Update`).
    - Alocação excessiva de memória (Garbage Collection).
    - Excesso de logs (`Debug.Log`) em builds finais.

2.  **Segurança (Geral)**:
    - Credenciais hardcoded (Senhas, API Keys).
    - Vulnerabilidades de Injeção (SQL, Command).
    - Falta de validação de inputs.

3.  **Qualidade de Código**:
    - Lógica complexa ou confusa.
    - Erros de tratamento de exceções.
    - Sugestões de refatoração para legibilidade.

## 📦 Instalação

1. Clone o repositório:
   ```bash
   git clone https://github.com/seu-usuario/iara-bot-reviewer.git
   cd iara-bot-reviewer
   ```

2. Configure a chave de API (OpenRouter):
   ```bash
   # Linux/Mac
   export OPENROUTER_API_KEY="sk-or-..."
   
   # Windows (PowerShell)
   $env:OPENROUTER_API_KEY="sk-or-..."
   ```

## ⚙️ Configuração

Crie um arquivo `.iara.json` na raiz do seu projeto. Você pode copiar o exemplo:

```bash
cp iara-example.json .iara.json
```

### Exemplo de `.iara.json`:

```json
{
  "project": {
    "name": "Meu Jogo Unity",
    "description": "Um RPG mobile feito em Unity.",
    "tech_stack": ["C#", "Unity", "Android"]
  },
  "review": {
    "focus_areas": ["Performance", "Memory Management"],
    "ignore_patterns": ["Assets/Plugins/*"]
  },
  "model": {
    "preferred": "google/gemini-2.0-flash-exp:free",
    "fallback_enabled": true
  }
}
```

## 🏃 Como Usar

### Via Pipe (Git Diff)

A forma mais comum de uso é enviando um diff via stdin:

```bash
git diff main | python ai-codereview.py
```

### Via Variável de Ambiente

Você também pode passar o diff via variável `PR_DIFF`:

```bash
# Windows PowerShell
$env:PR_DIFF = git diff main | Out-String
python ai-codereview.py
```

### Modo Scan
Para analisar um diretório inteiro (útil para código legado ou análise estática):

```bash
python ai-codereview.py --scan ./caminho/do/projeto
```

Isso ativará extensões locais (como a de Unity) para identificar problemas sem gastar tokens de LLM desnecessariamente.

### Via Forçando um Modelo

Você pode sobrescrever o modelo configurado via variável de ambiente:

```bash
# Usa apenas o modelo especificado, sem fallback
$env:IARA_MODEL="meta-llama/llama-3.2-3b-instruct:free"
git diff | python ai-codereview.py
```


## 🦊 GitLab CI

Adicione o seguinte job ao seu `.gitlab-ci.yml`:

```yaml
review:
  image: python:3.11-slim
  script:
    - apt-get update && apt-get install -y git
    - git fetch origin main
    - export PR_DIFF=$(git diff origin/main...HEAD)
    - python ai-codereview.py
  rules:
    - if: $CI_MERGE_REQUEST_ID
```
## 🧪 Testes

Para rodar os testes unitários:

```bash
python -m unittest discover tests
```

## 📜 Licença

MIT
