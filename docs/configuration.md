# Configuration Guide

Complete guide for configuring Iara Code Reviewer in your project.

## Table of Contents

- [Project Configuration](#project-configuration)
- [Configuration File Structure](#configuration-file-structure)
- [Indexer Settings](#indexer-settings)
  - [ignore_patterns](#ignore_patterns)
  - [max_index_file_size](#max_index_file_size)
- [Provider Configuration](#provider-configuration)
  - [Supported Providers](#supported-providers)
  - [Environment Variable Overrides](#environment-variable-overrides)
- [Memory and RAG](#memory-and-rag)
  - [Installation](#installation)
  - [Indexing Your Codebase](#indexing-your-codebase)
  - [Smart Chunking](#smart-chunking)
  - [Hybrid Search (Vector + Full-Text)](#hybrid-search-vector--full-text)
  - [Review with Context](#review-with-context)
  - [Managing Memory](#managing-memory)
- [Configuration Examples](#configuration-examples)

---

## Project Configuration

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

## Configuration File Structure

The `.iara.json` file contains:

- **`project`**: Project metadata and tech stack
- **`review`**: Review focus areas and indexer settings
- **`model`**: LLM provider and model preferences
- **`language`**: Review output language
- **`ci`** *(optional)*: CI/CD integration settings

### CI Block

```json
{
  "ci": {
    "review_mode": "inline",
    "platform": "gitlab"
  }
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `review_mode` | string | `"summary"` | `"summary"` = single MR/PR comment; `"inline"` = comments anchored to code lines |
| `platform` | string | auto-detected | Optional override: `"github"` or `"gitlab"`. Omit to let Iara detect from the CI environment (`GITHUB_ACTIONS` or `GITLAB_CI` env vars). The same `.iara.json` works on any platform without modification. |

---

## Indexer Settings

### ignore_patterns

You can configure the Iara Indexer's footprint to respect maximum file limits and skip specific artifacts from the RAG context memory.

**`ignore_patterns`:** Skips specific files or directories from being read (e.g., fixture folders or auto-generated payload files, which add zero value to code reviews).

**Important Notes on `ignore_patterns` behavior:**
- 🛠️ **Merged with Defaults:** Your defined patterns are **added** to a default list (which already includes `.git`, `node_modules`, `venv`, `__pycache__`, etc.). You do not need to rewrite these.
- ⚡ **Wildcards & Prefix Matching:** Iara uses Python's `fnmatch`, which means patterns like `test` match exact files or folders named `test`. To act as prefixes or match extensions, use wildcards (e.g., `test*` to match `test_dir`, or `*_generated.*` to match files ending with that).
- ⚠️ **Be Specific:** Broad patterns can inadvertently blind the Indexer. Using `*` or `*.py` as an ignore pattern will result in Iara ignoring your actual source code. It's safer to scope correctly (e.g., `tests/fixtures/*` or `logs/*.log`).

### max_index_file_size

**`max_index_file_size`:** Sets the byte threshold for a single file to be read (e.g. `10485760` for 10MB overrides the default 1MB restriction).

### false_positive_patterns

**`false_positive_patterns`:** Defines custom patterns to filter out known false positives from inline review comments before posting them to pull requests. This feature works only in **inline mode**.

Iara includes 4 built-in patterns that filter common false positives:
1. **CI/CD Secrets Syntax** - Filters comments about `${{ secrets.X }}` in GitHub Actions workflows
2. **Security Best Practices** - Filters complaints about `os.chmod()` with restrictive permissions
3. **Existing Error Handling** - Filters "missing error handling" when try-except blocks exist
4. **Small-Scale Performance** - Filters micro-optimizations for small datasets (< 10 items)

You can add your own custom patterns to extend filtering for project-specific conventions:

```json
{
  "review": {
    "false_positive_patterns": [
      {
        "name": "django-settings-globals",
        "file_pattern": "settings\\.py$",
        "message_pattern": "global.*variable",
        "reason": "Django settings.py uses globals by convention"
      }
    ]
  }
}
```

**Pattern Schema:**
- **`name`** (optional): Human-readable identifier for the pattern
- **`file_pattern`** (optional): Regex to match file paths (e.g., `"\.test\.js$"` for test files)
- **`message_pattern`** (required): Regex to match comment messages (e.g., `"hardcoded.*secret"`)
- **`context_safe`** (optional): Regex pattern - if found in code context, the comment is filtered
- **`reason`** (optional): Explanation for why this is filtered (shown in logs)

**Example Patterns:**

```json
{
  "review": {
    "false_positive_patterns": [
      {
        "name": "flask-app-config",
        "file_pattern": "app\\.py$",
        "message_pattern": "global.*config",
        "context_safe": "app\\.config",
        "reason": "Flask uses app.config as framework pattern"
      },
      {
        "name": "test-fixtures",
        "file_pattern": "test_.*\\.py$",
        "message_pattern": "hardcoded",
        "reason": "Test files use hardcoded fixtures by design"
      }
    ]
  }
}
```

**How It Works:**
1. After the LLM generates inline comments, Iara extracts code context from the diff
2. Each comment is checked against default + custom patterns
3. If a pattern matches (file + message + context conditions), the comment is filtered out
4. Filtering is logged for transparency (`INFO: Filtered 2 false positive(s)`)

**When to Use:**
- Your project has framework-specific conventions (Django, Flask, React, etc.)
- Certain files legitimately use patterns that look like anti-patterns (test files, config files)
- You want to reduce noise from recurring false positives that the LLM can't learn to avoid

**Note:** Custom patterns are merged with built-in patterns, so you don't need to redefine the defaults.

---

## Provider Configuration

### Supported Providers

| Provider | `provider` value | Example models |
| :--- | :--- | :--- |
| OpenRouter (default) | `openrouter` | `google/gemini-2.0-flash-exp:free`, `meta-llama/llama-3.2-3b-instruct:free` |
| OpenAI | `openai` | `gpt-4o`, `gpt-4.5-preview`, `o1` |
| Google Gemini | `gemini` | `gemini-2.5-flash`, `gemini-2.5-pro` |
| Anthropic Claude | `anthropic` | `claude-opus-4-5-20250929`, `claude-sonnet-4-5-20250929` |
| Groq | `groq` | `llama-3.3-70b-versatile`, `llama-3.1-70b-versatile`, `mixtral-8x7b-32768` |
| Ollama (local) | `ollama` | `qwen2.5-coder:7b`, `codellama:13b`, `llama3.1:8b` — any locally installed model |

> **Note**: Smart fallback to free models is only available for OpenRouter. When using `openai`, `gemini`, `anthropic`, or `groq`, set `"fallback_enabled": false`. Ollama requires no API key.

### Ollama — Local LLM Setup

[Ollama](https://ollama.com/) lets you run LLMs 100% locally — no API key, no data leaving your machine, no cost.

**Install Ollama:**

```bash
# Linux / macOS
curl -fsSL https://ollama.com/install.sh | sh

# Windows: download from https://ollama.com/download
```

**Pull a model:**

```bash
ollama pull qwen2.5-coder:7b      # Recommended: strong coder, ~5 GB
ollama pull codellama:13b          # Meta CodeLlama 13B, ~8 GB
ollama pull llama3.1:8b            # General purpose, ~5 GB
```

**Hardware requirements:**

| Model | VRAM / RAM | Quality | Speed |
| :--- | :--- | :--- | :--- |
| `qwen2.5-coder:7b` | 5–6 GB | Very Good | Fast |
| `codellama:13b` | 8–10 GB | Very Good | Medium |
| `llama3.1:8b` | 6–8 GB | Good | Fast |
| `deepseek-coder:6.7b` | 5–6 GB | Very Good | Fast |
| `codellama:34b` | 20+ GB | Excellent | Slow |

Works with CPU-only (slower) or GPU (NVIDIA/AMD/Apple Silicon).

**Configure Iara to use Ollama:**

```bash
# Option 1: interactive setup (recommended)
iara init
# → select "ollama" as provider (no API key needed)

# Option 2: environment variables
export IARA_PROVIDER="ollama"
export IARA_MODEL="qwen2.5-coder:7b"

# Option 3: .iara.json
```

```json
{
  "model": {
    "provider": "ollama",
    "preferred": "qwen2.5-coder:7b",
    "fallback_enabled": false
  }
}
```

**Custom Ollama endpoint** (e.g. remote server):

```bash
export OLLAMA_BASE_URL="http://my-server:11434"
```

**Troubleshooting:**

- `❌ Ollama is not running` → run `ollama serve` in a terminal
- `model not available` → run `ollama pull <model-name>` first
- Slow inference → normal for CPU-only; use GPU for better performance

The `language` field controls the review output language. Supported values: `en`, `pt-br`, `es`, `fr`, `de`, `ja`, `zh`, `ko`, `ru`, or any language the LLM understands.

### Environment Variable Overrides

You can also override provider, model, and language via environment variables:

```bash
export IARA_PROVIDER="anthropic"
export IARA_MODEL="claude-sonnet-4-5-20250929"
export IARA_LANGUAGE="pt-br"
```

---

## Memory and RAG

Iara supports a local **Retrieval-Augmented Generation (RAG)** system to provide context-aware reviews.

### Installation

Install RAG dependencies:

```bash
pip install iara-reviewer[rag]
# or
pip install lancedb sentence-transformers torch numpy
```

### Indexing Your Codebase

Run this command in your project root to create the local vector index:

```bash
iara memory index
```

This will parse your code (extracting functions, classes, and calls) and store it in `.iara/data/lancedb`.

### Smart Chunking

Iara uses **language-aware chunking** to ensure that code blocks fed into the LLM represent complete logical units (functions, classes, methods) instead of arbitrary 100-line blocks:

| Extension(s) | Strategy | What it extracts |
| :--- | :--- | :--- |
| `.py` | Python AST | Functions, async functions, classes |
| `.js`, `.ts` | Regex + brace balancing | Functions, async functions, classes, arrow functions |
| `.cs` | Regex + brace balancing | Classes, structs, interfaces, enums, methods |
| All others | Plain-text fallback | Blocks of up to 100 lines |

> **Why does this matter?** Chunks that cut a function in half generate noisy context for the LLM. Smart chunking keeps logical units intact, improving review accuracy and reducing token waste.

### Hybrid Search (Vector + Full-Text)

Iara's memory system uses **hybrid search** combining two complementary search modes:

| Search Mode | What it finds | Best for |
| :--- | :--- | :--- |
| **Vector Search** | Semantically similar code | Understanding context and logic |
| **Full-Text Search (FTS)** | Exact symbol/name matching | Finding specific functions or variables |

The system uses **Reciprocal Rank Fusion (RRF)** to intelligently merge both result sets:

- Results appearing in both searches get boosted rankings
- Symbol names match exactly (e.g., `calculate_risk_score()` finds `calculate_risk_score()`)
- Semantic understanding complements lexical precision
- Gracefully falls back to vector-only if FTS index unavailable

**Result**: Better context retrieval for more accurate code reviews.

### Review with Context

Just run the review command as usual. Iara will automatically use the memory to retrieve relevant context for the changed code.

```bash
git diff main | iara
```

### Managing Memory

To clear the index:

```bash
iara memory clear
```

---

## Configuration Examples

See complete configuration examples in the `examples/` directory:

- [`examples/iara-example.json`](../examples/iara-example.json) - Standard configuration
- [`examples/iara-example-inline.json`](../examples/iara-example-inline.json) - Inline PR comments mode

---

**Need help?** See the [main README](../README.md) or open an [issue](https://github.com/felipefernandes/iara/issues).
