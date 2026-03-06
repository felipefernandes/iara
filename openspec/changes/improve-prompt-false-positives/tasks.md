# Tasks: Improve System Prompt to Reduce False Positives

All tasks should be completed in order. Mark with `[x]` when done.

## Implementation Tasks

- [ ] **Update system prompt in `iara/prompt.py`**
  - Locate the existing "WHAT TO IGNORE (False Positives)" section (lines 75-77)
  - Replace with expanded guidelines covering 8 anti-patterns
  - Add clear examples for each anti-pattern (✅ CORRECT vs ❌ INCORRECT)
  - Ensure formatting is consistent with rest of prompt
  - Verify prompt length doesn't exceed model context limits

- [ ] **Add guiding principle statement**
  - Insert at end of false positive section
  - Clear guidance: "When uncertain → DO NOT REPORT"
  - Emphasize focus on REAL bugs/security/performance issues only

## Testing Tasks

- [ ] **Create test suite for false positives**
  - Create `tests/test_prompt_false_positives.py`
  - Test Case 1: GitHub Actions secrets (`${{ secrets.X }}`)
  - Test Case 2: Security chmod (`os.chmod(file, 0o600)`)
  - Test Case 3: Existing try-except blocks
  - Test Case 4: Small list iterations (< 10 items)
  - Each test should verify NO false positive is generated

- [ ] **Run regression tests**
  - Ensure existing test suite passes (`pytest tests/`)
  - Verify real bugs are still caught (test_reviewer.py)
  - Check security issues still detected (test_security.py if exists)
  - Confirm performance issues still flagged (test_performance.py if exists)

- [ ] **Manual validation with real PRs**
  - Test against PR #69 (Groq provider) where false positives were found
  - Test against PR #63 (documentation) to verify no style complaints
  - Test against PR with real security issues (if available in history)
  - Document before/after false positive counts

## Documentation Tasks

- [ ] **Update CHANGELOG.md**
  - Add entry under `[Unreleased]` section
  - Category: 🔧 Improvements
  - Description: "Improved system prompt to reduce false positives by 50-70%"
  - List specific anti-patterns addressed

- [ ] **Update docs/configuration.md (optional)**
  - Add note about false positive reduction in "Review Quality" section
  - Mention that users can still customize prompts via config if needed

## Validation Tasks

- [ ] **Measure false positive rate**
  - Before: Run Iara on 5-10 PRs, count false positives
  - After: Run updated Iara on same PRs, count false positives
  - Calculate reduction percentage
  - Document findings in PR description

- [ ] **User feedback validation**
  - Share updated version with 2-3 beta users (if available)
  - Collect feedback on review relevance
  - Verify no critical bugs are being missed

## Optional Tasks (Post-Release)

- [ ] **A/B testing setup** (optional)
  - Add feature flag to toggle between old/new prompt
  - Compare false positive rates in production
  - Gather user sentiment data

## Dependencies

- No external dependencies
- Must complete implementation before testing
- Manual validation requires access to historical PRs
- All tasks can be done sequentially by a single developer

## Estimated Time

- Implementation: 30 minutes
- Testing: 30-45 minutes
- Documentation: 15 minutes
- Validation: 30 minutes

**Total**: 1.5-2 hours (Quick Win ✅)
