## 1. The Tree

```
└── tests
    ├── __init__.py
    ├── integration
    │   ├── __init__.py
    │   ├── test_full_snapshot.py
    │   ├── test_robustness.py
    │   └── test_snapshot_flow.py
    ├── output
    │   ├── 2026-02-18t21-09-34z
    │   │   ├── graph.json
    │   │   ├── manifest.json
    │   │   └── structure.json
    │   └── current.json
    └── unit
        ├── __init__.py
        ├── test_filesystem_scanner.py
        ├── test_fingerprint_hardening.py
        ├── test_flatten_exporter.py
        ├── test_graph_builder.py
        ├── test_ignore_logic.py
        ├── test_import_scanner.py
        ├── test_normalizer.p
        ├── test_path_normalizer.py
        ├── test_scanner_hardening.py
        ├── test_structure.py
        └── test_structure_builder.py
```

## 2. File Summaries

### `tests/integration/test_full_snapshot.py`
**Role:** Validates the end-to-end pipeline from filesystem scan to serialized snapshot artifacts.
**Key Tests:**
- `test_snapshot_creation()` - Verifies that the generated manifest contains correct config, file lists, and accurately detected external dependencies (e.g., `os`).
**Dependencies:** `src.cli.main.run_snapshot`, `src.snapshot.snapshot_loader`.

### `tests/integration/test_robustness.py`
**Role:** Tests the system's resilience against complex filesystem scenarios like symlink cycles and mixed file health.
**Key Tests:**
- `test_snapshot_with_mixed_health()` - Confirms the scanner breaks symlink loops and correctly excludes items inside `node_modules`.
**Dependencies:** `src.core.controller.run_snapshot`.

### `tests/integration/test_snapshot_flow.py`
**Role:** Verifies the standard operational flow and directory structure creation for new snapshots.
**Key Tests:**
- `test_snapshot_creation()` - Ensures `manifest.json` is physically written and contains the expected relative paths.
**Dependencies:** `src.cli.main.run_snapshot`.

### `tests/unit/test_filesystem_scanner.py`
**Role:** Validates the directory traversal logic and ignore rule enforcement.
**Key Tests:**
- `test_scanner_ignores()` - Asserts that specified directories (e.g., `.git`, `dist`) are strictly excluded from the scan results.
**Dependencies:** `src.scanner.filesystem_scanner`.

### `tests/unit/test_fingerprint_hardening.py`
**Role:** Ensures file metadata and hashing logic handle various file states correctly.
**Key Tests:**
- `test_valid_file()` - Verifies SHA256 and size calculations.
- `test_locked_or_missing_file()` - Asserts that `OSError` is raised when files are inaccessible.
**Dependencies:** `src.fingerprint.file_fingerprint`.

### `tests/unit/test_flatten_exporter.py`
**Role:** Validates the projection of snapshot data into markdown format.
**Key Tests:**
- `test_tree_generation()` - Confirms the rendered markdown contains a valid ASCII tree.
- `test_scope_filtering()` - Ensures that `module:` or `prefix:` scopes correctly filter the file list.
**Dependencies:** `src.exporters.flatten_markdown_exporter`.

### `tests/unit/test_graph_builder.py`
**Role:** Tests the logical resolution of import strings into a dependency graph.
**Key Tests:**
- `test_node_generation()` - Verifies that internal files and external packages (including scoped npm packages) are identified as nodes.
- `test_edge_resolution_python()` - Validates mapping of Python dots to filesystem paths.
**Dependencies:** `src.analysis.graph_builder`.

### `tests/unit/test_ignore_logic.py`
**Role:** Dedicated verification of name-based exclusion during scanning.
**Key Tests:**
- `test_scanner_ignores()` - Confirms internal paths are kept while ignored roots are discarded.
**Dependencies:** `src.scanner.filesystem_scanner`.

### `tests/unit/test_import_scanner.py`
**Role:** Validates the static analysis logic for both Python (AST) and JS/TS (Regex).
**Key Tests:**
- `test_python_complex_structure()` - Checks parenthesized and aliased imports.
- `test_js_edge_cases()` - Ensures side-effect imports and multi-line imports are captured while comments are stripped.
**Dependencies:** `src.analysis.import_scanner`.

### `tests/unit/test_path_normalizer.py`
**Role:** Ensures deterministic path strings across different operating systems.
**Key Tests:**
- `test_windows_separator_handling()` - Confirms backslashes are converted to forward slashes and lowercased.
- `test_id_generation()` - Validates the `file:`, `module:`, and `repo:` ID prefixes.
**Dependencies:** `src.normalize.path_normalizer`.

### `tests/unit/test_scanner_hardening.py`
**Role:** Tests error handling and edge cases within the filesystem scanner.
**Key Tests:**
- `test_symlink_cycle_detection()` - Verifies the scanner does not enter infinite recursion.
- `test_permission_error_handling()` - Ensures the scanner skips inaccessible directories gracefully.
**Dependencies:** `src.scanner.filesystem_scanner`.

### `tests/unit/test_structure_builder.py` (and `test_structure.py`)
**Role:** Validates the transformation of a flat file list into the hierarchical module JSON model.
**Key Tests:**
- `test_build_structure()` - Asserts that files are grouped into the correct module paths and sorted lexicographically.
**Dependencies:** `src.structure.structure_builder`.

### `tests/output/` (Artifact Samples)
**Role:** Contains "Golden" snapshot samples used to verify output schema stability.
**Key Data:**
- `manifest.json` - Sample snapshot metadata including hashes and detected imports.
- `structure.json` - Sample hierarchical containment model.
- `graph.json` - Sample node/edge dependency representation.