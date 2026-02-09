# Design: Unity Support and GitLab CI

## Context
We need to support "Scanning" of Unity C# code and integration with GitLab CI.

## Decisions

### 1. Extension System
Instead of a complex plugin architecture, we will use a simple directory-based module loader.
- `extensions/`: Directory to hold extension scripts.
- `extensions/unity.py`: Will contain a `review(content, context)` function or similar.
- `ai-codereview.py`: Will import extensions based on `.iara.json` configuration (`extensions: ["unity"]`).

### 2. Scanning Mode (`--scan`)
Default behavior relies on `git diff`. Scanning implies looking at existing files.
- We will add `argparse` to support `python ai-codereview.py --scan ./Assets/Scripts`.
- In scan mode, Iara will iterate recursively, filtering by `.cs` (if Unity extension active) or generic patterns.
- **Challenge**: Context Window. Sending ALL files to LLM is impossible.
- **Solution**:
    - **Chunking**: Process files individually or in small batches?
    - **Local Analysis**: The "Unity Extension" should implement regex-based or AST-based *pre-analysis* to find suspicious patterns locally *before* asking LLM? Or just send the file content to LLM if it's small?
    - **Hybrid**: The `unity.py` extension will likely use Regex triggers to identify "hot spots" (e.g. `Update()` methods) and send those snippets to the LLM for review. This saves tokens and cost.

### 3. GitLab CI
- Standard `.gitlab-ci.yml` using a Python docker image.
- Steps:
    1. Checkout.
    2. Install dependencies (None/Minimal).
    3. Run `python ai-codereview.py`.

## Alternatives Considered
- **Roslyn Analyzer**: Writing a C# analyzer would be better for performance but requires a build step and isn't Python-based (Iara is Python). We stick to Python for portability on Raspberry Pi/CI.

## Risks
- **False Positives**: Regex-based scanning might flag commented code. We rely on LLM to filter these out ("Is this actually a bug?").
- **Cost**: Scanning 100 files with LLM is expensive. We MUST implement filters.
