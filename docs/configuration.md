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

---

## Provider Configuration

### Supported Providers

| Provider | `provider` value | Example models |
| :--- | :--- | :--- |
| OpenRouter (default) | `openrouter` | `google/gemini-2.0-flash-exp:free`, `meta-llama/llama-3.2-3b-instruct:free` |
| OpenAI | `openai` | `gpt-4o`, `gpt-4.5-preview`, `o1` |
| Google Gemini | `gemini` | `gemini-2.5-flash`, `gemini-2.5-pro` |
| Anthropic Claude | `anthropic` | `claude-opus-4-5-20250929`, `claude-sonnet-4-5-20250929` |

> **Note**: Smart fallback to free models is only available for OpenRouter. When using `openai`, `gemini`, or `anthropic`, set `"fallback_enabled": false`.

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
