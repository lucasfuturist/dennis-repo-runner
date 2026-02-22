### **"High-Resolution Interface Map" - `repo-runner` Tests Module**

---

### **The Tree**
```
└── tests
    ├── __init__.py
    ├── integration
    │   ├── __init__.py
    │   ├── test_full_snapshot.py
    │   ├── test_robustness.py
    │   └── test_snapshot_flow.py
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

---

### **File Summaries**

### `tests/integration/test_full_snapshot.py`
**Role:** Validates the end-to-end snapshot lifecycle from CLI execution to manifest/structure verification.
**Key Exports:**
- `test_snapshot_creation()` - Asserts that running the snapshot CLI produces a valid manifest with correct file paths, external dependencies, and hashes.
**Dependencies:** `src.cli.main`, `src.snapshot.snapshot_loader`

### `tests/integration/test_robustness.py`
**Role:** Tests system resilience against complex filesystem scenarios like symlink cycles and mixed file health.
**Key Exports:**
- `test_snapshot_with_mixed_health()` - Verifies the controller can successfully complete a scan when encountering infinite directory loops and ignored folders.
**Dependencies:** `src.core.controller`, `src.snapshot.snapshot_loader`

### `tests/integration/test_snapshot_flow.py`
**Role:** Standard integration test for the basic snapshot generation and loading workflow.
**Key Exports:**
- `test_snapshot_creation()` - Validates that the core runner generates a valid output directory containing expected manifest entries.
**Dependencies:** `src.cli.main`, `src.snapshot.snapshot_loader`

### `tests/unit/test_filesystem_scanner.py`
**Role:** Unit tests for the directory traversal engine and ignore-pattern matching logic.
**Key Exports:**
- `test_scanner_ignores()` - Confirms the scanner correctly excludes specified directory names during recursion.
**Dependencies:** `src.scanner.filesystem_scanner`

### `tests/unit/test_fingerprint_hardening.py`
**Role:** Unit tests for the file hashing and metadata extraction utility.
**Key Exports:**
- `test_valid_file()` - Validates SHA256 calculation and size extraction.
- `test_empty_file()` - Checks handling of 0-byte files.
- `test_locked_or_missing_file()` - Ensures appropriate OS exceptions are raised for inaccessible paths.
**Dependencies:** `src.fingerprint.file_fingerprint`

### `tests/unit/test_flatten_exporter.py`
**Role:** Unit tests for generating flattened Markdown representations of repository snapshots.
**Key Exports:**
- `test_tree_generation()` - Validates the recursive rendering of the directory tree into Markdown strings.
- `test_scope_filtering()` - Ensures specific module scopes can be isolated in the export.
- `test_binary_placeholder()` - Checks formatting of entries for non-text or skipped files.
**Dependencies:** `src.exporters.flatten_markdown_exporter`

### `tests/unit/test_graph_builder.py`
**Role:** Unit tests for the dependency graph construction engine, focusing on node resolution and edge mapping.
**Key Exports:**
- `test_node_generation()` - Validates identification of internal files versus collapsed external packages.
- `test_edge_resolution_python()` - Verifies AST-derived import links between Python nodes.
- `test_edge_resolution_js()` - Verifies Regex-derived import links for JavaScript/TypeScript.
**Dependencies:** `src.analysis.graph_builder`, `src.core.types`

### `tests/unit/test_ignore_logic.py`
**Role:** Specific unit verification of the `FileSystemScanner`'s ability to filter the filesystem.
**Key Exports:**
- `test_scanner_ignores()` - Asserts that restricted paths (e.g., `.git`, `dist`) are absent from scan results.
**Dependencies:** `src.scanner.filesystem_scanner`

### `tests/unit/test_import_scanner.py`
**Role:** Unit tests for the multi-language import extraction logic using AST (Python) and Regex (JS/TS).
**Key Exports:**
- `test_python_*()` - Validates parsing of relative imports, aliasing, and scope isolation in Python.
- `test_js_*() / test_ts_*()` - Validates parsing of ES6 imports, CommonJS requires, and TypeScript type-only imports.
**Dependencies:** `src.analysis.import_scanner`

### `tests/unit/test_path_normalizer.py`
**Role:** Unit tests for the path canonicalization and ID generation utility.
**Key Exports:**
- `test_basic_normalization()` - Checks conversion of absolute paths to relative, forward-slash formats.
- `test_id_generation()` - Validates the creation of stable prefix-based IDs (e.g., `file:`, `module:`).
**Dependencies:** `src.normalize.path_normalizer`

### `tests/unit/test_scanner_hardening.py`
**Role:** Unit tests for handling OS-level edge cases during filesystem scanning.
**Key Exports:**
- `test_symlink_cycle_detection()` - Confirms the scanner breaks infinite loops.
- `test_permission_error_handling()` - Ensures the scanner skips inaccessible directories without crashing.
**Dependencies:** `src.scanner.filesystem_scanner`

### `tests/unit/test_structure.py` & `test_structure_builder.py`
**Role:** Unit tests for the hierarchical module builder that organizes flat file lists into a tree schema.
**Key Exports:**
- `test_build_structure()` - Validates the transformation of `FileEntry` objects into a `structure.json` compliant hierarchy.
**Dependencies:** `src.structure.structure_builder`, `src.normalize.path_normalizer`