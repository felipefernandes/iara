# review-quality Spec Delta

## ADDED Requirements

### Requirement: False Positive Mitigation
The system SHALL include specific guidelines in the system prompt to prevent common false positive patterns and ensure high-precision code reviews.

#### Scenario: CI/CD Secrets Syntax Recognition
- **WHEN** reviewing code that contains CI/CD secret interpolation syntax (e.g., `${{ secrets.API_KEY }}`, `${{ env.DATABASE_URL }}`, `${VAULT_TOKEN}`)
- **THEN** the system MUST NOT flag these as hardcoded secrets
- **AND** ONLY report actual hardcoded literal strings (e.g., `"sk-proj-abc123"`) as security issues

#### Scenario: Security Best Practice Recognition
- **WHEN** reviewing code that uses `os.chmod()` on configuration files or private keys with restrictive permissions (e.g., `0o600`, `0o400`)
- **THEN** the system MUST NOT flag these as performance issues or unnecessary operations
- **AND** recognize them as security hardening best practices

#### Scenario: Existing Error Handling Detection
- **WHEN** reviewing code that already contains try-except blocks for error handling
- **THEN** the system MUST NOT report "missing error handling" for code within those blocks
- **AND** verify the presence of exception handling before suggesting additional error handling

#### Scenario: Small-Scale Performance Tolerance
- **WHEN** reviewing code with lists or loops processing fewer than 10 items
- **THEN** the system MUST NOT suggest micro-optimizations (e.g., "use set for O(1) lookup" for 5-item lists)
- **AND** ONLY flag performance issues for operations with N > 100 iterations or significant scale

#### Scenario: Framework Convention Recognition
- **WHEN** reviewing code that uses framework-specific patterns (e.g., Django `settings.DEBUG`, Flask `app.config['SECRET_KEY']`)
- **THEN** the system MUST NOT flag these as improper global variable usage
- **AND** recognize them as correct framework conventions

#### Scenario: Test Code Pattern Recognition
- **WHEN** reviewing test files (e.g., `test_*.py`, `*_test.py`) that contain hardcoded test fixtures or assert statements without error handling
- **THEN** the system MUST NOT flag these as code quality issues
- **AND** recognize them as expected test patterns

#### Scenario: Intentional Suppression Respect
- **WHEN** reviewing code that contains intentional suppression comments (e.g., `# type: ignore`, `# noqa`, `# pylint: disable`)
- **THEN** the system MUST NOT report issues that are explicitly suppressed
- **AND** respect developer-acknowledged technical decisions

#### Scenario: Conservative Reporting Principle
- **WHEN** the system is uncertain whether something is a real issue
- **THEN** the system MUST err on the side of NOT reporting
- **AND** ONLY flag issues that clearly cause bugs, security vulnerabilities, or significant performance degradation
- **AND** avoid reporting style issues unless they severely impact readability

### Requirement: Prompt Guideline Documentation
The system SHALL maintain clear, concrete examples in the system prompt to guide the LLM away from common false positive patterns.

#### Scenario: Anti-Pattern Examples in Prompt
- **WHEN** generating the system prompt
- **THEN** the prompt MUST include a "WHAT TO IGNORE (False Positives)" section with at least 8 specific anti-patterns
- **AND** each anti-pattern MUST have concrete examples showing ✅ CORRECT vs ❌ INCORRECT patterns
- **AND** examples MUST cover CI/CD syntax, security practices, error handling, performance optimizations, framework conventions, test patterns, suppressions, and style issues

#### Scenario: Guiding Principle Clarity
- **WHEN** generating the system prompt
- **THEN** the prompt MUST include a clear guiding principle: "When uncertain → DO NOT REPORT"
- **AND** emphasize focus on REAL bugs, security vulnerabilities, and significant performance issues only
