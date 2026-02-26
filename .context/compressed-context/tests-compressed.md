# High-Resolution Interface Map: `repo-runner` (Tests)

## 1. The Tree

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
        ├── test_drawio_exporter.py
        ├── test_file_fingerprint.py
        ├── test_filesystem_scanner.py
        ├── test_flatten_exporter.py
        ├── test_graph_builder.py
        ├── test_ignore_logic.py
        ├── test_import_scanner.py
        ├── test_mermaid_exporter.py
        ├── test_path_normalizer.py
        ├── test_snapshot_comparator.py
        ├── test_snapshot_loader.py
        ├── test_structure_builder.py
        ├── test_token_telemetry.py
        └── test_types.py
```

## 2. File Summaries

### `tests/conftest.py`
**Role:** Global Pytest fixtures for creating temporary repository environments and file structures.
**Key Exports:**
- `temp_repo_root()` - Yields a unique, cleaned-up temporary directory path for isolation.
- `create_file(rel_path, content)` - Factory to generate files within the temp repo.
- `simple_repo` / `complex_repo` - Pre-scaffolded repository states for quick testing.
**Dependencies:** `pytest`, `tempfile`, `shutil`

### `tests/integration/test_api.py`
**Role:** Validates the FastAPI server endpoints for snapshot lifecycle, context slicing, and diffing.
**Key Exports:**
- `TestAPI` - Test suite using `TestClient` to verify HTTP responses and JSON payloads.
**Dependencies:** `src.api.server`, `fastapi.testclient`

### `tests/integration/test_cli_diff.py`
**Role:** Verifies that the CLI diff command correctly parses arguments and invokes the controller.
**Key Exports:**
- `TestCLIDiff` - Checks if `src.cli.main` correctly routes flags to `run_compare`.
**Dependencies:** `src.cli.main`, `unittest.mock`

### `tests/integration/test_cli_slice.py`
**Role:** Verifies that the CLI slice command correctly maps arguments (radius, tokens) to the export controller.
**Key Exports:**
- `TestCLISlice` - Checks argument parsing and defaults for `run_export_flatten`.
**Dependencies:** `src.cli.main`, `unittest.mock`

### `tests/integration/test_e2e_snapshot.py`
**Role:** End-to-end verification of the snapshot engine, ensuring files, graphs, and manifests are written to disk.
**Key Exports:**
- `TestFullSnapshot` - Validates directory structure, JSON schema compliance, and auto-export generation.
**Dependencies:** `src.core.controller`, `src.snapshot.snapshot_loader`

### `tests/integration/test_export_flow.py`
**Role:** Tests the Markdown export functionality, including scoping (full vs module) and token stats.
**Key Exports:**
- `TestExportFlow` - Ensures generated Markdown contains expected file contents and exclusions.
**Dependencies:** `src.core.controller`

### `tests/integration/test_graph_snapshot.py`
**Role:** Verifies the dependency graph generation within a full snapshot run.
**Key Exports:**
- `TestGraphSnapshot` - checks that nodes/edges correspond to actual Python imports in the temp repo.
**Dependencies:** `src.core.controller`, `src.snapshot.snapshot_loader`

### `tests/integration/test_robustness.py`
**Role:** Tests system stability against messy inputs like symlink cycles, ignored directories, and mixed file types.
**Key Exports:**
- `TestRobustness` - Ensures the scanner doesn't crash or hang on infinite loops or locked files.
**Dependencies:** `src.core.controller`

### `tests/unit/test_config_loader.py`
**Role:** Unit tests for parsing `repo-runner.json` and handling malformed configuration.
**Key Exports:**
- `TestConfigLoader` - Verifies fallback to defaults on missing or invalid JSON.
**Dependencies:** `src.core.config_loader`

### `tests/unit/test_context_slicer.py`
**Role:** Validates graph traversal logic, including radius limitation, token budgeting, and cycle reporting.
**Key Exports:**
- `TestContextSlicer` - Tests `ContextSlicer.slice_manifest` against mock graph topologies.
**Dependencies:** `src.analysis.context_slicer`

### `tests/unit/test_drawio_exporter.py`
**Role:** Ensures the Draw.io CSV exporter generates valid layout directives and node rows.
**Key Exports:**
- `TestDrawioExporter` - Verifies CSV headers and module swimlane generation.
**Dependencies:** `src.exporters.drawio_exporter`

### `tests/unit/test_file_fingerprint.py`
**Role:** Tests SHA256 calculation and language detection, including error handling for locked files.
**Key Exports:**
- `TestFingerprintHardening` - Verifies hashing accuracy and OS error propagation.
**Dependencies:** `src.fingerprint.file_fingerprint`

### `tests/unit/test_filesystem_scanner.py`
**Role:** Tests the recursive directory walker, ignore rules, and symlink loop detection.
**Key Exports:**
- `TestFileSystemScanner` - Verifies that ignored files are excluded and traversal depth is respected.
**Dependencies:** `src.scanner.filesystem_scanner`

### `tests/unit/test_flatten_exporter.py`
**Role:** Unit tests for the Markdown generation logic, including tree rendering and binary file placeholders.
**Key Exports:**
- `TestFlattenExporter` - Checks filtering logic and string output formatting.
**Dependencies:** `src.exporters.flatten_markdown_exporter`

### `tests/unit/test_graph_builder.py`
**Role:** Tests the construction of graph nodes/edges from file inputs, including cycle detection and import resolution.
**Key Exports:**
- `TestGraphBuilder` - Validates Python/JS import resolution and external node creation.
**Dependencies:** `src.analysis.graph_builder`

### `tests/unit/test_ignore_logic.py`
**Role:** Dedicated tests for checking that specific directory patterns (e.g., `.git`, `dist`) are skipped.
**Key Exports:**
- `TestIgnoreLogic` - Validates scanner behavior against a set of ignore rules.
**Dependencies:** `src.scanner.filesystem_scanner`

### `tests/unit/test_import_scanner.py`
**Role:** Tests the Regex and AST scanners for Python and JavaScript/TypeScript import extraction.
**Key Exports:**
- `TestImportScanner` - Verifies extraction of standard, relative, and dynamic imports.
**Dependencies:** `src.analysis.import_scanner`

### `tests/unit/test_mermaid_exporter.py`
**Role:** Tests generation of Mermaid diagram syntax, including subgraph clustering and cycle styling.
**Key Exports:**
- `TestMermaidExporter` - Checks for correct `graph TD` syntax and node ID escaping.
**Dependencies:** `src.exporters.mermaid_exporter`

### `tests/unit/test_path_normalizer.py`
**Role:** Verifies path normalization rules (lowercasing, forward slashes, root escape prevention).
**Key Exports:**
- `TestPathNormalizer` - Ensures paths are consistent across OS environments.
**Dependencies:** `src.normalize.path_normalizer`

### `tests/unit/test_snapshot_comparator.py`
**Role:** Unit tests for the diff engine, verifying detection of added/removed files and edge drift.
**Key Exports:**
- `TestSnapshotComparator` - Checks logic for comparing two `Manifest` objects.
**Dependencies:** `src.analysis.snapshot_comparator`

### `tests/unit/test_structure_builder.py`
**Role:** Tests the transformation of flat file lists into a nested hierarchical dictionary.
**Key Exports:**
- `TestStructureBuilder` - Verifies module grouping logic.
**Dependencies:** `src.structure.structure_builder`

### `tests/unit/test_token_telemetry.py`
**Role:** Verifies mathematical calculations for token estimation, cost, and compression ratios.
**Key Exports:**
- `TestTokenTelemetry` - Checks formatting of the markdown telemetry summary.
**Dependencies:** `src.observability.token_telemetry`

### `tests/unit/test_types.py`
**Role:** Tests Pydantic data models, specifically custom validators for path normalization and IDs.
**Key Exports:**
- `TestTypes` - Ensures `FileEntry` automatically cleans inputs.
**Dependencies:** `src.core.types`