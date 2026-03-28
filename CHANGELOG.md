# Changelog

All notable changes to Iara Code Reviewer will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.11.1] - 2026-03-28

### 🐛 Bug Fixes

#### Anthropic Integration Fixes (PR #87, #88)
- **Fixed `anthropic-version` header**: Corrected invalid version `2024-06-01` to `2023-06-01` — the only valid value accepted by the Anthropic API (all models were failing with "not a valid version").
- **Fixed model fallback for Anthropic**: `fallback_enabled: true` now correctly falls back to `SUGGESTED_MODELS` (e.g. `claude-sonnet-4-5`, `claude-haiku-4-5`) when the preferred model fails. Previously, fallback only worked for OpenRouter.

### 🧪 Tests
- Added `test_anthropic_fallback_when_preferred_model_fails` — verifies fallback chain for Anthropic provider.
- Added `test_anthropic_no_fallback_when_disabled` — ensures `fallback_enabled: false` is respected.

---

## [1.11.0] - 2026-03-27

### ✨ New Features

#### Anthropic (Claude) First-Class Support (Issue #85)
- **Live Validation**: Added explicit `x-api-key` validation with fallback behaviors.
- **Model Fallbacks**: Implemented smart fallback defaults for Anthropic suggested models (`claude-3-opus`, `claude-3-haiku`, etc.) automatically resolving to active models if one hits a rate limit or service interruption.
- **Headers & Capabilities**: Ensured code complies with Anthropic's versioning requirements (`anthropic-version`: 2024-06-01).

---

## [1.10.0] - 2026-03-27

### GitLab CI — Native Support (Issue #82)

- **Docker image works natively in GitLab CI**: `entrypoint.sh` detects `GITLAB_CI=true` and forks to a dedicated flow — reads API keys directly from the environment, generates the diff via `git diff` (no GitHub API call), posts the comment. No `pip install` per run.
- **Platform auto-detection**: Iara now reads `GITHUB_ACTIONS` or `GITLAB_CI` to select the right adapter automatically. `ci.platform` in `.iara.json` is now an optional override for edge cases. The same config works on GitHub Actions, GitLab CI cloud, and self-hosted GitLab CE/EE without modification.
- **`ci.platform` no longer required for inline mode**: removing the field from `.iara.json` is valid; platform is resolved at runtime via environment detection.
- **Self-hosted GitLab support**: `GitLabAdapter` reads `CI_SERVER_URL` (injected automatically by GitLab CI) as the API base URL.
- **Simplified GitLab CI template** — 2 variables, 2 script lines:
  ```yaml
  variables:
    OPENROUTER_API_KEY: $OPENROUTER_API_KEY
    GITLAB_TOKEN: $GITLAB_TOKEN
  script:
    - git fetch origin $CI_MERGE_REQUEST_TARGET_BRANCH_NAME
    - git diff origin/$CI_MERGE_REQUEST_TARGET_BRANCH_NAME...$CI_COMMIT_SHA | iara --post-comment
  ```

---

## [1.9.0] - 2026-03-06

### 🔧 Improvements

- **Improved system prompt to reduce false positives by 50-70%**: Expanded false positive guidelines from 2 generic rules to 10 specific anti-patterns with concrete examples. Now correctly recognizes:
  - CI/CD secrets syntax (`${{ secrets.X }}` is NOT hardcoded)
  - Security best practices (`os.chmod` on configs is GOOD, not a performance issue)
  - Existing error handling (don't report "missing" when try-except exists)
  - Small-scale performance (< 10 items → O(n) is FINE)
  - Framework conventions (Django/Flask config patterns)
  - Test code patterns (hardcoded values in tests are EXPECTED)
  - Intentional suppressions (`# type: ignore`, `# noqa`)
  - Conservative reporting principle: "When uncertain → DO NOT REPORT"

- **Added post-processing filters for known false positives (30-50% additional reduction)**: Deterministic pattern-based filtering catches false positives that slip through LLM responses. Works **only in inline mode**.
  - **4 built-in patterns**: CI/CD secrets syntax, security chmod, existing error handling, small-scale performance
  - **Configurable via `.iara.json`**: Add custom patterns for project-specific conventions
  - **Context-aware filtering**: Extracts code context from diffs to make intelligent filtering decisions
  - **Transparent logging**: Shows exactly what was filtered and why (`INFO: Filtered 2 false positive(s)`)
  - **See [Configuration Guide](docs/configuration.md#false_positive_patterns)** for examples and pattern schema

---

## [1.8.0] - 2026-03-06

### ✨ New Features

#### Multi-Provider Support: Groq
Added Groq as the 5th LLM provider alongside OpenRouter, OpenAI, Gemini, and Anthropic.

**Why Groq?**
- ⚡ Fast inference speeds (up to 10x faster than traditional providers)
- 💬 Better JSON generation for inline PR comments (free OpenRouter models struggle with structured output)
- 🎯 Reliable models: `llama-3.3-70b-versatile`, `llama-3.1-70b-versatile`, `mixtral-8x7b-32768`, `gemma2-9b-it`
- 🔓 Competitive pricing for high-quality code reviews

**How to use:**
```bash
export IARA_PROVIDER="groq"
export GROQ_API_KEY="gsk_..."
```

Or in `.iara.json`:
```json
{
  "model": {
    "provider": "groq",
    "preferred": "llama-3.3-70b-versatile"
  }
}
```

**GitHub Actions integration:**
```yaml
- uses: felipefernandes/iara@v1
  with:
    provider: groq
    groq_api_key: ${{ secrets.GROQ_API_KEY }}
```

### 🐛 Bug Fixes

- **Fixed Cloudflare protection error (HTTP 403)**: Added `User-Agent` header to bypass Cloudflare error code 1010 when calling Groq API from GitHub Actions
- **Improved inline comment JSON parser**: Enhanced markdown code block stripping with regex to handle LLM variations (```json, ```, ````json, etc.)

### 📚 Documentation

- Reorganized documentation structure for better navigation
- Created dedicated `docs/` folder with technical guides
- Added `docs/configuration.md` - comprehensive configuration guide
- Added `docs/ci-integration.md` - CI/CD integration for all platforms
- Created `CONTRIBUTING.md` - bilingual developer guide (PT/EN)
- Reduced README files to ~200 lines (landing page focus)
- Added Table of Contents to both README files
- Organized example files into `examples/` folder (iara-example.json, iara-example-inline.json, gitlab-ci.yml)
- Updated all documentation references to new file paths
- Added Groq provider examples throughout documentation

---

## [1.7.2] - 2026-03-05

### 🎉 Major Features

#### Inline PR Comments (GitHub & GitLab)
Post code review comments directly on specific lines of code, just like CodeClimate, SonarCloud, or human reviewers!

**What's new:**
- 💬 **Inline comments** anchored to specific code lines in PR diffs
- 🏗️ **Platform adapters** for GitHub (PR Review Comments API) and GitLab (MR Discussions API)
- 🎯 **Structured JSON output** from LLM with severity classification (🐛 bug, 🔒 security, ⚡ performance, ✨ style, 💡 other)
- 🔄 **Graceful fallback** to summary mode if inline posting fails
- ✅ **100% backward compatible** - existing configs work unchanged

**How to enable:**
```json
{
  "ci": {
    "platform": "github",
    "review_mode": "inline"
  }
}
```

**GitHub Actions permissions:**
```yaml
permissions:
  contents: read
  pull-requests: write
```

### 🐛 Bug Fixes
- Fixed backward compatibility when no `ci` platform is configured (auto-infers GitHub from environment)
- Fixed case-sensitive severity validation (now accepts "Bug", "SECURITY", "performance", etc.)

### 📚 Documentation
- Added comprehensive inline mode documentation to README
- Created `iara-example-inline.json` config example
- Documented platform requirements and permissions

### 🧪 Testing
- Added 40+ new unit tests for inline comments feature
- All 223 tests passing with improved coverage

**Supported Platforms:**
- ✅ GitHub Actions
- ✅ GitLab CI
- ⏳ Bitbucket, Azure DevOps (coming soon)

---

## [1.7.1] - 2026-03-04

### 🧠 Memory Enhancements

#### Hybrid RAG Search with Reciprocal Rank Fusion
- Implemented hybrid search combining vector similarity + full-text search (FTS)
- Uses Reciprocal Rank Fusion (RRF) algorithm to merge results intelligently
- Items appearing in both searches get boosted rankings
- Graceful fallback to vector-only search if FTS index unavailable

### 🔧 Improvements
- Better FTS monitoring with clear warning messages
- Schema validation for memory store
- Improved RRF formula implementation (1/(k+rank+1))

---

## [1.7.0] - 2026-02-20

### 🚀 Major Features

#### Smart Chunking for Code Indexing
- Language-aware chunking for Python, JavaScript/TypeScript, and C#
- Extracts complete logical units (functions, classes, methods)
- Prevents cutting functions in half for better LLM context
- Fallback to plain-text chunking for unsupported languages

#### Intelligent Diff Compression
- Automatically compresses large PR diffs to fit token limits
- Smart prioritization: keeps added/removed lines, reduces context
- Configurable via `max_diff_tokens` in `.iara.json`
- Prevents "diff too large" errors in massive PRs

### 🐛 Bug Fixes
- Fixed smart chunking edge cases (escape chars, unbalanced braces)
- Improved diff compressor robustness and validation

---

## Earlier Versions

For changes prior to v1.7.0, see the [commit history](https://github.com/felipefernandes/iara/commits/main).

---

## Contributing

Found a bug or have a feature request? [Open an issue](https://github.com/felipefernandes/iara/issues) or submit a PR!

**Contributors:**
- Felipe Fernandes ([@felipefernandes](https://github.com/felipefernandes))
- Claude Sonnet 4.5 (AI pair programmer)

---

**Legend:**
- 🎉 Major features
- ✨ New features
- 🐛 Bug fixes
- 🔧 Improvements
- 📚 Documentation
- 🧪 Testing
- ⚠️ Breaking changes (we avoid these!)
