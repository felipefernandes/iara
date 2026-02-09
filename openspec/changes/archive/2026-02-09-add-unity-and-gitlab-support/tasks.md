## 1. Extension System & Scanning Mode
- [ ] 1.1 Refactor `ai-codereview.py` to use `argparse` for arguments (`--scan`, `--diff`)
- [ ] 1.2 Implement `scan_directory(path)` function in `ai-codereview.py`
- [ ] 1.3 Create `extensions/` directory and `extensions/__init__.py`
- [ ] 1.4 Implement extension loading logic in `ai-codereview.py`

## 2. Unity Extension
- [ ] 2.1 Create `extensions/unity.py`
- [ ] 2.2 Implement `UnityReviewer` class (or function) with regex triggers for common pitfalls
- [ ] 2.3 Integrate Unity extension into the scanning loop

## 3. GitLab CI
- [ ] 3.1 Create `gitlab-ci.yml` template file
- [ ] 3.2 Document GitLab CI usage in `README.md`

## 4. Verification
- [ ] 4.1 Create dummy Unity C# script with bugs
- [ ] 4.2 Run `ai-codereview.py --scan` and verify it catches the bugs
- [ ] 4.3 Verify GitLab CI template syntax
