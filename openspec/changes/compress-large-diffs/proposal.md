# Proposal

## Problem
Currently, Iara truncates large pull request diffs aggressively at 15,000 characters. This causes major issues for large Pull Requests, as the LLM receives incomplete functions and misses entire files at the end of the diff, compromising the quality and breadth of the review. Furthermore, lots of context lines (unmodified code) waste precious tokens without adding value for the changes being evaluated.

## Proposed Solution
Implement an intelligent local `DiffCompressor` module inspired by Th0th's code structure technique. This module will:
- Compress diffs strictly locally (no LLM, no network, no added cost).
- Strip down the diff and prioritize file headers (`diff --git`, `@@`), added lines (`+`), and removed lines (`-`).
- Discard context lines if the diff exceeds a configurable `review.max_diff_tokens` limit (default 12000).
- Ensure all files in a PR are at least structurally represented rather than dropping trailing files from the prompt entirely.
- Run automatically before sending the diff to the LLM.

## Impact
- Small PRs remain untouched and fully contextual.
- Large and very large PRs now receive complete, structural reviews of all files instead of partial or truncated ones.
- Reduces token usage by omitting unmodified context lines.
