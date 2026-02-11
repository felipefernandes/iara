# Iara - AI Code Reviewer 🧜‍♀️

![Iara - AI Code Review Agent](.assets/iara-github-banner.png)

🇺🇸 [Read in English](README.md)

Iara é uma ferramenta de revisão de código automatizada, agnóstica a projetos e configurável, projetada para rodar em pipelines de CI/CD ou localmente via CLI. Ela se conecta diretamente ao provedor de LLM de sua escolha — OpenRouter (modelos gratuitos), OpenAI, Google Gemini ou Anthropic Claude.

---

[![🧜‍♀️ Iara Code Review](https://github.com/felipefernandes/iara/actions/workflows/iara-review.yml/badge.svg)](https://github.com/felipefernandes/iara/actions/workflows/iara-review.yml) [![🧪 Tests](https://github.com/felipefernandes/iara/actions/workflows/tests.yml/badge.svg)](https://github.com/felipefernandes/iara/actions/workflows/tests.yml) [![codecov](https://codecov.io/gh/felipefernandes/iara/branch/main/graph/badge.svg)](https://codecov.io/gh/felipefernandes/iara) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🚀 Funcionalidades

- **Agnóstica**: Configure o contexto do seu projeto (Tech Stack, Regras) via JSON.
- **Multi-Provedor**: Conecte diretamente ao OpenRouter, OpenAI, Google Gemini ou Anthropic Claude.
- **Fallback Inteligente**: Tenta modelos gratuitos automaticamente se o preferido falhar (apenas OpenRouter).
- **Rules-Based (Estático)**: Identifica padrões perigosos instantaneamente sem gastar tokens (ex: `GetComponent` em loops no Unity).
- **LLM-Based (Inteligente)**: Usa IA para entender a lógica, segurança e contexto, indo além da sintaxe.
- **GitHub + GitLab**: Integração nativa com ambas as plataformas, com comentários automáticos em PRs/MRs.
- **Reviews Multi-Idioma**: Configure o idioma de saída — reviews podem ser escritas em Português, Inglês, Espanhol, Francês e mais.

## 🧠 Capacidades

A Iara combina diferentes tipos de análise para uma revisão completa:

| Tipo | O que faz? | A Iara cobre? | Como? |
| :--- | :--- | :--- | :--- |
| **Análise Estática** | Caça bugs lendo o código (rápido). | ✅ **Sim** | Via Extensões (Regex) e LLM. |
| **Linting** | Corrige estilo e formatação. | ✅ **Sim** | LLM pode sugerir *Clean Code*. |
| **SAST** | Caça falhas de segurança no código. | ✅ **Sim** | Foco primário na busca por vulnerabilidades. |
| **Análise Dinâmica** | Caça bugs rodando o app (lento). | ❌ Não | Foco em CI/CD rápido (Code Review). |

### O que ela detecta?

1. **Unity / Game Dev**:
   - Uso de APIs lentas (`Find`, `GetComponent`) em loops críticos (`Update`).
   - Alocação excessiva de memória (Garbage Collection).
   - Excesso de logs (`Debug.Log`) em builds finais.

2. **Segurança (Geral)**:
   - Credenciais hardcoded (Senhas, API Keys).
   - Vulnerabilidades de Injeção (SQL, Command).
   - Falta de validação de inputs.

3. **Qualidade de Código**:
   - Lógica complexa ou confusa.
   - Erros de tratamento de exceções.
   - Sugestões de refatoração para legibilidade.

---

## 📦 Instalação e Setup

### 1. Instalar

```bash
pip install iara-reviewer
```

### 2. Configurar (Setup Interativo)

```bash
iara init
```

O wizard vai guiar você em **5 passos**:

1. **Idioma** — Escolha o idioma das reviews (en, pt-br, es, fr, etc.)
2. **Provedor** — Escolha seu provedor de LLM: `openrouter` (padrão, gratuito), `openai`, `gemini` ou `anthropic`
3. **API Key** — Informe a chave do provedor escolhido (validada e salva em `~/.iara/config.json`)
4. **Projeto** — Nome, tech stack, descrição
5. **Preferências** — Áreas de foco (Security, Performance, etc.)

Pronto! O config do projeto fica salvo em `.iara.json`.

### 3. Usar

```bash
git diff main | iara
```

### Verificar autenticação

```bash
iara auth status
```

### Setup manual (sem wizard)

Configure o provedor e sua chave via variáveis de ambiente:

```bash
# OpenRouter (padrão — modelos gratuitos disponíveis)
export OPENROUTER_API_KEY="sk-or-..."

# OpenAI
export IARA_PROVIDER="openai"
export OPENAI_API_KEY="sk-..."

# Google Gemini
export IARA_PROVIDER="gemini"
export GEMINI_API_KEY="AIza..."

# Anthropic Claude
export IARA_PROVIDER="anthropic"
export ANTHROPIC_API_KEY="sk-ant-..."
```

A prioridade de resolução da API key é: variável de ambiente > config global (`~/.iara/config.json`).

### Via clone (Desenvolvimento)

```bash
git clone https://github.com/felipefernandes/iara.git
cd iara
pip install -e .
```

---

## ⚙️ Configuração do Projeto

O `iara init` cria automaticamente o `.iara.json`. Você também pode criá-lo manualmente:

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
    "fallback_enabled": true,
    "provider": "openrouter"
  },
  "language": "pt-br"
}
```

### Provedores suportados e modelos de exemplo

| Provedor | valor de `provider` | Modelos de exemplo |
| :--- | :--- | :--- |
| OpenRouter (padrão) | `openrouter` | `google/gemini-2.0-flash-exp:free`, `meta-llama/llama-3.2-3b-instruct:free` |
| OpenAI | `openai` | `gpt-4o`, `gpt-4.5-preview`, `o1` |
| Google Gemini | `gemini` | `gemini-2.5-flash`, `gemini-2.5-pro` |
| Anthropic Claude | `anthropic` | `claude-opus-4-5-20250929`, `claude-sonnet-4-5-20250929` |

> **Nota**: O fallback inteligente para modelos gratuitos está disponível apenas para o OpenRouter. Ao usar `openai`, `gemini` ou `anthropic`, configure `"fallback_enabled": false`.

O campo `language` controla o idioma das reviews. Valores suportados: `en`, `pt-br`, `es`, `fr`, `de`, `ja`, `zh`, `ko`, `ru`, ou qualquer idioma que o LLM entenda.

Você também pode sobrescrever provedor, modelo e idioma via variáveis de ambiente:

```bash
export IARA_PROVIDER="anthropic"
export IARA_MODEL="claude-sonnet-4-5-20250929"
export IARA_LANGUAGE="pt-br"
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

### Forçando Provedor e Modelo

```bash
# Anthropic Claude
export IARA_PROVIDER="anthropic"
export ANTHROPIC_API_KEY="sk-ant-..."
export IARA_MODEL="claude-sonnet-4-5-20250929"
git diff | iara

# OpenAI GPT-4o
export IARA_PROVIDER="openai"
export OPENAI_API_KEY="sk-..."
export IARA_MODEL="gpt-4o"
git diff | iara

# Google Gemini
export IARA_PROVIDER="gemini"
export GEMINI_API_KEY="AIza..."
export IARA_MODEL="gemini-2.5-flash"
git diff | iara
```

---

## 🐙 Integração GitHub

Adicione a Iara ao seu repositório GitHub em **2 passos**:

### 1. Configurar o secret

Vá em **Settings > Secrets and variables > Actions > New repository secret** e adicione a chave do seu provedor:

| Provedor | Nome do secret |
| :--- | :--- |
| OpenRouter | `OPENROUTER_API_KEY` |
| OpenAI | `OPENAI_API_KEY` |
| Google Gemini | `GEMINI_API_KEY` |
| Anthropic | `ANTHROPIC_API_KEY` |

### 2. Criar o workflow

Crie o arquivo `.github/workflows/iara-review.yml`.

**Com OpenRouter (padrão, modelos gratuitos):**

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
        uses: felipefernandes/iara@main
        with:
          openrouter_api_key: ${{ secrets.OPENROUTER_API_KEY }}
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

**Com Anthropic Claude:**

```yaml
      - name: Run Iara Code Review
        uses: felipefernandes/iara@main
        with:
          provider: anthropic
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          model: "claude-sonnet-4-5-20250929"
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

**Com OpenAI:**

```yaml
      - name: Run Iara Code Review
        uses: felipefernandes/iara@main
        with:
          provider: openai
          openai_api_key: ${{ secrets.OPENAI_API_KEY }}
          model: "gpt-4o"
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

**Com Google Gemini:**

```yaml
      - name: Run Iara Code Review
        uses: felipefernandes/iara@main
        with:
          provider: gemini
          gemini_api_key: ${{ secrets.GEMINI_API_KEY }}
          model: "gemini-2.5-flash"
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

A Iara vai automaticamente:

- Revisar o diff do Pull Request
- Postar um comentário com o resultado da review

### Todos os inputs disponíveis

```yaml
- uses: felipefernandes/iara@main
  with:
    provider: "openrouter"                         # openrouter (padrão), openai, gemini, anthropic
    openrouter_api_key: ${{ secrets.OPENROUTER_API_KEY }}  # quando provider=openrouter
    openai_api_key: ${{ secrets.OPENAI_API_KEY }}          # quando provider=openai
    gemini_api_key: ${{ secrets.GEMINI_API_KEY }}          # quando provider=gemini
    anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}    # quando provider=anthropic
    model: "google/gemini-2.0-flash-exp:free"     # forçar modelo
    config_path: ".iara.json"                     # caminho do config (padrão: .iara.json)
    post_comment: "true"                           # postar comentário no PR (padrão: true)
    language: "pt-br"                              # idioma da review
```

---

## 🦊 Integração GitLab

### 1. Configurar variáveis

Vá em **Settings > CI/CD > Variables** e adicione:

- A chave do seu provedor (ex: `OPENROUTER_API_KEY`, `ANTHROPIC_API_KEY`, etc.)
- `IARA_PROVIDER`: nome do provedor (ex: `anthropic`) — omita para usar OpenRouter por padrão
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

# OpenRouter (padrão)
export OPENROUTER_API_KEY="sk-or-..."
git diff main...HEAD | iara

# Anthropic Claude
export IARA_PROVIDER="anthropic"
export ANTHROPIC_API_KEY="sk-ant-..."
export IARA_MODEL="claude-sonnet-4-5-20250929"
git diff main...HEAD | iara
```

---

## 🧪 Testes

```bash
python -m unittest discover tests
```

## 📜 Licença

MIT
