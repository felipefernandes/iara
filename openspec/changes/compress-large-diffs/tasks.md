# Tasks

1. **[Config]** - [x] Add `max_diff_tokens` setting initialized to 12000 under `review` configuration dictionaries.
2. **[Diff Parser]** - [x] Create `iara/diff_compressor.py` with the `DiffCompressor` class and implement a parsing setup `_parse_diff_files` that extracts individual file changes separated by `diff --git`.
3. **[Compression Rules]** - [x] Implement the compression logic in `_prioritize_and_compress`. Prioritize headers, added lines (`+`), and removed lines (`-`), stripping surrounding context lines if the diff length breaches `max_diff_tokens`. Guarantee every file is preserved in the resulting un-truncated diff.
4. **[Reviewer Integration]** - [x] Integrate `DiffCompressor` into `iara/reviewer.py` in the `review_code` block. Process the incoming diff payload through `DiffCompressor.compress()` and remove the old naive `15000` hard limit truncation.
5. **[Logging Integration]** - [x] Validate that a log trace is reported when compression runs, matching the required footprint (`🗜️ Diff compressed: 30KB → 6KB (80% reduction)`).
6. **[Testing]** - [x] Develop unit tests in `tests/test_diff_compressor.py` validating that small diffs return untouched, large diffs execute contextual reduction, and the output holds all headers accurately.
