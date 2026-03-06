# Improve System Prompt to Reduce False Positives

**Change ID**: `improve-prompt-false-positives`
**Related Issue**: [#70](https://github.com/felipefernandes/iara/issues/70)
**Complexity**: 🟢 Quick Win (1-2 hours)

## Why

The current system prompt in `iara/prompt.py` generates false positives that reduce user trust and create noise in code reviews. Observed false positives include:

1. **GitHub Actions Secrets**: Reporting `${{ secrets.API_KEY }}` as hardcoded secrets (it's correct CI/CD syntax)
2. **Security Best Practices**: Flagging `os.chmod(config_file, 0o600)` as performance issues (it's intentional security hardening)
3. **Existing Error Handling**: Reporting "missing error handling" when try-except blocks already exist
4. **Premature Optimization**: Suggesting O(1) lookups for small lists (< 10 items) where O(n) is negligible

These false positives were identified during Groq provider integration (#67) and real-world usage.

## What Changes

### Modified Capabilities
- **Prompt Engineering** (`iara/prompt.py`)

### Expected Impact
- **50-70% reduction** in false positive rate
- More **focused and actionable** reviews
- Better **user trust** in the tool
- No performance degradation (purely prompt changes)

## Solution Approach

Expand the existing "WHAT TO IGNORE (False Positives)" section in the system prompt with specific, concrete examples of common false positives. This leverages the LLM's in-context learning without requiring model retraining.

### Key Additions

Add **8 specific anti-patterns** to avoid:

1. **CI/CD Syntax**: `${{ secrets.X }}`, `${{ env.X }}`, `${VAR}` are NOT hardcoded
2. **Security Hardening**: `os.chmod` on configs is GOOD (security best practice)
3. **Existing Error Handling**: Don't report "missing" handling when try-except exists
4. **Small Scale Optimizations**: < 10 items → O(n) vs O(1) is negligible
5. **Framework Conventions**: Django `settings.py` globals, Flask `app.config` are CORRECT
6. **Test Code Patterns**: Hardcoded values in tests are EXPECTED
7. **Type Hints**: `# type: ignore` comments are INTENTIONAL
8. **Conservative Reporting**: When uncertain → DON'T report

### Prompt Structure Changes

**Before** (2 generic rules):
```python
### ❌ WHAT TO IGNORE (False Positives):
- Don't complain about style unless it seriously hurts readability.
- Don't complain about global variables if they are project convention (e.g., configs).
```

**After** (10 specific guidelines):
```python
### ❌ WHAT TO IGNORE (False Positives):

**🚫 DO NOT Report These Common False Positives:**

1. **CI/CD Secrets Syntax**:
   - ✅ `${{ secrets.API_KEY }}` (GitHub Actions - CORRECT)
   - ✅ `${{ env.DATABASE_URL }}` (CI environment variables - CORRECT)
   - ✅ `${VAULT_TOKEN}` (Variable interpolation - CORRECT)
   - ❌ ONLY report if literal string like `"sk-proj-abc123"` is hardcoded

2. **Security Best Practices**:
   - ✅ `os.chmod(config, 0o600)` (File permission hardening - CORRECT)
   - ✅ `os.chmod(private_key, 0o400)` (Security requirement - CORRECT)
   - ❌ DO NOT flag as "performance issue" or "unnecessary"

3. **Existing Error Handling**:
   - ✅ Code already has `try-except` block → DO NOT report "missing error handling"
   - ✅ Check if exception is caught BEFORE suggesting to add handling

4. **Small-Scale Performance**:
   - ✅ Lists with < 10 items → O(n) linear search is FINE
   - ✅ Small loops (< 100 iterations) → Micro-optimizations NOT worth it
   - ❌ ONLY report performance issues for large-scale operations (N > 100)

5. **Framework Conventions**:
   - ✅ Django: `settings.DEBUG`, `settings.DATABASES` (correct usage)
   - ✅ Flask: `app.config['SECRET_KEY']` (framework pattern)
   - ✅ Configuration globals in config files (project convention)

6. **Test Code**:
   - ✅ Hardcoded values in `test_*.py` files (test fixtures - EXPECTED)
   - ✅ `assert` statements without error handling (test assertions - CORRECT)

7. **Intentional Suppressions**:
   - ✅ `# type: ignore` comments (developer acknowledged type issue)
   - ✅ `# noqa` comments (linting suppression - intentional)
   - ✅ `# pylint: disable` (intentional linting override)

8. **Code Style (Unless Critical)**:
   - ✅ Formatting, naming conventions → IGNORE unless severely impacts readability
   - ✅ Personal preferences (e.g., single vs double quotes) → IGNORE

**🎯 Guiding Principle**:
When uncertain if something is a real issue → **DO NOT REPORT**.
Only flag issues that would cause **bugs, security vulnerabilities, or significant performance degradation**.
```

## Out of Scope

- **Post-processing filters** (Issue #71) - Separate implementation
- **Confidence scores** (Issue #72) - Requires LLM API changes
- **RAG-based documentation** (Issue #73) - Requires memory system
- **Self-review validation** (Issue #74) - Multi-pass approach

This change focuses **solely on prompt engineering** as a Quick Win solution.

## Validation Strategy

### Before/After Comparison

Test against known false positive cases:

```python
# Test Case 1: GitHub Actions Secrets
diff = """
+ OPENROUTER_API_KEY="${{ secrets.OPENROUTER_API_KEY }}"
"""
# Expected: NO "hardcoded secret" warning

# Test Case 2: Security Chmod
diff = """
+ os.chmod(config_file, 0o600)  # Restrict permissions to owner only
"""
# Expected: NO "performance issue" warning

# Test Case 3: Existing Try-Except
diff = """
  try:
      result = api_call()
  except RequestException as e:
+     logger.error(f"API call failed: {e}")
      return None
```
# Expected: NO "missing error handling" warning

# Test Case 4: Small List Iteration
diff = """
+ for user in users[:5]:  # Process first 5 users only
+     send_notification(user)
"""
# Expected: NO "use set for O(1) lookup" suggestion
```

### Success Metrics

- ✅ False positive rate drops by 50-70%
- ✅ No increase in false negatives (still catches real issues)
- ✅ User feedback: reviews feel more relevant and actionable

## Dependencies

- No code dependencies (prompt-only change)
- No breaking changes (backward compatible)
- No new packages or external services
