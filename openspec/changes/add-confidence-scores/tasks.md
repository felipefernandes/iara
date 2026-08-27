## 1. Implementation
- [ ] 1.1 Update `iara/prompt.py` to request a 0.0-1.0 confidence rating for every inline comment
- [ ] 1.2 Update `iara/parsers/inline_parser.py` to require `confidence` and validate `0.0 <= confidence <= 1.0` (clamp out-of-range values with a warning)
- [ ] 1.3 Add confidence threshold filtering to the inline flow in `iara/post_comment.py`
- [ ] 1.4 Add optional `review.min_confidence` config option (default 0.7) with validation
- [ ] 1.5 Update `.iara.json` and documentation (README, docs/ci-integration.md)

## 2. Testing
- [ ] 2.1 Parser: valid, missing, non-numeric, and out-of-range confidence values
- [ ] 2.2 Filter: inclusive boundary (>=), default 0.7, and 0.0 disables filtering
- [ ] 2.3 End-to-end: inline review with mixed confidence posts only comments >= threshold
- [ ] 2.4 Fail-safe: malformed confidence values never crash the review
