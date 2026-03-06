# Iara - AI Code Reviewer 🧜‍♀️

![Iara - AI Code Review Agent](.assets/iara-github-banner.png)

🇧🇷 [Leia em Português](README.pt-br.md)

Iara is an automated, project-agnostic, configurable code review tool designed to run in CI/CD pipelines or locally via CLI. It connects directly to the LLM provider of your choice — OpenRouter (free models), OpenAI, Google Gemini, or Anthropic Claude.

---

[![🧜‍♀️ Iara Code Review](https://github.com/felipefernandes/iara/actions/workflows/iara-review.yml/badge.svg)](https://github.com/felipefernandes/iara/actions/workflows/iara-review.yml) [![🧪 Tests](https://github.com/felipefernandes/iara/actions/workflows/tests.yml/badge.svg)](https://github.com/felipefernandes/iara/actions/workflows/tests.yml) [![codecov](https://codecov.io/gh/felipefernandes/iara/branch/main/graph/badge.svg)](https://codecov.io/gh/felipefernandes/iara) [![PyPI - Version](https://img.shields.io/pypi/v/iara-reviewer)](https://pypi.org/project/iara-reviewer/) [![GitHub Marketplace](https://img.shields.io/badge/Marketplace-Iara%20Code%20Reviewer-blue?logo=github)](https://github.com/marketplace/actions/iara-code-reviewer) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Table of Contents

- [Features](#-features)
- [Capabilities](#-capabilities)
- [Installation and Setup](#-installation-and-setup)
- [How to Use](#-how-to-use)
- [Privacy & Security](#-privacy--security)
- [Documentation](#-documentation)
- [Tests](#-tests)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🚀 Features

- **Agnostic**: Configure your project context (Tech Stack, Rules) via JSON.
- **Multi-Provider**: Connect directly to OpenRouter, OpenAI, Google Gemini, Anthropic Claude, or Groq.
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
2. **Provider** — Choose your LLM provider: `openrouter` (default, free), `openai`, `gemini`, `anthropic`, or `groq`
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

## 🔒 Privacy & Security

**Important**: Iara sends your code to third-party LLM providers for analysis. While convenient, this has privacy implications you should be aware of.

### What happens to your code?
- Code diffs are sent to external APIs (OpenRouter, OpenAI, Gemini, Anthropic, Groq)
- Providers may temporarily store data for processing
- Data retention and training policies vary by provider

### Provider Privacy Comparison

| Provider | Training on API Data | Data Retention | Enterprise Options | Best For |
|----------|---------------------|----------------|-------------------|----------|
| **Anthropic** | ❌ No | Temporary | ✅ Yes | Sensitive code |
| **OpenAI** | ⚠️ Opt-out required | 30 days | ✅ Yes | General use |
| **Gemini** | ⚠️ Varies | Not documented | ✅ Yes | General use |
| **Groq** | ⚠️ Not documented | Not documented | ❌ No | Public code |
| **OpenRouter** | ⚠️ Depends on model | Varies | ❌ No | Public code |

### Recommendations by Use Case

- **Open Source Projects**: Any provider (code is already public)
- **Private Projects (non-sensitive)**: Anthropic or Groq
- **Sensitive/Proprietary Code**: Anthropic Enterprise or self-hosted LLM
- **Regulated Industries (HIPAA, PCI-DSS)**: Self-hosted LLM only (e.g., Ollama - see [Issue #76](https://github.com/felipefernandes/iara/issues/76))

For detailed privacy information and self-hosted options, see **[Privacy & Security Guide](docs/privacy-security.md)**.

---

## 📚 Documentation

For detailed guides and configuration options, see:

- **[Configuration Guide](docs/configuration.md)** - Project configuration, providers, models, RAG memory setup
- **[CI/CD Integration](docs/ci-integration.md)** - GitHub Actions, GitLab CI, Docker, inline PR comments
- **[Privacy & Security Guide](docs/privacy-security.md)** - Data privacy, provider policies, self-hosted options
- **[Contributing Guide](CONTRIBUTING.md)** - Development setup, testing, pull requests

### Configuration Examples

Complete configuration examples are available in [`examples/`](examples/):

- [`examples/iara-example.json`](examples/iara-example.json) - Standard configuration
- [`examples/iara-example-inline.json`](examples/iara-example-inline.json) - Inline PR comments mode
- [`examples/github-workflow.yml`](examples/github-workflow.yml) - GitHub Actions workflow
- [`examples/gitlab-ci.yml`](examples/gitlab-ci.yml) - GitLab CI pipeline

### Quick Links

- [GitHub Marketplace](https://github.com/marketplace/actions/iara-code-reviewer) - Add Iara to your repository
- [PyPI Package](https://pypi.org/project/iara-reviewer/) - Install via pip
- [Changelog](CHANGELOG.md) - Version history and release notes

---

## 🧪 Tests

```bash
python -m unittest discover tests
```

---

## 🤝 Contributing

We welcome contributions! See our [Contributing Guide](CONTRIBUTING.md) for:

- Development setup
- Running tests
- Code quality standards
- Pull request guidelines
- Release process

---

## 📜 License

MIT
