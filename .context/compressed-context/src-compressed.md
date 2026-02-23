## High-Resolution Interface Map: repo-runner

### Tree
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

### File Summaries

### `src/analysis/context_slicer.py`
**Role:** Deterministically prunes a repository manifest to isolate a specific file and its dependencies within a token budget.
**Key Exports:**
- `ContextSlicer.slice_manifest(manifest, graph, focus_id, radius, max_tokens): Dict` - Performs a BFS on the dependency graph to return a subset of the manifest centered on a target file.
**Dependencies:** `src.observability.token_telemetry`

### `src/analysis/graph_builder.py`
**Role:** Transforms a list of file entries into a directed dependency graph with cycle detection.
**Key Exports:**
- `GraphBuilder.build(files: List[FileEntry]): GraphStructure` - Orchestrates import resolution, node creation, and deterministic cycle detection.
**Dependencies:** `src.core.types`

### `src/analysis/import_scanner.py`
**Role:** Extracts import statements and defined symbols (classes/functions) from Python and JavaScript/TypeScript source code.
**Key Exports:**
- `ImportScanner.scan(path, language): Dict` - Uses AST (Python) and Regex (JS/TS) to identify external and internal dependencies.
**Dependencies:** None (Standard Library)

### `src/analysis/snapshot_comparator.py`
**Role:** Calculates the structural and content drift between two repository snapshots.
**Key Exports:**
- `SnapshotComparator.compare(manifest_a, manifest_b, graph_a, graph_b): SnapshotDiffReport` - Identifies added, removed, or modified files (via SHA256) and dependency edge changes.
**Dependencies:** `src.core.types`

### `src/api/server.py`
**Role:** Provides a FastAPI web interface for triggering snapshots, slicing context, and comparing snapshots via HTTP.
**Key Exports:**
- `create_snapshot(req: SnapshotRequest)` - Endpoint to run the full ingestion pipeline on a target directory.
- `slice_snapshot(snapshot_id, req: SliceRequest)` - Endpoint to retrieve a compressed LLM context manifest.
- `compare_snapshots(req: CompareRequest)` - Endpoint to retrieve a diff report between two IDs.
**Dependencies:** `src.core.controller`, `src.snapshot.snapshot_loader`, `src.analysis.context_slicer`

### `src/cli/main.py`
**Role:** Command-line entry point for executing snapshots, diffs, and context exports.
**Key Exports:**
- `main()` - Orchestrates CLI argument parsing and maps commands to controller functions.
**Dependencies:** `src.core.controller`, `src.core.config_loader`

### `src/core/config_loader.py`
**Role:** Locates and parses `repo-runner.json` to establish project-specific defaults.
**Key Exports:**
- `ConfigLoader.load_config(repo_root): RepoRunnerConfig` - Returns a validated configuration object from a local JSON file or defaults.
**Dependencies:** `src.core.types`

### `src/core/controller.py`
**Role:** The primary orchestrator that connects the scanner, analyzer, and writer to execute system operations.
**Key Exports:**
- `run_snapshot(...) -> str` - Executes the full pipeline: scan, fingerprint, analyze, and write.
- `run_export_flatten(...) -> str` - Handles the generation of Markdown context files, including slicing logic.
- `run_compare(...) -> SnapshotDiffReport` - High-level wrapper for diffing two stored snapshots.
**Dependencies:** `src.scanner`, `src.analysis`, `src.snapshot`, `src.exporters`, `src.fingerprint`

### `src/core/types.py`
**Role:** Centralized Pydantic model definitions for system-wide data structures and validation.
**Key Exports:**
- `FileEntry` - Schema for individual file metadata including SHA256 and symbols.
- `Manifest` - The root schema for a complete repository snapshot.
- `GraphStructure` - Schema for nodes, edges, and detected cycles.
- `SnapshotDiffReport` - Schema for structural comparisons.
**Dependencies:** None

### `src/entry_point.py`
**Role:** Main execution hook for the application, handling platform-specific DPI scaling and mode switching (CLI vs GUI).
**Key Exports:**
- `launch()` - Determines whether to start the Tkinter GUI or the Argparse CLI based on sys.argv.
**Dependencies:** `src.cli.main`, `src.gui.app`

### `src/exporters/flatten_markdown_exporter.py`
**Role:** Converts repository snapshots into a single, LLM-friendly Markdown document.
**Key Exports:**
- `FlattenMarkdownExporter.export(...) -> str` - Renders the file tree and source code blocks into a formatted text file.
- `FlattenOptions` - Data class defining export scope (full, module, or file list).
**Dependencies:** None

### `src/fingerprint/file_fingerprint.py`
**Role:** Generates unique identity markers for files based on content and extension.
**Key Exports:**
- `FileFingerprint.fingerprint(path): Dict` - Computes SHA256 hashes and maps extensions to programming languages.
**Dependencies:** None

### `src/gui/app.py`
**Role:** Main Tkinter application class managing the visual control panel and background worker threads.
**Key Exports:**
- `RepoRunnerApp` - Coordinates UI updates, file scanning progress, and snapshot triggers.
**Dependencies:** `src.gui.components`, `src.core.controller`, `src.scanner.filesystem_scanner`

### `src/gui/components/tree_view.py`
**Role:** Interactive file explorer with checkbox-based selection for selective snapshotting.
**Key Exports:**
- `FileTreePanel` - Managed widget for visualizing directory structures and capturing user file selections.
**Dependencies:** None

### `src/normalize/path_normalizer.py`
**Role:** Ensures consistent path formatting and security across different Operating Systems.
**Key Exports:**
- `PathNormalizer.normalize(absolute_path): str` - Converts paths to lowercase, forward-slash-delimited strings relative to the repo root.
**Dependencies:** None

### `src/observability/token_telemetry.py`
**Role:** Estimates and tracks LLM token usage and associated costs for context slices.
**Key Exports:**
- `TokenTelemetry.estimate_tokens(size_bytes, language): int` - Heuristic-based token counting for code and text.
- `TokenTelemetry.calculate_telemetry(...) -> str` - Generates a markdown summary of context reduction and pricing.
**Dependencies:** None

### `src/scanner/filesystem_scanner.py`
**Role:** High-performance recursive directory crawler with depth limiting and ignore-list support.
**Key Exports:**
- `FileSystemScanner.scan(root_paths, progress_callback): List[str]` - Returns a list of absolute paths while respecting symlink cycle detection and depth constraints.
**Dependencies:** None

### `src/snapshot/snapshot_loader.py`
**Role:** Handles retrieval of historical snapshot data from the output storage directory.
**Key Exports:**
- `SnapshotLoader.resolve_snapshot_dir(snapshot_id): str` - Resolves "current" alias or specific IDs to physical disk paths.
**Dependencies:** None

### `src/snapshot/snapshot_writer.py`
**Role:** Persists manifests, graphs, and structure data to disk as JSON artifacts.
**Key Exports:**
- `SnapshotWriter.write(...) -> str` - Atomically saves snapshot components and updates the "current" pointer.
**Dependencies:** `src.core.types`

### `src/structure/structure_builder.py`
**Role:** Maps a flat list of file entries into a logical module-based hierarchy.
**Key Exports:**
- `StructureBuilder.build(repo_id, files): Dict` - Groups files by their parent directories for tree visualization.
**Dependencies:** `src.core.types`