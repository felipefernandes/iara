# Tasks

- [x] 1. Update `iara/config.py` to include `"max_index_file_size": 1048576` under the `review` dictionary in `DEFAULT_CONFIG`.
- [x] 2. Update `iara/memory/indexer.py` `Indexer`'s `__init__` or `index_project` to fetch the config value (or allow injecting it). 
- [x] 3. Insert conditional size check `os.path.getsize(file_path)` inside `os.walk` iteration before opening the file.
- [x] 4. Skip files greater than `max_index_file_size` and append skipping telemetry/logging at the debug level.
- [x] 5. Add basic unit tests to simulate passing files exceeding size and verify they are omitted before caching strings. Verify that adjusting `.iara.json` affects the limit in tests.
