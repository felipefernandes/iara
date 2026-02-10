#!/bin/bash
set -e

# ============================================
# Iara Code Reviewer - GitHub Action Entrypoint
# ============================================

# --- Input Variables (from action.yml inputs) ---
OPENROUTER_API_KEY="${INPUT_OPENROUTER_API_KEY}"
IARA_MODEL="${INPUT_MODEL}"
IARA_LANGUAGE="${INPUT_LANGUAGE}"
CONFIG_PATH="${INPUT_CONFIG_PATH:-.iara.json}"
POST_COMMENT="${INPUT_POST_COMMENT:-true}"

# --- GitHub Context Variables ---
GITHUB_TOKEN="${GITHUB_TOKEN}"
REPO="${GITHUB_REPOSITORY}"

# --- Validate Required Inputs ---
if [ -z "$OPENROUTER_API_KEY" ]; then
  echo "::error::OPENROUTER_API_KEY is required. Add it as a repository secret."
  exit 1
fi

# --- Determine PR Number ---
PR_NUMBER=""
if [ -f "$GITHUB_EVENT_PATH" ]; then
  PR_NUMBER=$(jq -r '.pull_request.number // .number // empty' "$GITHUB_EVENT_PATH" 2>/dev/null || true)
fi

if [ -z "$PR_NUMBER" ]; then
  echo "::warning::Could not determine PR number. Is this running on a pull_request event?"
  exit 0
fi

echo "Reviewing PR #${PR_NUMBER} in ${REPO}"

# --- Get PR Diff via GitHub API ---
DIFF=$(curl -s \
  -H "Authorization: token ${GITHUB_TOKEN}" \
  -H "Accept: application/vnd.github.v3.diff" \
  "https://api.github.com/repos/${REPO}/pulls/${PR_NUMBER}")

if [ -z "$DIFF" ] || [ "$DIFF" = "null" ]; then
  echo "::warning::Empty diff received for PR #${PR_NUMBER}"
  exit 0
fi

# --- Export for Iara ---
export OPENROUTER_API_KEY
export PR_DIFF="$DIFF"

if [ -n "$IARA_MODEL" ]; then
  export IARA_MODEL
fi

if [ -n "$IARA_LANGUAGE" ]; then
  export IARA_LANGUAGE
fi

# --- Copy config from workspace if it exists ---
if [ -f "/github/workspace/${CONFIG_PATH}" ]; then
  cp "/github/workspace/${CONFIG_PATH}" /app/.iara.json
fi

# --- Run Iara ---
cd /github/workspace
REVIEW=$(PYTHONPATH=/app python3 -m iara 2>/tmp/iara_stderr.txt || true)

# Print stderr for debugging (visible in Actions log)
if [ -s /tmp/iara_stderr.txt ]; then
  cat /tmp/iara_stderr.txt
fi

if [ -z "$REVIEW" ]; then
  echo "::warning::Iara produced no output"
  exit 0
fi

# --- Output the review (GitHub Action output) ---
{
  echo "review<<IARA_EOF"
  echo "$REVIEW"
  echo "IARA_EOF"
} >> "$GITHUB_OUTPUT"

# --- Post as PR Comment ---
if [ "$POST_COMMENT" = "true" ] && [ -n "$GITHUB_TOKEN" ]; then
  echo "Posting review comment to PR #${PR_NUMBER}..."

  COMMENT_BODY="## 🧜‍♀️ Iara Code Review

${REVIEW}

---
*Reviewed by [Iara](https://github.com/felipefernandes/iara) - AI Code Reviewer*"

  # Use jq to properly escape the body for JSON
  PAYLOAD=$(jq -n --arg body "$COMMENT_BODY" '{"body": $body}')

  HTTP_CODE=$(curl -s -o /tmp/gh_response.txt -w "%{http_code}" \
    -X POST \
    -H "Authorization: token ${GITHUB_TOKEN}" \
    -H "Accept: application/vnd.github.v3+json" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD" \
    "https://api.github.com/repos/${REPO}/issues/${PR_NUMBER}/comments")

  if [ "$HTTP_CODE" -ge 200 ] && [ "$HTTP_CODE" -lt 300 ]; then
    echo "Review posted successfully to PR #${PR_NUMBER}."
  else
    echo "::warning::Failed to post comment (HTTP ${HTTP_CODE})"
    cat /tmp/gh_response.txt
  fi
fi

echo "Done."
