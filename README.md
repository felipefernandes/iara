# Iara - AI Code Reviewer 🧜‍♀️

🇧🇷 [Leia em Português](README.pt-br.md)

Iara is an automated, project-agnostic, configurable code review tool designed to run in CI/CD pipelines or locally via CLI. It uses the OpenRouter API to access multiple LLM models (Llama 3, Gemini 2.0, etc.) for free or on paid plans.

## 🚀 Features

- **Agnostic**: Configure your project context (Tech Stack, Rules) via JSON.
- **Multi-Model**: Support for multiple providers via OpenRouter.
- **Smart Fallback**: Automatically tries free models if the preferred one fails.
- **Rules-Based (Static)**: Identifies dangerous patterns instantly without spending tokens (e.g., `GetComponent` in loops in Unity).
- **LLM-Based (Intelligent)**: Uses AI to understand logic, security, and context, going beyond syntax.
- **GitHub + GitLab**: Native integration with both platforms, with automatic comments on PRs/MRs.
- **Multi-Language Reviews**: Configure the output language — reviews can be written in English, Portuguese, Spanish, French, and more.

## 🧠 Capabilities

Iara combines different types of analysis for a complete review:

| Type | What does it do? | Does Iara cover it? | How? |
| :--- | :--- | :--- | :--- |
| **Static Analysis** | Finds bugs by reading code (fast). | ✅ **Yes** | Via Extensions (Regex) and LLM. |
| **Linting** | Fixes style and formatting. | ✅ **Yes** | LLM can suggest *Clean Code*. |
| **SAST** | Finds security flaws in code. | ✅ **Yes** | Primary focus on vulnerability detection. |
| **Dynamic Analysis** | Finds bugs by running the app (slow). | ❌ No | Focus on fast CI/CD (Code Review). |

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

The wizard will guide you through 4 steps:

- **API Key** — Asks for your OpenRouter key (free at [openrouter.ai/keys](https://openrouter.ai/keys)), validates and saves it
- **Language** — Choose the review output language (en, pt-br, es, fr, etc.)
- **Project** — Name, tech stack, description
- **Preferences** — Focus areas (Security, Performance, etc.)

Done! The API key is saved at `~/.iara/config.json` and project config at `.iara.json`.

### 3. Use

```bash
git diff main | iara
```

### Check authentication

```bash
iara auth status
```

### Alternative setup (without wizard)

If you prefer to configure manually:

```bash
# Linux/Mac
export OPENROUTER_API_KEY="sk-or-..."

# Windows (PowerShell)
$env:OPENROUTER_API_KEY="sk-or-..."
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
    "ignore_patterns": []
  },
  "model": {
    "preferred": "google/gemini-2.0-flash-exp:free",
    "fallback_enabled": true
  },
  "language": "en"
}
```

The `language` field controls the review output language. Supported values: `en`, `pt-br`, `es`, `fr`, `de`, `ja`, `zh`, `ko`, `ru`, or any language the LLM understands.

You can also override via environment variable:

```bash
export IARA_LANGUAGE="pt-br"
```

A ready-to-use example is available at `iara-example.json`.

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

### Forcing a Model

```bash
export IARA_MODEL="meta-llama/llama-3.2-3b-instruct:free"
git diff | iara
```

---

## 🐙 GitHub Integration

Add Iara to your GitHub repository in **2 steps**:

### 1. Configure the secret

Go to **Settings > Secrets and variables > Actions > New repository secret** and add:

- Name: `OPENROUTER_API_KEY`
- Value: your OpenRouter API key

### 2. Create the workflow

Create the file `.github/workflows/iara-review.yml`:

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

Iara will automatically:

- Review the Pull Request diff
- Post a comment with the review result

### Additional options

```yaml
- uses: felipefernandes/iara@main
  with:
    openrouter_api_key: ${{ secrets.OPENROUTER_API_KEY }}
    model: 'google/gemini-2.0-flash-exp:free'   # Force model
    config_path: '.iara.json'                     # Config path
    post_comment: 'true'                          # Post comment (default: true)
    language: 'pt-br'                             # Review language
```

---

## 🦊 GitLab Integration

### 1. Configure variables

Go to **Settings > CI/CD > Variables** and add:

- `OPENROUTER_API_KEY`: OpenRouter API key
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
export OPENROUTER_API_KEY="sk-or-..."
git diff main...HEAD | iara
```

---

## 🧪 Tests

```bash
python -m unittest discover tests
```

## 📜 License

MIT
