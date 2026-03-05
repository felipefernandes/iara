# Iara - AI Code Reviewer 🧜‍♀️

![Iara - AI Code Review Agent](.assets/iara-github-banner.png)

🇧🇷 [Leia em Português](README.pt-br.md)

Iara is an automated, project-agnostic, configurable code review tool designed to run in CI/CD pipelines or locally via CLI. It connects directly to the LLM provider of your choice — OpenRouter (free models), OpenAI, Google Gemini, or Anthropic Claude.

---

[![🧜‍♀️ Iara Code Review](https://github.com/felipefernandes/iara/actions/workflows/iara-review.yml/badge.svg)](https://github.com/felipefernandes/iara/actions/workflows/iara-review.yml) [![🧪 Tests](https://github.com/felipefernandes/iara/actions/workflows/tests.yml/badge.svg)](https://github.com/felipefernandes/iara/actions/workflows/tests.yml) [![codecov](https://codecov.io/gh/felipefernandes/iara/branch/main/graph/badge.svg)](https://codecov.io/gh/felipefernandes/iara) [![PyPI - Version](https://img.shields.io/pypi/v/iara-reviewer)](https://pypi.org/project/iara-reviewer/) [![GitHub Marketplace](https://img.shields.io/badge/Marketplace-Iara%20Code%20Reviewer-blue?logo=github)](https://github.com/marketplace/actions/iara-code-reviewer) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🚀 Features

- **Agnostic**: Configure your project context (Tech Stack, Rules) via JSON.
- **Multi-Provider**: Connect directly to OpenRouter, OpenAI, Google Gemini, or Anthropic Claude.
- **Smart Fallback**: Automatically tries free models if the preferred one fails (OpenRouter only).
- **Rules-Based (Static)**: Identifies dangerous patterns instantly without spending tokens (e.g., `GetComponent` in loops in Unity).
- **LLM-Based (Intelligent)**: Uses AI to understand logic, security, and context, going beyond syntax.
- **GitHub + GitLab**: Native integration with both platforms, with automatic comments on PRs/MRs.
- **Multi-Language Reviews**: Configure the output language — reviews can be written in English, Portuguese, Spanish, French, and more.

## 🧠 Capabilities

Iara combines different types of analysis for a complete review:

| Type                 | What does it do?                      | Does Iara cover it? | How?                                      |
| :------------------- | :------------------------------------ | :------------------ | :---------------------------------------- |
| **Static Analysis**  | Finds bugs by reading code (fast).    | ✅ **Yes**          | Via Extensions (Regex) and LLM.           |
| **Linting**          | Fixes style and formatting.           | ✅ **Yes**          | LLM can suggest _Clean Code_.             |
| **SAST**             | Finds security flaws in code.         | ✅ **Yes**          | Primary focus on vulnerability detection. |
| **Dynamic Analysis** | Finds bugs by running the app (slow). | ❌ No               | Focus on fast CI/CD (Code Review).        |

### What does it detect?

1. **Unity / Game Dev**:
   - Use of slow APIs (`Find`, `GetComponent`) in critical loops (`Update`).
   - Excessive memory allocation (Garbage Collection).
   - Excess logging (`Debug.Log`) in final builds.

2. **Security (General)**:
   - Hardcoded credentials (Passwords, API Keys).
   - Injection vulnerabilities (SQL, Command).
   - Missing input validation.

3. **Code Quality**:
   - Complex or confusing logic.
   - Exception handling errors.
   - Refactoring suggestions for readability.

---

## 📦 Installation and Setup

### 1. Install

```bash
pip install iara-reviewer
```

### 2. Configure (Interactive Setup)

```bash
iara init
```

The wizard guides you through **5 steps**:

1. **Language** — Choose the review output language (en, pt-br, es, fr, etc.)
2. **Provider** — Choose your LLM provider: `openrouter` (default, free), `openai`, `gemini`, or `anthropic`
3. **API Key** — Enter the key for the chosen provider (validated and saved to `~/.iara/config.json`)
4. **Project** — Name, tech stack, description
5. **Preferences** — Focus areas (Security, Performance, etc.)

Done! Project config is saved at `.iara.json`.

### 3. Use

```bash
git diff main | iara
```

### Check authentication

```bash
iara auth status
```

### Manual setup (without wizard)

Set the provider and its key via environment variables:

```bash
# OpenRouter (default — free models available)
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

API key resolution priority: environment variable > global config (`~/.iara/config.json`).

### From source (Development)

```bash
git clone https://github.com/felipefernandes/iara.git
cd iara
pip install -e .
```

---

## ⚙️ Project Configuration

`iara init` automatically creates `.iara.json`. You can also create it manually:

```json
{
  "project": {
    "name": "My Project",
    "description": "Project description.",
    "tech_stack": ["Python"]
  },
  "review": {
    "focus_areas": ["Performance", "Security"],
    "ignore_patterns": ["fixtures", "migrations", "generated"],
    "max_index_file_size": 10485760
  },
  "model": {
    "preferred": "google/gemini-2.0-flash-exp:free",
    "fallback_enabled": true,
    "provider": "openrouter"
  },
  "language": "en"
}
```

### `ignore_patterns` and `max_index_file_size`
You can configure the Iara Indexer's footprint to respect maximum file limits and skip specific artifacts from the RAG context memory.

**`max_index_file_size`:** Sets the byte threshold for a single file to be read (e.g. `10485760` for 10MB overrides the default 1MB restriction).
**`ignore_patterns`:** Skips specific files or directories from being read (e.g., fixture folders or auto-generated payload files, which add zero value to code reviews). 

**Important Notes on `ignore_patterns` behavior:**
- 🛠️ **Merged with Defaults:** Your defined patterns are **added** to a default list (which already includes `.git`, `node_modules`, `venv`, `__pycache__`, etc.). You do not need to rewrite these.
- ⚡ **Wildcards & Prefix Mathing:** Iara uses Python's `fnmatch`, which means patterns like `test` match exact files or folders named `test`. To act as prefixes or match extensions, use wildcards (e.g., `test*` to match `test_dir`, or `*_generated.*` to match files ending with that).
- ⚠️ **Be Specific:** Broad patterns can inadvertently blind the Indexer. Using `*` or `*.py` as an ignore pattern will result in Iara ignoring your actual source code. It's safer to scope correctly (e.g., `tests/fixtures/*` or `logs/*.log`).

### Supported providers and example models

| Provider | `provider` value | Example models |
| :--- | :--- | :--- |
| OpenRouter (default) | `openrouter` | `google/gemini-2.0-flash-exp:free`, `meta-llama/llama-3.2-3b-instruct:free` |
| OpenAI | `openai` | `gpt-4o`, `gpt-4.5-preview`, `o1` |
| Google Gemini | `gemini` | `gemini-2.5-flash`, `gemini-2.5-pro` |
| Anthropic Claude | `anthropic` | `claude-opus-4-5-20250929`, `claude-sonnet-4-5-20250929` |

> **Note**: Smart fallback to free models is only available for OpenRouter. When using `openai`, `gemini`, or `anthropic`, set `"fallback_enabled": false`.

The `language` field controls the review output language. Supported values: `en`, `pt-br`, `es`, `fr`, `de`, `ja`, `zh`, `ko`, `ru`, or any language the LLM understands.

You can also override provider, model, and language via environment variables:

```bash
export IARA_PROVIDER="anthropic"
export IARA_MODEL="claude-sonnet-4-5-20250929"
export IARA_LANGUAGE="pt-br"
```

A ready-to-use example is available at `iara-example.json`.

---


## 🧠 Memory (RAG) [New]

Iara now supports a local **Retrieval-Augmented Generation (RAG)** system to provide context-aware reviews.

### 1. Install Dependencies
```bash
pip install iara-reviewer[rag]
# or
pip install lancedb sentence-transformers torch numpy
```

### 2. Index Your Codebase
Run this command in your project root to create the local vector index:
```bash
iara memory index
```
This will parse your code (extracting functions, classes, and calls) and store it in `.iara/data/lancedb`.

#### Smart Chunking — Supported Languages

Iara uses **language-aware chunking** to ensure that code blocks fed into the LLM represent complete logical units (functions, classes, methods) instead of arbitrary 100-line blocks:

| Extension(s) | Strategy | What it extracts |
| :--- | :--- | :--- |
| `.py` | Python AST | Functions, async functions, classes |
| `.js`, `.ts` | Regex + brace balancing | Functions, async functions, classes, arrow functions |
| `.cs` | Regex + brace balancing | Classes, structs, interfaces, enums, methods |
| All others | Plain-text fallback | Blocks of up to 100 lines |

> **Why does this matter?** Chunks that cut a function in half generate noisy context for the LLM. Smart chunking keeps logical units intact, improving review accuracy and reducing token waste.

### 3. Review with Context
Just run the review command as usual. Iara will automatically use the memory to retrieve relevant context for the changed code.
```bash
git diff main | iara
```

### 4. Manage Memory
To clear the index:
```bash
iara memory clear
```

---

## 🏃 How to Use

### Via Pipe (Git Diff)

```bash
git diff main | iara
```

### Via Environment Variable

```bash
export PR_DIFF=$(git diff main)
iara
```

### Scan Mode (Static Analysis)

```bash
iara --scan ./path/to/project
```

### Forcing a Provider and Model

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

## 🐙 GitHub Integration

Iara is available on the [**GitHub Marketplace**](https://github.com/marketplace/actions/iara-code-reviewer) — you can add it to your repository with just a few clicks. No Docker required! Iara runs as a lightweight **Composite Action** directly on the runner, with automatic pip caching for fast execution.

Add Iara to your GitHub repository in **2 steps**:

### 1. Configure the secret

Go to **Settings > Secrets and variables > Actions > New repository secret** and add the key for your chosen provider:

| Provider | Secret name |
| :--- | :--- |
| OpenRouter | `OPENROUTER_API_KEY` |
| OpenAI | `OPENAI_API_KEY` |
| Google Gemini | `GEMINI_API_KEY` |
| Anthropic | `ANTHROPIC_API_KEY` |

### 2. Create the workflow

Create the file `.github/workflows/iara-review.yml`.

**With OpenRouter (default, free models):**

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

**With Anthropic Claude:**

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

**With OpenAI:**

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

**With Google Gemini:**

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

Iara will automatically:

- Review the Pull Request diff
- Post a comment with the review result

### All available inputs

```yaml
- uses: felipefernandes/iara@main
  with:
    provider: "openrouter"                         # openrouter (default), openai, gemini, anthropic
    openrouter_api_key: ${{ secrets.OPENROUTER_API_KEY }}  # when provider=openrouter
    openai_api_key: ${{ secrets.OPENAI_API_KEY }}          # when provider=openai
    gemini_api_key: ${{ secrets.GEMINI_API_KEY }}          # when provider=gemini
    anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}    # when provider=anthropic
    model: "google/gemini-2.0-flash-exp:free"     # override model
    config_path: ".iara.json"                     # config path (default: .iara.json)
    post_comment: "true"                           # post comment on PR (default: true)
    language: "en"                                 # review language
    index_codebase: "true"                         # enable RAG memory (default: false)
```

---

## 🦊 GitLab Integration

### 1. Configure variables

Go to **Settings > CI/CD > Variables** and add:

- The key for your provider (e.g., `OPENROUTER_API_KEY`, `ANTHROPIC_API_KEY`, etc.)
- `IARA_PROVIDER`: the provider name (e.g., `anthropic`) — omit for OpenRouter default
- `GITLAB_TOKEN`: Personal/Project Access Token with `api` scope (required for MR comments)

### 2. Add to `.gitlab-ci.yml`

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

Iara will automatically:

- Review the Merge Request diff
- Post a comment with the review result on the MR

A complete template is available at `gitlab-ci.yml`.

---

## 🔧 Any CI (Jenkins, CircleCI, etc.)

```bash
pip install iara-reviewer

# OpenRouter (default)
export OPENROUTER_API_KEY="sk-or-..."
git diff main...HEAD | iara

# Anthropic Claude
export IARA_PROVIDER="anthropic"
export ANTHROPIC_API_KEY="sk-ant-..."
export IARA_MODEL="claude-sonnet-4-5-20250929"
git diff main...HEAD | iara
```

---

## 🧪 Tests

```bash
python -m unittest discover tests
```

## 📜 License

MIT
