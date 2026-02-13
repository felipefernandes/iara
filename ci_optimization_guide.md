# CI/CD Optimization Strategy: Host Execution vs. Docker Action

This guide details the strategy used to fix the "No space left on device" error in the Iara CI pipeline. This approach is highly effective for Python-based tools involving large dependencies (like PyTorch, LLMs) on GitHub Actions.

## The Problem: Docker Actions Overhead

When you use a Docker-based GitHub Action (`uses: docker://...` or `uses: author/action@main` where `action.yml` uses `docker`):

1.  **Double Storage**: The runner pulls the Docker image (several GBs) *AND* often needs the source code checked out locally.
2.  **Slow Startup**: Pulling and extracting the image takes time.
3.  **Caching Difficulty**: caching `pip` packages inside a Docker container from a GitHub Action is complex and often fails to speed up builds.
4.  **Disk Limits**: GitHub free runners have ~14GB of usable space. A PyTorch image + Source + Build Artifacts can easily exceed this.

## The Solution: Host Execution (Script-Based)

Instead of running the tool inside a black-box container, we run it **directly on the Ubuntu Host runner**.

### Benefits
- **Zero Docker Overhead**: No image pull, no extra file system layers.
- **Native Caching**: `actions/setup-python` comes with built-in, one-line caching (`cache: 'pip'`).
- **Complete Control**: You can debug easier (`ls -la`, `echo $VAR`) because it's just a script running in the shell.

## Implementation Pattern

### 1. The Wrapper Script (`scripts/run_ci_tool.sh`)
Create a bash script that handles the logic usually hidden in `entrypoint.sh`.

```bash
#!/bin/bash
set -e

# 1. Validation
if [ -z "$GITHUB_TOKEN" ]; then
  echo "Error: GITHUB_TOKEN is missing."
  exit 1
fi

# 2. Logic (e.g., getting PR diff)
PR_NUMBER=$(jq -r '.pull_request.number' "$GITHUB_EVENT_PATH")
echo "Processing PR #$PR_NUMBER"

# 3. Execution (The Tool)
# Run the tool's module directly
python -m my_tool_module

# 4. Feedback (e.g., Posting Comment)
# Using GitHub CLI (pre-installed on runners) is often easier than plain curl
gh pr comment "$PR_NUMBER" --body "Review complete!"
```

### 2. The Optimized Workflow (`.github/workflows/tool.yml`)

```yaml
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      # Fast setup with caching
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip' # <--- MAGIC LINE: Instantly restores pip cache
          
      # Install dependencies directly
      - name: Install Tool
        run: pip install my-tool[heavy-deps]
        
      # Run the script
      - name: Run Analysis
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          chmod +x scripts/run_ci_tool.sh
          ./scripts/run_ci_tool.sh
```

## Recommendation for Iara Repository

To make this standard for everyone, Iara could offer a **Composite Action**.

### Convert Docker Action to Composite Action
In `action.yml`, change `runs: using: 'docker'` to `runs: using: 'composite'`.

**Advantages for Iara Users:**
- Users don't need to manually create the shell script; the Action handles it.
- Users still get the "Host Execution" benefits (speed, no docker overhead).

**Example `action.yml` (Composite):**
```yaml
name: 'Iara Code Review (Composite)'
description: 'Fast, non-docker version'
inputs:
  token:  {required: true}
runs:
  using: "composite"
  steps:
    - run: pip install iara-reviewer[rag]
      shell: bash
    - run: python -m iara_reviewer.cli
      shell: bash
```
