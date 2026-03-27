#!/bin/bash
set -e

# ============================================
# Iara Code Reviewer - GitHub Action Entrypoint
# ============================================

# --- GitLab CI Native Flow ---
# When running inside GitLab CI, skip GitHub Actions INPUT_* extraction entirely.
# Variables are already injected by GitLab CI as-is; overwriting them with empty
# INPUT_* values would cause validation to fail immediately.
if [ "${GITLAB_CI:-}" = "true" ]; then
  echo "GitLab CI detected — using native GitLab CI flow."

  # Validate API key presence (provider auto-detected by iara CLI)
  API_KEY_SET=false
  for var in OPENROUTER_API_KEY OPENAI_API_KEY GEMINI_API_KEY ANTHROPIC_API_KEY GROQ_API_KEY; do
    if [ -n "${!var}" ]; then
      API_KEY_SET=true
      break
    fi
  done
  if [ "$API_KEY_SET" = "false" ]; then
    echo "ERROR: No API key found. Set OPENROUTER_API_KEY (or another provider key) in CI/CD variables."
    exit 1
  fi

  # Only run on merge request events
  if [ -z "${CI_MERGE_REQUEST_IID:-}" ]; then
    echo "Not a merge request event (CI_MERGE_REQUEST_IID is empty). Skipping review."
    exit 0
  fi

  echo "Reviewing MR !${CI_MERGE_REQUEST_IID} in ${CI_PROJECT_PATH}"

  # Generate diff via git (no external API call needed)
  git fetch origin "${CI_MERGE_REQUEST_TARGET_BRANCH_NAME}" 2>/dev/null || true
  export PR_DIFF
  PR_DIFF=$(git diff "origin/${CI_MERGE_REQUEST_TARGET_BRANCH_NAME}...${CI_COMMIT_SHA}" 2>/dev/null || true)

  if [ -z "$PR_DIFF" ]; then
    echo "WARNING: Empty diff. Skipping review."
    exit 0
  fi

  # Run Iara review
  REVIEW=$(PYTHONPATH=/app python3 -m iara 2>/tmp/iara_stderr.txt || true)

  if [ -s /tmp/iara_stderr.txt ]; then
    cat /tmp/iara_stderr.txt
  fi

  if [ -z "$REVIEW" ]; then
    echo "WARNING: Iara produced no output."
    exit 0
  fi

  echo "$REVIEW"

  # Post comment to MR if GITLAB_TOKEN is configured
  if [ -n "${GITLAB_TOKEN:-}" ]; then
    echo "Posting review comment to MR !${CI_MERGE_REQUEST_IID}..."
    echo "$REVIEW" | PYTHONPATH=/app python3 -m iara.post_comment - && \
      echo "Review posted successfully." || \
      echo "WARNING: Failed to post review comment."
  else
    echo "GITLAB_TOKEN not set — skipping comment posting."
  fi

  exit 0
fi

# --- Input Variables (from action.yml inputs) ---
OPENROUTER_API_KEY="${INPUT_OPENROUTER_API_KEY}"
OPENAI_API_KEY="${INPUT_OPENAI_API_KEY}"
GEMINI_API_KEY="${INPUT_GEMINI_API_KEY}"
ANTHROPIC_API_KEY="${INPUT_ANTHROPIC_API_KEY}"
GROQ_API_KEY="${INPUT_GROQ_API_KEY}"
PROVIDER="${INPUT_PROVIDER:-openrouter}"
PROVIDER=$(echo "$PROVIDER" | tr '[:upper:]' '[:lower:]')
IARA_MODEL="${INPUT_MODEL}"
IARA_LANGUAGE="${INPUT_LANGUAGE}"
IARA_REVIEW_MODE="${INPUT_REVIEW_MODE:-summary}"
CONFIG_PATH="${INPUT_CONFIG_PATH:-.iara.json}"
POST_COMMENT="${INPUT_POST_COMMENT:-true}"

# --- GitHub Context Variables ---
export GITHUB_TOKEN="${INPUT_GITHUB_TOKEN:-$GITHUB_TOKEN}"
export REPO="${INPUT_GITHUB_REPOSITORY:-$GITHUB_REPOSITORY}"
export GITHUB_EVENT_PATH="${INPUT_GITHUB_EVENT_PATH:-$GITHUB_EVENT_PATH}"

# --- Validate Provider ---
case "$PROVIDER" in
  openrouter|openai|gemini|anthropic|groq)
    ;;
  *)
    echo "::error::Invalid provider '$PROVIDER'. Supported: openrouter, openai, gemini, anthropic, groq."
    exit 1
    ;;
esac

# --- Validate Required Inputs ---
KEY_COUNT=0
KEY_LABELS=()
if [ -n "$OPENROUTER_API_KEY" ]; then
  KEY_COUNT=$((KEY_COUNT + 1))
  KEY_LABELS+=("openrouter")
fi
if [ -n "$OPENAI_API_KEY" ]; then
  KEY_COUNT=$((KEY_COUNT + 1))
  KEY_LABELS+=("openai")
fi
if [ -n "$GEMINI_API_KEY" ]; then
  KEY_COUNT=$((KEY_COUNT + 1))
  KEY_LABELS+=("gemini")
fi
if [ -n "$ANTHROPIC_API_KEY" ]; then
  KEY_COUNT=$((KEY_COUNT + 1))
  KEY_LABELS+=("anthropic")
fi
if [ -n "$GROQ_API_KEY" ]; then
  KEY_COUNT=$((KEY_COUNT + 1))
  KEY_LABELS+=("groq")
fi

if [ "$KEY_COUNT" -gt 1 ]; then
  echo "::warning::Multiple provider API keys provided (${KEY_LABELS[*]}). Using only '${PROVIDER}'."
fi

if [ "$PROVIDER" = "openai" ]; then
  if [ -z "$OPENAI_API_KEY" ]; then
    echo "::error::OPENAI_API_KEY is required. Add it as a repository secret."
    exit 1
  fi
elif [ "$PROVIDER" = "gemini" ]; then
  if [ -z "$GEMINI_API_KEY" ]; then
    echo "::error::GEMINI_API_KEY is required. Add it as a repository secret."
    exit 1
  fi
elif [ "$PROVIDER" = "anthropic" ]; then
  if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "::error::ANTHROPIC_API_KEY is required. Add it as a repository secret."
    exit 1
  fi
elif [ "$PROVIDER" = "groq" ]; then
  if [ -z "$GROQ_API_KEY" ]; then
    echo "::error::GROQ_API_KEY is required. Add it as a repository secret."
    exit 1
  fi
else
  if [ -z "$OPENROUTER_API_KEY" ]; then
    echo "::error::OPENROUTER_API_KEY is required. Add it as a repository secret."
    exit 1
  fi
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

export PR_NUMBER
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
if [ "$PROVIDER" = "openai" ]; then
  export OPENAI_API_KEY
elif [ "$PROVIDER" = "gemini" ]; then
  export GEMINI_API_KEY
elif [ "$PROVIDER" = "anthropic" ]; then
  export ANTHROPIC_API_KEY
elif [ "$PROVIDER" = "groq" ]; then
  export GROQ_API_KEY
else
  export OPENROUTER_API_KEY
fi

export IARA_PROVIDER="$PROVIDER"
export PR_DIFF="$DIFF"

if [ -n "$IARA_MODEL" ]; then
  export IARA_MODEL
fi

if [ -n "$IARA_LANGUAGE" ]; then
  export IARA_LANGUAGE
fi

if [ -n "$IARA_REVIEW_MODE" ]; then
  export IARA_REVIEW_MODE
fi

# --- Copy config from workspace if it exists ---
if [ -f "/github/workspace/${CONFIG_PATH}" ]; then
  cp "/github/workspace/${CONFIG_PATH}" /app/.iara.json
fi

# --- Run Indexing (Optional) ---
INDEX_CODEBASE="${INPUT_INDEX_CODEBASE:-false}"
if [ "$INDEX_CODEBASE" = "true" ]; then
  echo "🧠 Indexing codebase for RAG memory..."
  cd /github/workspace
  PYTHONPATH=/app python3 -m iara memory index || echo "::warning::Failed to index codebase via RAG."
  cd /app
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

  # Use the new post_comment module which supports inline and summary modes
  # Pass "-" to indicate reading from stdin (review text is piped via echo)
  echo "$REVIEW" | PYTHONPATH=/app python3 -m iara.post_comment -

  if [ $? -eq 0 ]; then
    echo "Review posted successfully to PR #${PR_NUMBER}."
  else
    echo "::warning::Failed to post review comment"
  fi
fi

echo "Done."
