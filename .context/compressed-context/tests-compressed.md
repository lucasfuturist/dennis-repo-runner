## High-Resolution Interface Map: repo-runner Tests

### Tree
```
└── tests
    ├── __init__.py
    ├── conftest.py
    ├── integration
    │   ├── __init__.py
    │   ├── test_api.py
    │   ├── test_cli_diff.py
    │   ├── test_cli_slice.py
    │   ├── test_e2e_snapshot.py
    │   ├── test_export_flow.py
    │   ├── test_graph_snapshot.py
    │   └── test_robustness.py
    └── unit
        ├── __init__.py
        ├── test_config_loader.py
        ├── test_context_slicer.py
        ├── test_file_fingerprint.py
        ├── test_filesystem_scanner.py
        ├── test_flatten_exporter.py
        ├── test_graph_builder.py
        ├── test_ignore_logic.py
        ├── test_import_scanner.py
        ├── test_path_normalizer.py
        ├── test_snapshot_comparator.py
        ├── test_snapshot_loader.py
        ├── test_structure_builder.py
        ├── test_token_telemetry.py
        └── test_types.py
```

---

### File Summaries

### `tests/conftest.py`
**Role:** Provides shared pytest fixtures for temporary filesystem orchestration and mock repository generation.
**Key Exports:**
- `temp_repo_root(): str` - A generator fixture that creates and cleans up a unique temporary directory for repository simulation.
- `create_file(temp_repo_root): Callable` - A factory fixture for generating files with specific content within the test environment.
- `complex_repo(temp_repo_root, create_file): str` - A fixture that populates a multi-language, nested directory structure for integration testing.
**Dependencies:** `os`, `shutil`, `tempfile`

### `tests/integration/test_api.py`
**Role:** Validates the FastAPI server's lifecycle, including snapshot creation, context slicing, and comparison endpoints.
**Key Exports:**
- `test_full_api_lifecycle()` - Verifies the end-to-end flow from initial ingestion to structural comparison.
- `test_slice_with_token_limit()` - Ensures the API correctly prunes context when a `max_tokens` constraint is provided.
**Dependencies:** `src.api.server`, `fastapi.testclient`

### `tests/integration/test_cli_diff.py`
**Role:** Ensures the command-line interface correctly parses arguments and dispatches them to the snapshot comparison engine.
**Key Exports:**
- `test_diff_command_parsing()` - Validates that CLI flags map correctly to the internal `run_compare` controller.
**Dependencies:** `src.cli.main`, `src.core.controller`

### `tests/integration/test_cli_slice.py`
**Role:** Verifies CLI argument handling for the context slicing and Markdown export commands.
**Key Exports:**
- `test_slice_command_invocation()` - Checks that `radius` and `max_tokens` flags reach the export controller with correct types.
**Dependencies:** `src.cli.main`, `src.core.controller`

### `tests/integration/test_e2e_snapshot.py`
**Role:** Tests the high-level snapshot creation logic, ensuring all JSON artifacts and exports are generated on disk.
**Key Exports:**
- `test_snapshot_creation_with_graph_and_auto_export()` - Confirms that a single run produces manifests, structure, and dependency graphs.
**Dependencies:** `src.core.controller`, `src.snapshot.snapshot_loader`

### `tests/integration/test_export_flow.py`
**Role:** Validates the conversion of snapshots into Markdown documentation across different scopes (full vs. module-limited).
**Key Exports:**
- `test_export_scoped()` - Ensures that exports restricted to specific modules exclude files outside that directory.
**Dependencies:** `src.core.controller`

### `tests/integration/test_graph_snapshot.py`
**Role:** Validates that the dependency graph is correctly analyzed and persisted during a standard snapshot run.
**Key Exports:**
- `test_end_to_end_graph_generation()` - Confirms that internal file-to-file and external-to-package edges are captured in JSON.
**Dependencies:** `src.core.controller`, `src.snapshot.snapshot_loader`

### `tests/integration/test_robustness.py`
**Role:** Checks system stability against filesystem edge cases like symlink cycles and mixed health states.
**Key Exports:**
- `test_snapshot_with_mixed_health()` - Verifies that symlink loops do not cause infinite recursion in the scanner.
**Dependencies:** `src.core.controller`, `src.scanner.filesystem_scanner`

### `tests/unit/test_config_loader.py`
**Role:** Tests the robust parsing of `repo-runner.json` files and fallback behavior for invalid configurations.
**Key Exports:**
- `test_load_custom_config()` - Validates mapping of JSON fields to the `RepoRunnerConfig` schema.
**Dependencies:** `src.core.config_loader`

### `tests/unit/test_context_slicer.py`
**Role:** Validates the graph traversal logic and token budgeting used to prune context for LLMs.
**Key Exports:**
- `test_radius_logic_standard()` - Confirms that BFS expansion stops at the correct number of hops.
- `test_token_budget_enforcement()` - Ensures files are excluded if they exceed the remaining token budget.
- `test_symbol_focus_resolution()` - Validates the translation of symbolic names (classes/functions) to file IDs.
**Dependencies:** `src.analysis.context_slicer`, `src.core.types`

### `tests/unit/test_file_fingerprint.py`
**Role:** Tests SHA256 hashing and language identification based on file extensions.
**Key Exports:**
- `test_valid_file()` - Confirms hash accuracy and metadata extraction.
**Dependencies:** `src.fingerprint.file_fingerprint`

### `tests/unit/test_filesystem_scanner.py`
**Role:** Validates directory traversal, including depth limits and permission error handling.
**Key Exports:**
- `test_scanner_ignores()` - Ensures restricted directories (like `.git`) are never traversed.
**Dependencies:** `src.scanner.filesystem_scanner`

### `tests/unit/test_flatten_exporter.py`
**Role:** Tests the rendering logic for the Markdown exporter, specifically the tree and binary file handling.
**Key Exports:**
- `test_scope_filtering()` - Checks the internal application of path filters on file lists.
**Dependencies:** `src.exporters.flatten_markdown_exporter`

### `tests/unit/test_graph_builder.py`
**Role:** Tests the construction of the dependency graph, including deterministic sorting and cycle detection.
**Key Exports:**
- `test_cycle_detection_triangular()` - Verifies that circular dependencies are correctly identified.
- `test_graph_determinism()` - Ensures graph output is identical regardless of input processing order.
**Dependencies:** `src.analysis.graph_builder`, `src.core.types`

### `tests/unit/test_import_scanner.py`
**Role:** Validates AST (Python) and Regex (JS/TS) scanning for imports and symbol definitions.
**Key Exports:**
- `test_python_scope_and_strings()` - Confirms that strings looking like imports are ignored by the AST parser.
- `test_ts_advanced_imports()` - Validates support for `import type` and dynamic imports in TypeScript.
**Dependencies:** `src.analysis.import_scanner`

### `tests/unit/test_path_normalizer.py`
**Role:** Ensures paths are consistently formatted across platforms and security checks are enforced.
**Key Exports:**
- `test_parent_traversal()` - Confirms that `..` segments are resolved to canonical paths.
- `test_casing_policy()` - Validates that all stored paths are forced to lowercase for cross-OS stability.
**Dependencies:** `src.normalize.path_normalizer`

### `tests/unit/test_snapshot_comparator.py`
**Role:** Validates the identification of added, removed, and modified files and edges between two manifests.
**Key Exports:**
- `test_file_diffing()` - Checks that changes in SHA256 trigger "modified" status.
**Dependencies:** `src.analysis.snapshot_comparator`, `src.core.types`

### `tests/unit/test_structure_builder.py`
**Role:** Tests the mapping of a flat file list into a nested hierarchical JSON structure.
**Key Exports:**
- `test_build_structure()` - Verifies module grouping and path sorting.
**Dependencies:** `src.structure.structure_builder`, `src.core.types`

### `tests/unit/test_token_telemetry.py`
**Role:** Validates the mathematical accuracy of token estimations and cost calculations.
**Key Exports:**
- `test_telemetry_calculations()` - Confirms reduction percentages and cost formatting in the final report.
**Dependencies:** `src.observability.token_telemetry`

### `tests/unit/test_types.py`
**Role:** Ensures Pydantic models enforce schema constraints and automatic path cleaning.
**Key Exports:**
- `test_path_normalization_validator()` - Demonstrates that `FileEntry` objects automatically clean dirty input paths on instantiation.
**Dependencies:** `src.core.types`