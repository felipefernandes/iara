# review-quality Spec Delta

## ADDED Requirements

### Requirement: Post-Processing False Positive Filtering
The system SHALL filter out known false positive patterns from inline review comments before posting them to pull requests.

#### Scenario: Pattern-Based Filtering
- **WHEN** inline review comments are parsed from LLM output
- **THEN** the system MUST apply false positive filters before posting
- **AND** filter comments matching any configured pattern
- **AND** log each filtered comment with reason

#### Scenario: GitHub Actions Secrets Pattern
- **WHEN** a comment reports "hardcoded secret" in a `.github/workflows/*.yml` file
- **AND** the diff context contains `${{ secrets.` syntax
- **THEN** the system MUST filter out this comment
- **AND** log: "GitHub Actions secrets syntax is correct"

#### Scenario: Security Chmod Pattern
- **WHEN** a comment flags `os.chmod()` as a performance issue
- **AND** the diff context contains restrictive permissions (e.g., `0o600`, `0o400`)
- **THEN** the system MUST filter out this comment
- **AND** log: "File permission hardening is security best practice"

#### Scenario: Existing Error Handling Pattern
- **WHEN** a comment reports "missing error handling"
- **AND** the diff context does NOT contain `try:` and `except` blocks
- **THEN** the system MUST NOT filter this comment (it's a real issue)
- **BUT** when context DOES contain try-except
- **THEN** the system MUST filter out this comment
- **AND** log: "Error handling already present in context"

#### Scenario: Small-Scale Performance Pattern
- **WHEN** a comment suggests performance optimization (e.g., "use set for O(1) lookup")
- **AND** the diff context contains small-scale indicators (e.g., `range(5)`, `[:10]`, `< 10`)
- **THEN** the system MUST filter out this comment
- **AND** log: "Micro-optimizations unnecessary for small scale"

#### Scenario: Real Bug Not Filtered
- **WHEN** a comment reports a logic error, security vulnerability, or performance issue
- **AND** the comment does NOT match any false positive pattern
- **THEN** the system MUST NOT filter this comment
- **AND** post it normally to the pull request

#### Scenario: Filtering Failure Fallback
- **WHEN** the filtering process encounters an error (e.g., regex compilation error)
- **THEN** the system MUST log the error
- **AND** post all original comments without filtering (fail-safe behavior)
- **AND** NOT crash or fail the review process

### Requirement: Configurable False Positive Patterns
The system SHALL allow projects to define custom false positive patterns in `.iara.json` configuration.

#### Scenario: Default Patterns Included
- **WHEN** no custom patterns are configured
- **THEN** the system MUST use built-in default patterns (at least 4):
  - GitHub Actions secrets syntax
  - Security chmod best practices
  - Existing error handling
  - Small-scale performance optimizations

#### Scenario: Custom Pattern Definition
- **WHEN** `.iara.json` contains `review.false_positive_patterns` array
- **THEN** the system MUST load and apply these patterns in addition to defaults
- **AND** each pattern MUST support:
  - `name` (optional): Human-readable identifier
  - `file_pattern` (optional): Regex to match file paths
  - `message_pattern` (required): Regex to match comment messages
  - `context_safe` (optional): Regex - if found in context, filter comment
  - `context_unsafe` (optional): Regex - if NOT found in context, filter comment
  - `reason` (optional): Explanation logged when filtering

#### Scenario: Custom Pattern Example (Django Settings)
- **WHEN** `.iara.json` contains:
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
- **AND** a comment flags "global variable usage" in `settings.py`
- **THEN** the system MUST filter this comment
- **AND** log: "Django settings.py uses globals by convention"

#### Scenario: Context Extraction from Diff
- **WHEN** filtering a comment for line N in file F
- **THEN** the system MUST extract context from the diff:
  - Find the file section in diff (`+++ b/F`)
  - Parse hunk headers to track line numbers
  - Extract 3 lines before and 3 lines after line N
  - Return context string for pattern matching
- **AND** if line N not found in diff, return empty context (safe fallback)

#### Scenario: Pattern Matching Logic
- **WHEN** evaluating a comment against a pattern
- **THEN** the system MUST:
  1. Skip pattern if `file_pattern` specified and file doesn't match
  2. Skip pattern if `message_pattern` doesn't match comment message
  3. If `context_safe` specified: filter ONLY if pattern found in context
  4. If `context_unsafe` specified: filter ONLY if pattern NOT found in context
  5. If no context condition: filter based on message match alone
- **AND** use case-insensitive matching for all regex patterns
- **AND** filter comment if ANY pattern fully matches

### Requirement: Filtering Observability
The system SHALL provide clear logging and metrics for filtered comments.

#### Scenario: Filtered Comment Logging
- **WHEN** a comment is filtered out
- **THEN** the system MUST log at INFO level:
  - File path and line number
  - First 60 characters of the message
  - Pattern name that triggered the filter
  - Reason for filtering
- **EXAMPLE**: `INFO: Filtered false positive in .github/workflows/ci.yml:15 - 🔒 Potential hardcoded secret detected... (Pattern: github-actions-secrets)`

#### Scenario: Filtering Summary
- **WHEN** filtering completes for a review
- **AND** at least one comment was filtered
- **THEN** the system MUST log at INFO level the total count
- **EXAMPLE**: `INFO: Filtered 3 false positive(s)`

#### Scenario: No Comments Filtered
- **WHEN** no comments match any false positive pattern
- **THEN** the system MUST NOT log filtering summary
- **AND** proceed normally with posting all comments

#### Scenario: Debug Pattern Matching
- **WHEN** logger level is set to DEBUG
- **AND** a pattern matches a comment
- **THEN** the system MUST log at DEBUG level:
  - Pattern name
  - Pattern reason
  - Matched file/message/context conditions
- **EXAMPLE**: `DEBUG: False positive detected: github-actions-secrets - GitHub Actions secrets syntax is correct`
