"""Tests for false positive mitigation in system prompt."""

import unittest
from iara.prompt import generate_system_prompt


class TestFalsePositiveMitigation(unittest.TestCase):
    """Test that the system prompt includes anti-false-positive guidelines."""

    def setUp(self):
        """Set up test configuration."""
        self.config = {
            "project": {
                "name": "Test Project",
                "description": "A test project",
                "tech_stack": ["Python"]
            },
            "language": "en"
        }

    def test_prompt_includes_false_positive_section(self):
        """Test that prompt includes false positive guidelines section."""
        prompt = generate_system_prompt(self.config, review_mode="summary")

        self.assertIn("WHAT TO IGNORE (False Positives)", prompt)
        self.assertIn("DO NOT Report These Common False Positives", prompt)

    def test_prompt_includes_cicd_secrets_guidelines(self):
        """Test that prompt includes CI/CD secrets syntax guidelines."""
        prompt = generate_system_prompt(self.config, review_mode="summary")

        # Should mention GitHub Actions syntax
        self.assertIn("secrets.API_KEY", prompt)
        self.assertIn("env.DATABASE_URL", prompt)
        # Should clarify what to report
        self.assertIn("ONLY report if literal string", prompt)

    def test_prompt_includes_security_best_practices_guidelines(self):
        """Test that prompt includes security best practices guidelines."""
        prompt = generate_system_prompt(self.config, review_mode="summary")

        # Should mention os.chmod as correct security practice
        self.assertIn("os.chmod", prompt)
        self.assertIn("0o600", prompt)
        self.assertIn("Security", prompt)
        # Should warn against flagging as performance issue
        self.assertIn("DO NOT flag as", prompt)

    def test_prompt_includes_existing_error_handling_guidelines(self):
        """Test that prompt includes existing error handling guidelines."""
        prompt = generate_system_prompt(self.config, review_mode="summary")

        # Should mention try-except blocks
        self.assertIn("try-except", prompt)
        self.assertIn("missing error handling", prompt)
        # Should instruct to check before reporting
        self.assertIn("Check if exception is caught", prompt)

    def test_prompt_includes_small_scale_performance_guidelines(self):
        """Test that prompt includes small-scale performance guidelines."""
        prompt = generate_system_prompt(self.config, review_mode="summary")

        # Should mention small lists/loops
        self.assertIn("< 10 items", prompt)
        self.assertIn("< 100 iterations", prompt)
        # Should mention O(n) is fine for small scale
        self.assertIn("O(n)", prompt)
        # Should specify threshold
        self.assertIn("N > 100", prompt)

    def test_prompt_includes_framework_conventions_guidelines(self):
        """Test that prompt includes framework conventions guidelines."""
        prompt = generate_system_prompt(self.config, review_mode="summary")

        # Should mention Django and Flask patterns
        self.assertIn("Django", prompt)
        self.assertIn("Flask", prompt)
        self.assertIn("settings.", prompt)
        self.assertIn("app.config", prompt)

    def test_prompt_includes_test_code_guidelines(self):
        """Test that prompt includes test code pattern guidelines."""
        prompt = generate_system_prompt(self.config, review_mode="summary")

        # Should mention test files
        self.assertIn("test_*.py", prompt)
        # Should clarify hardcoded values are expected
        self.assertIn("test fixtures", prompt)
        self.assertIn("EXPECTED", prompt)

    def test_prompt_includes_intentional_suppressions_guidelines(self):
        """Test that prompt includes intentional suppression guidelines."""
        prompt = generate_system_prompt(self.config, review_mode="summary")

        # Should mention suppression comments
        self.assertIn("# type: ignore", prompt)
        self.assertIn("# noqa", prompt)
        self.assertIn("# pylint: disable", prompt)

    def test_prompt_includes_guiding_principle(self):
        """Test that prompt includes conservative reporting guiding principle."""
        prompt = generate_system_prompt(self.config, review_mode="summary")

        # Should include guiding principle
        self.assertIn("Guiding Principle", prompt)
        self.assertIn("When uncertain", prompt)
        self.assertIn("DO NOT REPORT", prompt)
        # Should emphasize focus on real issues
        self.assertIn("bugs, security vulnerabilities", prompt)
        self.assertIn("significant performance degradation", prompt)

    def test_inline_mode_preserves_false_positive_guidelines(self):
        """Test that inline mode also includes false positive guidelines."""
        prompt = generate_system_prompt(self.config, review_mode="inline")

        # Inline mode should have same false positive section
        self.assertIn("WHAT TO IGNORE (False Positives)", prompt)
        self.assertIn("DO NOT Report These Common False Positives", prompt)
        self.assertIn("Guiding Principle", prompt)

    def test_all_eight_antipatterns_included(self):
        """Test that all 8 anti-patterns are included in the prompt."""
        prompt = generate_system_prompt(self.config, review_mode="summary")

        # Count numbered anti-patterns (1. through 8.)
        antipatterns = [
            "1. **CI/CD Secrets Syntax**",
            "2. **Security Best Practices**",
            "3. **Existing Error Handling**",
            "4. **Small-Scale Performance**",
            "5. **Framework Conventions**",
            "6. **Test Code**",
            "7. **Intentional Suppressions**",
            "8. **Code Style (Unless Critical)**"
        ]

        for antipattern in antipatterns:
            self.assertIn(antipattern, prompt, f"Missing anti-pattern: {antipattern}")


if __name__ == "__main__":
    unittest.main()
