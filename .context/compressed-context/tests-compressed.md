## High-Resolution Interface Map: repo-runner (Test Suite)

### 1. The Tree
```
└── tests
    ├── __init__.py
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

### 2. File Summaries

#### `tests/integration/test_api.py`
**Role:** Validates the end-to-end REST API lifecycle from snapshot creation to context slicing and comparison.
**Key Exports:**
- `test_full_api_lifecycle()` - Verifies the flow of creating snapshots, slicing a focus file, and comparing versions.
- `test_slice_with_token_limit()` - Ensures the API correctly prunes context when a `max_tokens` budget is provided.
**Dependencies:** `src.api.server`

#### `tests/integration/test_export_flow.py`
**Role:** Tests the generation of flattened Markdown artifacts through the core controller.
**Key Exports:**
- `test_export_full_with_tokens()` - Verifies that exported Markdown contains telemetry and file contents.
- `test_export_scoped()` - Ensures that exports can be restricted to specific sub-modules.
**Dependencies:** `src.core.controller`

#### `tests/integration/test_full_snapshot.py`
**Role:** Confirms that the snapshot engine correctly produces manifests, graphs, and auto-exports.
**Key Exports:**
- `test_snapshot_creation_with_graph_and_auto_export()` - Validates the integrity of all generated snapshot artifacts.
- `test_snapshot_skip_graph()` - Verifies the system's behavior when dependency graph generation is disabled.
**Dependencies:** `src.core.controller`, `src.snapshot.snapshot_loader`

#### `tests/integration/test_graph_snapshot.py`
**Role:** Verifies the accuracy of dependency graph extraction and external dependency identification.
**Key Exports:**
- `test_end_to_end_graph_generation()` - Confirms that internal file imports and external library nodes are mapped correctly.
**Dependencies:** `src.core.controller`

#### `tests/integration/test_robustness.py`
**Role:** Tests system resilience against complex filesystem scenarios like symlink cycles and mixed health.
**Key Exports:**
- `test_snapshot_with_mixed_health()` - Ensures the scanner skips ignored directories and handles symlink loops without hanging.
**Dependencies:** `src.core.controller`

#### `tests/unit/test_context_slicer.py`
**Role:** Validates the deterministic BFS logic for graph-based manifest pruning.
**Key Exports:**
- `test_radius_logic_standard()` - Checks hop-distance filtering.
- `test_token_budget_enforcement()` - Verifies the engine stops expanding context once token limits are reached.
- `test_symbol_focus_resolution()` - Tests resolving a context slice from a symbol name to its parent file.
**Dependencies:** `src.analysis.context_slicer`

#### `tests/unit/test_graph_builder.py`
**Role:** Tests the construction of dependency graphs, including edge normalization and cycle detection.
**Key Exports:**
- `test_scoped_and_deep_external_packages()` - Ensures deep library imports are collapsed to root package names.
- `test_cycle_detection_*()` - Verifies detection of self-loops, simple cycles, and complex triangular dependencies.
**Dependencies:** `src.analysis.graph_builder`

#### `tests/unit/test_import_scanner.py`
**Role:** Comprehensive testing of AST and Regex-based import/symbol extraction logic for Python and JS.
**Key Exports:**
- `test_python_complex_structure()` - Validates AST extraction of multi-line and aliased Python imports.
- `test_js_edge_cases()` - Ensures side-effect imports and multi-line JS imports are captured.
- `test_*_symbols()` - Verifies extraction of classes, functions, and async methods across languages.
**Dependencies:** `src.analysis.import_scanner`

#### `tests/unit/test_path_normalizer.py`
**Role:** Ensures path stability and casing policies across different operating systems.
**Key Exports:**
- `test_messy_path_normalization()` - Confirms redundant slashes and dots are resolved.
- `test_windows_separator_handling()` - Validates that backslashes are converted to forward slashes.
**Dependencies:** `src.normalize.path_normalizer`

#### `tests/unit/test_snapshot_comparator.py`
**Role:** Tests the structural diffing engine for files and dependency edges.
**Key Exports:**
- `test_file_diffing()` - Verifies detection of status changes (added/removed/modified) via SHA256.
- `test_graph_diffing()` - Ensures added or removed dependency relationships are identified.
**Dependencies:** `src.analysis.snapshot_comparator`

#### `tests/unit/test_token_telemetry.py`
**Role:** Validates the accuracy of token estimation and cost calculation heuristics.
**Key Exports:**
- `test_telemetry_calculations()` - Confirms reduction percentages and cost estimates match expected mathematical models.
**Dependencies:** `src.observability.token_telemetry`

#### `tests/unit/test_types.py`
**Role:** Proves that Pydantic models enforce path normalization and stable ID schemas at the data level.
**Key Exports:**
- `test_path_normalization_validator()` - Shows the `FileEntry` model automatically cleans dirty input paths.
- `test_stable_id_validation()` - Ensures only valid URN-style identifiers are permitted.
**Dependencies:** `src.core.types`