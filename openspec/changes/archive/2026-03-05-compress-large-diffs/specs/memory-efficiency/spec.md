## ADDED Requirements

### Requirement: Intelligent Local Diff Compression
When a Pull Request diff size is exceedingly large, it MUST be smartly compressed using a local, rule-based approach before being provided to the LLM for review. This prevents hard truncation that causes the LLM to miss files or misinterpret incomplete functions.

- **Configurability:** A `max_diff_tokens` parameter (default 12000) under the `review` namespace controls the start and target threshold of the compression algorithm.
- **Prioritization Rule:** The compressor prioritizes file headers (`diff --git`, `@@`) and directly modified lines (`+` and `-`), stripping contextual/unmodified lines when over the size threshold.
- **Token Optimization Tracking:** Any compression applied must log an informational message indicating original size, compressed size, and the percentage reduced.

#### Scenario: Submitting a PR diff that fits the limit
Given a pull request diff containing fewer tokens than the limit
And the configured limit `review.max_diff_tokens` is 12000
When the diff is processed by the Reviewer module
Then the DiffCompressor returns the original diff uncompressed
And no compression is logged

#### Scenario: Submitting a PR diff exceeding the limit
Given a pull request diff of large amounts of characters spanning multiple files
And the configured limit `review.max_diff_tokens` restricts the payload length
When the diff is processed by the Reviewer module
Then the DiffCompressor applies rules to prioritize headers and changed lines
And strips unmodified lines
And avoids omitting the end of the PR
And the logger prints the compression reduction values
And the smartly compressed diff is successfully sent to the LLM agent
