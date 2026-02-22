## High-Resolution Interface Map: repo-runner

### 1. The Tree
```
└── src
    ├── __init__.py
    ├── analysis
    │   ├── __init__.py
    │   ├── context_slicer.py
    │   ├── graph_builder.py
    │   ├── import_scanner.py
    │   └── snapshot_comparator.py
    ├── api
    │   ├── init.py
    │   └── server.py
    ├── cli
    │   ├── __init__.py
    │   └── main.py
    ├── core
    │   ├── __init__.py
    │   ├── config_loader.py
    │   ├── controller.py
    │   ├── repo-runner.code-workspace
    │   └── types.py
    ├── entry_point.py
    ├── exporters
    │   └── flatten_markdown_exporter.py
    ├── fingerprint
    │   └── file_fingerprint.py
    ├── gui
    │   ├── __init__.py
    │   ├── app.py
    │   └── components
    │       ├── config_tabs.py
    │       ├── export_preview.py
    │       ├── preview_pane.py
    │       ├── progress_window.py
    │       └── tree_view.py
    ├── normalize
    │   └── path_normalizer.py
    ├── observability
    │   ├── init.py
    │   └── token_telemetry.py
    ├── scanner
    │   └── filesystem_scanner.py
    ├── snapshot
    │   ├── snapshot_loader.py
    │   └── snapshot_writer.py
    └── structure
        └── structure_builder.py
```

---

### 2. File Summaries

### `src/analysis/context_slicer.py`
**Role:** Deterministically prunes repository manifests based on graph topology to fit LLM context windows.
**Key Exports:**
- `ContextSlicer.slice_manifest(manifest, graph, focus_id, radius, max_tokens): Dict` - Filters a manifest to include only files within a specific hop-distance of a target node, respecting token budgets.
**Dependencies:** `src.observability.token_telemetry`

### `src/analysis/graph_builder.py`
**Role:** Constructs a directed dependency graph by resolving file imports into stable internal IDs.
**Key Exports:**
- `GraphBuilder.build(files): GraphStructure` - Transforms a list of file entries into a nodes-and-edges graph including cycle detection.
**Dependencies:** `src.core.types`

### `src/analysis/import_scanner.py`
**Role:** Extracts import statements and defined symbols (classes/functions) from source code using AST (Python) and Regex (JS/TS).
**Key Exports:**
- `ImportScanner.scan(path, language): Dict` - Parses a file to return lists of detected imports and top-level symbols.
**Dependencies:** None (Standard Library)

### `src/analysis/snapshot_comparator.py`
**Role:** Identifies structural and content drift between two repository snapshots.
**Key Exports:**
- `SnapshotComparator.compare(manifest_a, manifest_b, graph_a, graph_b): SnapshotDiffReport` - Diffs file hashes and graph edges to report added, removed, or modified components.
**Dependencies:** `src.core.types`

### `src/api/server.py`
**Role:** Exposes the engine's core functionality via a FastAPI REST interface.
**Key Exports:**
- `create_snapshot(req: SnapshotRequest)` - Endpoint to trigger a new repository scan and fingerprinting.
- `slice_snapshot(snapshot_id, req: SliceRequest)` - Endpoint to retrieve a graph-pruned context window.
- `compare_snapshots(req: CompareRequest)` - Endpoint to calculate the diff between two stored snapshots.
**Dependencies:** `src.core.controller`, `src.snapshot.snapshot_loader`, `src.analysis.context_slicer`, `src.analysis.snapshot_comparator`

### `src/core/config_loader.py`
**Role:** Locates and parses `repo-runner.json` to initialize system-wide defaults.
**Key Exports:**
- `ConfigLoader.load_config(repo_root): RepoRunnerConfig` - Loads project-specific settings or returns defaults if no config is found.
**Dependencies:** `src.core.types`

### `src/core/controller.py`
**Role:** The central orchestrator that coordinates scanning, analysis, and persistence.
**Key Exports:**
- `run_snapshot(...): str` - Executes the full pipeline: scan, fingerprint, graph build, and write to disk.
- `run_export_flatten(...): str` - Generates a Markdown representation of a snapshot or slice.
- `run_compare(...): SnapshotDiffReport` - High-level wrapper for comparing two historical snapshots.
**Dependencies:** `src.scanner`, `src.fingerprint`, `src.analysis`, `src.snapshot`, `src.exporters`

### `src/core/types.py`
**Role:** Defines the Pydantic data models used for system-wide Type Safety and JSON serialization.
**Key Exports:**
- `FileEntry` - Schema for individual file metadata (path, sha256, imports).
- `Manifest` - The root schema for a repository snapshot.
- `GraphStructure` - Schema for the dependency graph and detected cycles.
**Dependencies:** None (Pydantic)

### `src/exporters/flatten_markdown_exporter.py`
**Role:** Consolidates multiple source files into a single structured Markdown document for LLM consumption.
**Key Exports:**
- `FlattenMarkdownExporter.export(repo_root, snapshot_dir, manifest, output_path, options): str` - Writes a formatted Markdown file containing the tree and file contents.
**Dependencies:** `src.exporters` (internal dataclasses)

### `src/fingerprint/file_fingerprint.py`
**Role:** Generates unique identifiers for files based on content and identifies programming languages.
**Key Exports:**
- `FileFingerprint.fingerprint(path): Dict` - Computes SHA256 hashes and determines language based on file extensions.
**Dependencies:** None (Standard Library)

### `src/gui/app.py`
**Role:** Main entry point and state coordinator for the Tkinter-based graphical user interface.
**Key Exports:**
- `RepoRunnerApp` - The primary Window class managing scan threads and component interaction.
**Dependencies:** `src.core.controller`, `src.gui.components.*`

### `src/normalize/path_normalizer.py`
**Role:** Ensures cross-platform path consistency and generates stable identifiers for files and modules.
**Key Exports:**
- `PathNormalizer.normalize(absolute_path): str` - Converts absolute OS paths to lowercase, forward-slash, repo-relative paths.
- `PathNormalizer.file_id(normalized_path): str` - Prefixes a path with `file:` to create a system-wide unique ID.
**Dependencies:** None (Standard Library)

### `src/observability/token_telemetry.py`
**Role:** Provides heuristics for calculating LLM context usage based on file sizes.
**Key Exports:**
- `TokenTelemetry.estimate_tokens(size_bytes): int` - Estimates token count using a character-to-token ratio (default 4:1).
**Dependencies:** None

### `src/scanner/filesystem_scanner.py`
**Role:** Recursively traverses the physical filesystem to identify candidate files while respecting ignore rules.
**Key Exports:**
- `FileSystemScanner.scan(root_paths, progress_callback): List[str]` - Returns a list of absolute paths found within depth and exclusion constraints.
**Dependencies:** None (Standard Library)

### `src/snapshot/snapshot_loader.py`
**Role:** Resolves snapshot directory paths and handles "current" alias logic.
**Key Exports:**
- `SnapshotLoader.resolve_snapshot_dir(snapshot_id): str` - Translates a snapshot ID or the "current" keyword into a physical disk path.
**Dependencies:** None (Standard Library)

### `src/snapshot/snapshot_writer.py`
**Role:** Persists snapshot artifacts (Manifest, Structure, Graph) to disk in a timestamped directory.
**Key Exports:**
- `SnapshotWriter.write(manifest, structure, graph, write_current_pointer): str` - Serializes snapshot data and updates the `current.json` pointer.
**Dependencies:** `src.core.types`

### `src/structure/structure_builder.py`
**Role:** Organizes flat file lists into a hierarchical module/file relationship for UI tree rendering.
**Key Exports:**
- `StructureBuilder.build(repo_id, files): Dict` - Maps file entries to their parent modules/directories.
**Dependencies:** `src.core.types`

---
*Note: No dedicated test files (`.test.py`, `test_*.py`) were detected in the provided source scan. All core logic files have been documented.*