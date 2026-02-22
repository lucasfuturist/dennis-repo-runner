# TESTING_STRATEGY.md

# Testing Strategy (v0.2 - Standardized)

Repo-runner uses **Pytest** for all testing. The suite is designed to be fast (<2s), deterministic, and structurally isolated.

## 1. Test Architecture

We strictly separate **Unit logic** from **Integration flows**.

```text
tests/
├── conftest.py                 # Shared fixtures (temp repos, file factories)
├── unit/                       # Logic tests (1:1 mapping to src/)
│   ├── test_graph_builder.py
│   └── ...
└── integration/                # End-to-end flows (API, CLI, Snapshots)
    ├── test_api.py
    └── ...
```

## 2. Rules of Engagement

1.  **No Artifacts on Disk:**
    *   Never create files in the real filesystem.
    *   ALWAYS use the `temp_repo_root` or `test_dir` fixtures from `conftest.py`.
    *   Tests that leave debris in `tests/fixtures/` will be rejected.

2.  **Performance Budget:**
    *   The full suite must run in **under 5 seconds**.
    *   Current benchmark: ~1.6s for 60+ tests.
    *   Avoid `time.sleep()` unless testing async timeouts.
    *   Avoid huge loops in regex tests (prevent catastrophic backtracking).

3.  **Naming Conventions:**
    *   Files: `test_<module_name>.py`
    *   Classes: `Test<Feature>`
    *   Functions: `test_<scenario>_<expected_outcome>`

## 3. Core Fixtures (`tests/conftest.py`)

Do not reinvent setup logic. Use these fixtures:

*   **`temp_repo_root`**: Returns a path to a clean, empty temp directory. Auto-deletes after test.
*   **`create_file`**: Helper factory to write files to that temp repo.
    ```python
    def test_example(temp_repo_root, create_file):
        create_file("src/main.py", "print('hi')")
        assert os.path.exists(...)
    ```
*   **`simple_repo`**: A pre-populated repo with `src/main.py` and `README.md`.
*   **`complex_repo`**: A repo with nested dirs, `node_modules` (ignored), and mixed languages.

## 4. Execution

Run the suite from the project root:

```powershell
# Standard Run
python -m pytest

# With Coverage (optional)
python -m pytest --cov=src
```

## 5. Continuous Integration

Pull Requests must pass `scripts/verify.ps1` (Windows) or `pytest` (Linux) before merge.
```

