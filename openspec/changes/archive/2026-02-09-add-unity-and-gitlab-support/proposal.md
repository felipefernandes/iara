# Change: Add Unity Support and GitLab CI Integration

## Why
Phase 2 of the roadmap requires Iara to support Unity C# development (scanning, analysis, suggestions) and integration into GitLab CE CI pipelines. This expands Iara's utility beyond generic Python projects and into the Game Development domain, as well as enterprise on-premise deployments.

## What Changes
- **Unity Extension**: Implement a mechanism to load project-specific extensions. Create `extensions/unity.py` to analyze `.cs` files for common Unity pitfalls (e.g., `GetComponent` in `Update`, heavy operations, memory leaks).
- **Scanning Mode**: Add a `--scan <path>` argument to `ai-codereview.py` to allow reviewing specific files/directories without a diff (useful for static analysis or "varrer" existing code).
- **GitLab CI**: Create a `.gitlab-ci.yml` template and instructions for running Iara in GitLab CI/CD.

## Impact
- **Affected Specs**: `unity-reviewer` (New), `ci-integration` (New).
- **Affected Code**: `ai-codereview.py` (Add `argparse`, extension loader), `extensions/` (New directory).
- **Breaking Changes**: None expected, fully backward compatible. `git diff` usage remains default.
