# Design: Intelligent Diff Compression

## Architectural Reasoning

The Diff Compressor tackles the problem of PR diff truncation. We need to respect LLM token limits while ensuring the LLM is aware of all changes across a pull request.

### Components
1. **`DiffCompressor`**: A new service class in `iara/diff_compressor.py`.
   - Parses the raw diff string into logical blocks representing files (`DiffFile`).
   - Employs a local length measurement check to determine if compression is necessary based on `max_diff_tokens`.
   - Compresses the files by stripping contextual lines (those without `+` or `-`) if over the threshold, ensuring all files maintain their headers and primary changes.
2. **Reviewer Integration**: `iara/reviewer.py` will instantiate and employ `DiffCompressor` when preparing the input prompt. Previous naive hard-limiting logic (`diff = diff[:max_chars]`) will be removed.
3. **Configuration**: Extend `.iara.json` schema to support `review.max_diff_tokens` (default 12000).

### Trade-offs
- **Loss of Unmodified Context**: By removing unmodified context lines to fit within a limit, the LLM might miss some immediate surroundings of the changed code. However, this trade-off is required and significantly better than entirely dropping the end of the diff, which leads to fundamentally incomplete reviews.
