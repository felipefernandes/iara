# review-quality Spec Delta

## ADDED Requirements

### Requirement: Per-Comment Confidence Score
The system SHALL include a confidence score (0.0 to 1.0) on every LLM-generated inline comment and SHALL validate it during parsing.

#### Scenario: Valid Confidence Score
- **WHEN** the LLM returns an inline comment with `"confidence": 0.9`
- **THEN** the parser MUST accept the comment
- **AND** preserve the confidence value for filtering

#### Scenario: Out-of-Range Confidence Score
- **WHEN** the LLM returns a `confidence` value outside 0.0 to 1.0 (e.g., `1.4` or `-0.2`)
- **THEN** the parser MUST clamp the value into 0.0 to 1.0
- **AND** log a warning identifying the comment

#### Scenario: Missing Confidence Score
- **WHEN** an inline comment omits the `confidence` field
- **THEN** the parser MUST treat the confidence as `0.0`
- **AND** the comment MUST be filtered by the default threshold (0.7)

### Requirement: Prompt Requests Confidence Ratings
The system SHALL instruct the LLM to rate its confidence in every inline comment using a 0.0 to 1.0 rubric.

#### Scenario: Prompt Includes Confidence Rubric
- **WHEN** the inline review system prompt is generated
- **THEN** it MUST include the rubric:
  - 0.9-1.0: Definite bug/issue
  - 0.7-0.9: Highly likely issue
  - 0.5-0.7: Possible issue worth reviewing
  - 0.3-0.5: Speculative suggestion
  - 0.0-0.3: Low confidence observation

### Requirement: Confidence Threshold Filtering
The system SHALL filter inline review comments with confidence below the configured minimum before posting.

#### Scenario: Low-Confidence Comment Filtered
- **WHEN** `review.min_confidence` is `0.7` (or not configured)
- **AND** a comment has `confidence: 0.3`
- **THEN** the system MUST NOT post that comment
- **AND** log the number of filtered comments at INFO level

#### Scenario: High-Confidence Comment Posted
- **WHEN** `review.min_confidence` is `0.7`
- **AND** a comment has `confidence: 0.9`
- **THEN** the system MUST post the comment normally

#### Scenario: Boundary Is Inclusive
- **WHEN** `review.min_confidence` is `0.7`
- **AND** a comment has `confidence: 0.7`
- **THEN** the system MUST post the comment (threshold applies with `>=`)

#### Scenario: Threshold Disables Filtering
- **WHEN** `review.min_confidence` is `0.0`
- **THEN** the system MUST post all comments regardless of confidence

#### Scenario: Summary Mode Unaffected
- **WHEN** `ci.review_mode` is `summary`
- **THEN** confidence thresholds MUST NOT alter summary output

### Requirement: Configurable Minimum Confidence
The system SHALL support an optional `review.min_confidence` configuration value in `.iara.json`.

#### Scenario: Default Threshold
- **WHEN** `min_confidence` is not configured
- **THEN** the system MUST use `0.7` as the default threshold

#### Scenario: Invalid Threshold Value
- **WHEN** `min_confidence` is not a number or is outside 0.0 to 1.0
- **THEN** the system MUST fall back to the default `0.7`
- **AND** log a warning
