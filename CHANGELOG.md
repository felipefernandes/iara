# Changelog

All notable changes to Iara Code Reviewer will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

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
