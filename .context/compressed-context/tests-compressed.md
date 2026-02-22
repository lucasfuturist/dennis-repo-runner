## High-Resolution Interface Map: repo-runner (Test Suite)

### 1. The Tree
```
└── tests
    ├── __init__.py
    ├── fixtures
    │   ├── repo_20260221_223954 [...]
    │   └── repo_20260221_225829 [...]
    ├── integration
    │   ├── __init__.py
    │   ├── test_api.py
    │   ├── test_export_flow.py
    │   ├── test_full_snapshot.py
    │   ├── test_graph_snapshot.py
    │   ├── test_robustness.py
    │   └── test_snapshot_flow.py
    └── unit
        ├── __init__.py
        ├── test_cli_diff.py
        ├── test_cli_slice.py
        ├── test_config_loader.py
        ├── test_context_slicer.py
        ├── test_filesystem_scanner.py
        ├── test_fingerprint_hardening.py
        ├── test_flatten_exporter.py
        ├── test_graph_builder.py
        ├── test_graph_resolution.py
        ├── test_ignore_logic.py
        ├── test_import_scanner.py
        ├── test_import_scanner_logic.py
        ├── test_normalizer.py
        ├── test_path_normalizer.py
        ├── test_scanner_hardening.py
        ├── test_snapshot_comparator.py
        ├── test_snapshot_loader.py
        ├── test_structure.py
        ├── test_structure_builder.py
        ├── test_token_telemetry.py
        └── test_types.py
```

---

### 2. File Summaries (Integration Suite)

### `tests/integration/test_api.py`
**Role:** Validates the FastAPI REST layer by simulating HTTP lifecycles from snapshot creation to comparison.
**Key Scenarios:**
- `test_full_api_lifecycle` - Verifies snapshot generation, context slicing, and structural diffing via HTTP calls.
- `test_slice_with_token_limit` - Validates that the API correctly enforces `max_tokens` when returning sliced manifests.
**Dependencies:** `src.api.server`, `FastAPI.TestClient`

### `tests/integration/test_export_flow.py`
**Role:** Verifies the end-to-end pipeline of generating Markdown context files from existing snapshots.
**Key Scenarios:**
- `test_export_full_with_tokens` - Ensures token telemetry is correctly injected into the final Markdown header.
- `test_export_scoped` - Validates directory-specific scoping (`module:src/api`) in the final export output.
**Dependencies:** `src.core.controller`

### `tests/integration/test_full_snapshot.py`
**Role:** Ensures the orchestration logic correctly syncs the Scanner, GraphBuilder, and Markdown Exporter.
**Key Scenarios:**
- `test_snapshot_creation_with_graph_and_auto_export` - Validates that all side-effect files (manifest, graph, structure, markdown) are written to disk.
- `test_snapshot_skip_graph` - Verifies the system correctly bypasses analysis when configured.
**Dependencies:** `src.core.controller`, `src.snapshot.snapshot_loader`

### `tests/integration/test_graph_snapshot.py`
**Role:** Validates that generated snapshot artifacts correctly represent file-to-file and file-to-external dependencies.
**Key Scenarios:**
- `test_end_to_end_graph_generation` - Confirms that `main.py` -> `utils.py` edges are accurately serialized in the JSON output.
**Dependencies:** `src.core.controller`

### `tests/integration/test_robustness.py`
**Role:** Tests system stability against complex filesystem edge cases like symlink cycles and mixed file health.
**Key Scenarios:**
- `test_snapshot_with_mixed_health` - Verifies the scanner does not hang on circular symlinks and respects ignore rules.
**Dependencies:** `src.core.controller`

---

### 3. File Summaries (Unit Suite)

### `tests/unit/test_context_slicer.py`
**Role:** Exercises the core "context pruning" logic used to fit repository data into LLM context windows.
**Key Scenarios:**
- `test_token_budget_enforcement` - Validates BFS expansion stops exactly when the token limit is reached.
- `test_symbol_focus_resolution` - Tests resolving semantic queries (`symbol:ClassName`) into physical file focuses.
**Dependencies:** `src.analysis.context_slicer`

### `tests/unit/test_graph_builder.py`
**Role:** Validates the conversion of raw imports into a normalized dependency graph.
**Key Scenarios:**
- `test_scoped_and_deep_external_packages` - Ensures NPM scopes (e.g., `@mui/material`) are preserved while sub-paths are collapsed.
- `test_cycle_detection_*` - Verifies detection and normalization of circular dependencies (A->B->A).
**Dependencies:** `src.analysis.graph_builder`

### `tests/unit/test_import_scanner.py`
**Role:** Deep testing of the AST and Regex parsers for Python and JS/TS.
**Key Scenarios:**
- `test_python_scope_and_strings` - Confirms AST correctly ignores imports inside strings/comments but finds lazy imports in functions.
- `test_js_symbols` - Verifies extraction of Classes and Arrow Functions from modern JS.
**Dependencies:** `src.analysis.import_scanner`

### `tests/unit/test_path_normalizer.py`
**Role:** Ensures the "Stable ID" system is consistent across Windows and Unix.
**Key Scenarios:**
- `test_windows_separator_handling` - Confirms `\` is always converted to `/`.
- `test_casing_policy` - Validates universal lowercase transformation for cross-OS comparison.
**Dependencies:** `src.normalize.path_normalizer`

### `tests/unit/test_snapshot_comparator.py`
**Role:** Validates the logic for calculating structural drift between two snapshots.
**Key Scenarios:**
- `test_file_diffing` - Ensures modified files are detected via SHA256 changes even if paths remain identical.
- `test_graph_diffing` - Verifies the addition/removal of dependency edges is accurately reported.
**Dependencies:** `src.analysis.snapshot_comparator`

### `tests/unit/test_types.py`
**Role:** Confirms Pydantic model validation and automatic path cleaning.
**Key Scenarios:**
- `test_path_normalization_validator` - Proves the `FileEntry` model cleans "dirty" input paths on instantiation.
- `test_stable_id_validation` - Verifies strict ID prefixing (`file:`, `module:`).
**Dependencies:** `src.core.types`

### `tests/unit/test_cli_diff.py` / `test_cli_slice.py`
**Role:** Validates that the ArgParse CLI correctly maps user flags to Controller arguments.
**Dependencies:** `src.cli.main`

### `tests/unit/test_token_telemetry.py`
**Role:** Verifies the accuracy of token count estimations and cost projections.
**Dependencies:** `src.observability.token_telemetry`

### `tests/unit/test_structure_builder.py` / `test_structure.py`
**Role:** Confirms that flat file lists are correctly organized into a tree structure for UI rendering.
**Dependencies:** `src.structure.structure_builder`

### `tests/unit/test_scanner_hardening.py` / `test_filesystem_scanner.py`
**Role:** Validates filesystem traversal, permission error handling, and depth-limit logic.
**Dependencies:** `src.scanner.filesystem_scanner`