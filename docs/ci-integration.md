# CI/CD Integration Guide

Complete guide for integrating Iara Code Reviewer into your CI/CD pipeline.

## Table of Contents

- [Inline PR Comments](#inline-pr-comments)
  - [Supported Platforms](#supported-platforms)
  - [How to Enable](#how-to-enable)
  - [Required Permissions](#required-permissions)
  - [Behavior Notes](#behavior-notes)
- [GitHub Integration](#github-integration)
  - [Configure the Secret](#1-configure-the-secret)
  - [Create the Workflow](#2-create-the-workflow)
  - [All Available Inputs](#all-available-inputs)
- [GitLab Integration](#gitlab-integration)
  - [Configure Variables](#1-configure-variables)
  - [Add to .gitlab-ci.yml](#2-add-to-gitlab-ciyml)
- [Docker Image](#docker-image)
  - [Why Use the Docker Image](#why-use-the-docker-image)
  - [Usage in GitHub Actions](#usage-in-github-actions)
  - [Usage in GitLab CI](#usage-in-gitlab-ci)
  - [Usage in Jenkins CircleCI](#usage-in-jenkins-circleci-or-any-docker-enabled-ci)
  - [Local Testing](#local-testing)
- [Other CI Platforms](#other-ci-platforms)
- [Example Templates](#example-templates)

---

## Inline PR Comments

By default, Iara posts a single summary comment on your Pull Request. For a better developer experience, you can enable **inline comments** that are anchored directly to specific lines of code, similar to how CodeClimate, SonarCloud, or human reviewers comment.

### Supported Platforms

- ✅ **GitHub** — Uses [Pull Request Review Comments API](https://docs.github.com/en/rest/pulls/comments)
- ✅ **GitLab** — Uses [Merge Request Discussions API](https://docs.gitlab.com/ee/api/discussions.html)

### How to Enable

Add a `ci` section to your `.iara.json` file:

```json
{
  "ci": {
    "review_mode": "inline"
  },
  "project": {
    "name": "My Project",
    "...": "..."
  }
}
```

The platform is **auto-detected** from the CI environment (`GITHUB_ACTIONS` or `GITLAB_CI` env vars). No hardcoding required — the same `.iara.json` works on GitHub Actions and GitLab CI without modification.

**Configuration Options:**

- **`platform`** *(optional override)*: Force a specific platform adapter
  - `"github"` — GitHub Actions
  - `"gitlab"` — GitLab CI (cloud or self-hosted)
  - Omit this field to let Iara auto-detect from the environment

- **`review_mode`**: How Iara posts review feedback
  - `"summary"` — Single comment with all feedback (default)
  - `"inline"` — Individual comments anchored to specific lines

### Required Permissions

#### GitHub Actions

Your workflow needs `pull-requests: write` permission:

```yaml
permissions:
  contents: read
  pull-requests: write
```

#### GitLab CI

The CI job token (`CI_JOB_TOKEN`) needs `api` scope, or use a personal access token with `api` permissions:

```yaml
variables:
  GITLAB_TOKEN: ${CI_JOB_TOKEN}  # or use a PAT
```

### Behavior Notes

- **Platform is auto-detected** — Iara reads `GITHUB_ACTIONS` or `GITLAB_CI` env vars at runtime; `ci.platform` in `.iara.json` is an optional override for edge cases
- **Graceful fallback** — If inline comment posting fails (e.g., JSON parsing error, API failure), Iara automatically falls back to summary mode
- **Platform compatibility** — If the platform cannot be determined, `post_comment` exits with an error and a clear message

---

## GitHub Integration

Iara is available on the [**GitHub Marketplace**](https://github.com/marketplace/actions/iara-code-reviewer) — you can add it to your repository with just a few clicks. Iara runs as a Docker-based action for fast execution.

Add Iara to your GitHub repository in **2 steps**:

### 1. Configure the Secret

Go to **Settings > Secrets and variables > Actions > New repository secret** and add the key for your chosen provider:

| Provider | Secret name |
| :--- | :--- |
| OpenRouter | `OPENROUTER_API_KEY` |
| OpenAI | `OPENAI_API_KEY` |
| Google Gemini | `GEMINI_API_KEY` |
| Anthropic | `ANTHROPIC_API_KEY` |

### 2. Create the Workflow

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

### All Available Inputs

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

## GitLab Integration

### 1. Configure Variables

Go to **Settings > CI/CD > Variables** and add:

- The key for your provider (e.g., `OPENROUTER_API_KEY`, `ANTHROPIC_API_KEY`, etc.)
- `IARA_PROVIDER`: the provider name (e.g., `anthropic`) — omit for OpenRouter default
- `GITLAB_TOKEN`: Personal/Project Access Token with `api` scope (required for MR comments)

### 2. Add to `.gitlab-ci.yml`

**Using the pre-built Docker image (recommended — no install overhead):**

```yaml
stages:
  - review

iara_code_review:
  stage: review
  image: ghcr.io/felipefernandes/iara:latest
  variables:
    OPENROUTER_API_KEY: $OPENROUTER_API_KEY
    GITLAB_TOKEN: $GITLAB_TOKEN
  script:
    - git fetch origin $CI_MERGE_REQUEST_TARGET_BRANCH_NAME
    - git diff origin/$CI_MERGE_REQUEST_TARGET_BRANCH_NAME...$CI_COMMIT_SHA | iara --post-comment
  allow_failure: true
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
```

The platform (`gitlab`) and all CI variables (`CI_PROJECT_PATH`, `CI_MERGE_REQUEST_IID`, `CI_COMMIT_SHA`) are detected automatically — no aliases or boilerplate required.

> **Self-hosted GitLab CE/EE**: the API base URL is read from `CI_SERVER_URL`, which GitLab CI always injects. No extra configuration needed.

**Alternative: Using pip install (slower, ~1-2 min extra per run):**

```yaml
iara_code_review:
  stage: review
  image: python:3.11-slim
  script:
    - pip install iara-reviewer -q
    - git fetch origin $CI_MERGE_REQUEST_TARGET_BRANCH_NAME
    - git diff origin/$CI_MERGE_REQUEST_TARGET_BRANCH_NAME...$CI_COMMIT_SHA | iara --post-comment
  allow_failure: true
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
```

Iara will automatically:

- Detect the GitLab CI environment
- Review the Merge Request diff
- Post a comment with the review result on the MR

---

## Docker Image

Iara is available as a pre-built Docker image on **GitHub Container Registry (GHCR)**, which significantly speeds up CI/CD execution by eliminating dependency installation time.

**Image:** `ghcr.io/felipefernandes/iara:latest`

### Why Use the Docker Image

- ⚡ **Faster startup**: Skip `pip install` overhead — image pulls in seconds
- 📦 **All dependencies included**: Python 3.11, RAG dependencies, git, curl, jq
- 🔄 **Portable**: Works across GitHub Actions, GitLab CI, Jenkins, Bitbucket Pipelines, and more
- 🔒 **Consistent environment**: Same runtime environment on every platform

### Usage in GitHub Actions

The GitHub Action (`felipefernandes/iara@main`) **already uses this Docker image** automatically. No additional configuration needed!

If you want to use the Docker image directly:

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
    container:
      image: ghcr.io/felipefernandes/iara:latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Run Iara Review
        run: |
          export PR_DIFF=$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
            -H "Accept: application/vnd.github.v3.diff" \
            "https://api.github.com/repos/$GITHUB_REPOSITORY/pulls/${{ github.event.pull_request.number }}")
          iara --post-comment
        env:
          OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          REPO: ${{ github.repository }}
          PR_NUMBER: ${{ github.event.pull_request.number }}
```

### Usage in GitLab CI

```yaml
iara_code_review:
  stage: review
  image: ghcr.io/felipefernandes/iara:latest
  variables:
    OPENROUTER_API_KEY: $OPENROUTER_API_KEY
    GITLAB_TOKEN: $GITLAB_TOKEN
  script:
    - git fetch origin $CI_MERGE_REQUEST_TARGET_BRANCH_NAME
    - git diff origin/$CI_MERGE_REQUEST_TARGET_BRANCH_NAME...$CI_COMMIT_SHA | iara --post-comment
  allow_failure: true
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
```

### Usage in Jenkins, CircleCI, or Any Docker-enabled CI

```bash
docker run --rm \
  -e OPENROUTER_API_KEY="sk-or-..." \
  -e PR_DIFF="$(git diff main...HEAD)" \
  ghcr.io/felipefernandes/iara:latest
```

### Local Testing

You can test the Docker image locally before deploying to CI:

```bash
# Pull the image
docker pull ghcr.io/felipefernandes/iara:latest

# Run a review
docker run --rm \
  -e OPENROUTER_API_KEY="sk-or-..." \
  -e PR_DIFF="$(git diff main)" \
  ghcr.io/felipefernandes/iara:latest
```

---

## Other CI Platforms

For Jenkins, CircleCI, or any other CI platform:

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

## Example Templates

Complete working templates are available:

- [`examples/github-workflow.yml`](../examples/github-workflow.yml) - GitHub Actions workflow
- [`examples/gitlab-ci.yml`](../examples/gitlab-ci.yml) - GitLab CI pipeline

---

**Need help?** See the [main README](../README.md) or [Configuration Guide](configuration.md), or open an [issue](https://github.com/felipefernandes/iara/issues).
