# Iara - AI Code Reviewer 🧜‍♀️

Iara é uma ferramenta de revisão de código automatizada, agnóstica a projetos e configurável, projetada para rodar em pipelines de CI/CD ou localmente via CLI. Ela utiliza a API OpenRouter para acessar diversos modelos de LLM (Llama 3, Gemini 2.0, etc.) gratuitamente ou em planos pagos.

## 🚀 Funcionalidades

- **Agnóstica**: Configure o contexto do seu projeto (Tech Stack, Regras) via JSON.
- **Multi-Modelo**: Suporte a múltiplos provedores via OpenRouter.
- **Fallback Inteligente**: Tenta modelos gratuitos automaticamente se o preferido falhar.
- **Rules-Based (Estático)**: Identifica padrões perigosos instantaneamente sem gastar tokens (ex: `GetComponent` em loops no Unity).
- **LLM-Based (Inteligente)**: Usa IA para entender a lógica, segurança e contexto, indo além da sintaxe.
- **GitHub + GitLab**: Integração nativa com ambas as plataformas, com comentários automáticos em PRs/MRs.

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

---

## 📦 Instalação

### Via pip (Recomendado)

```bash
pip install iara-reviewer
```

Após instalar, o comando `iara` fica disponível globalmente:

```bash
git diff main | iara
```

### Via clone (Desenvolvimento)

```bash
git clone https://github.com/felipefernandes/iara.git
cd iara
pip install -e .
```

### Configurar chave de API

```bash
# Linux/Mac
export OPENROUTER_API_KEY="sk-or-..."

# Windows (PowerShell)
$env:OPENROUTER_API_KEY="sk-or-..."
```

Obtenha sua chave gratuita em [openrouter.ai](https://openrouter.ai/).

---

## ⚙️ Configuração

Crie um arquivo `.iara.json` na raiz do seu projeto:

```json
{
  "project": {
    "name": "Meu Projeto",
    "description": "Descrição do projeto.",
    "tech_stack": ["Python"]
  },
  "review": {
    "focus_areas": ["Performance", "Security"],
    "ignore_patterns": []
  },
  "model": {
    "preferred": "google/gemini-2.0-flash-exp:free",
    "fallback_enabled": true
  }
}
```

Exemplo pronto disponível em `iara-example.json`.

---

## 🏃 Como Usar

### Via Pipe (Git Diff)

```bash
git diff main | iara
```

### Via Variável de Ambiente

```bash
export PR_DIFF=$(git diff main)
iara
```

### Modo Scan (Análise Estática)

```bash
iara --scan ./caminho/do/projeto
```

### Forçando um Modelo

```bash
export IARA_MODEL="meta-llama/llama-3.2-3b-instruct:free"
git diff | iara
```

### Retrocompatibilidade

O script `ai-codereview.py` continua funcionando para quem já o utiliza:

```bash
git diff | python ai-codereview.py
```

---

## 🐙 Integração GitHub

Adicione a Iara ao seu repositório GitHub em **2 passos**:

### 1. Configurar o secret

Vá em **Settings > Secrets and variables > Actions > New repository secret** e adicione:

- Nome: `OPENROUTER_API_KEY`
- Valor: sua chave da API OpenRouter

### 2. Criar o workflow

Crie o arquivo `.github/workflows/iara-review.yml`:

```yaml
name: Iara Code Review

on:
  pull_request:
    types: [opened, synchronize]

permissions:
  pull-requests: write
  contents: read

jobs:
  review:
    runs-on: ubuntu-latest
    name: AI Code Review
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Run Iara Code Review
        uses: felipefernandes/iara@v1
        with:
          openrouter_api_key: ${{ secrets.OPENROUTER_API_KEY }}
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

A Iara vai automaticamente:

- Revisar o diff do Pull Request
- Postar um comentário com o resultado da review

### Opções adicionais

```yaml
- uses: felipefernandes/iara@v1
  with:
    openrouter_api_key: ${{ secrets.OPENROUTER_API_KEY }}
    model: 'google/gemini-2.0-flash-exp:free'   # Forçar modelo
    config_path: '.iara.json'                     # Caminho do config
    post_comment: 'true'                          # Postar comentário (default: true)
```

---

## 🦊 Integração GitLab

### 1. Configurar variáveis

Vá em **Settings > CI/CD > Variables** e adicione:

- `OPENROUTER_API_KEY`: Chave da API OpenRouter
- `GITLAB_TOKEN`: Personal/Project Access Token com scope `api` (necessário para comentários no MR)

### 2. Adicionar ao `.gitlab-ci.yml`

```yaml
stages:
  - review

iara_code_review:
  stage: review
  image: python:3.11-slim
  script:
    - apt-get update && apt-get install -y --no-install-recommends git curl
    - pip install iara-reviewer
    - git fetch origin $CI_MERGE_REQUEST_TARGET_BRANCH_NAME
    - export PR_DIFF=$(git diff origin/$CI_MERGE_REQUEST_TARGET_BRANCH_NAME...$CI_COMMIT_SHA)
    - REVIEW=$(iara 2>/tmp/iara_stderr.txt) || true
    - echo "$REVIEW"
    - |
      if [ -n "$REVIEW" ] && [ -n "$GITLAB_TOKEN" ]; then
        PAYLOAD=$(python3 -c "
      import sys, json
      review = '''$REVIEW'''
      body = '## 🧜‍♀️ Iara Code Review\n\n' + review + '\n\n---\n*Reviewed by Iara - AI Code Reviewer*'
      print(json.dumps({'body': body}))
      ")
        curl -s -X POST \
          -H "PRIVATE-TOKEN: $GITLAB_TOKEN" \
          -H "Content-Type: application/json" \
          -d "$PAYLOAD" \
          "${CI_API_V4_URL}/projects/${CI_PROJECT_ID}/merge_requests/${CI_MERGE_REQUEST_IID}/notes"
      fi
  allow_failure: true
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
```

A Iara vai automaticamente:

- Revisar o diff do Merge Request
- Postar um comentário com o resultado da review no MR

Um template completo está disponível em `gitlab-ci.yml`.

---

## 🔧 Qualquer CI (Jenkins, CircleCI, etc.)

```bash
pip install iara-reviewer
export OPENROUTER_API_KEY="sk-or-..."
git diff main...HEAD | iara
```

---

## 🧪 Testes

```bash
python -m unittest discover tests
```

## 📜 Licença

MIT
