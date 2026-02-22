### `repo-runner` High-Resolution Interface Map

## 1. The Tree
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

## 2. File Summaries

### `src/analysis/context_slicer.py`
**Role:** Deterministically prunes repository manifests by performing a bidirectional BFS on the dependency graph to isolate context for LLMs.
**Key Exports:**
- `ContextSlicer.slice_manifest(manifest, graph, focus_id, radius): Dict` - Filters a manifest to include only files within a specific N-degree radius of a target file.
**Dependencies:** `src.core.types`

### `src/analysis/graph_builder.py`
**Role:** Constructs a directed dependency graph by resolving raw import strings into stable file identifiers.
**Key Exports:**
- `GraphBuilder.build(files): GraphStructure` - Converts a list of file entries into a node-edge graph of internal and external dependencies.
**Dependencies:** `src.core.types`

### `src/analysis/import_scanner.py`
**Role:** Extracts import statements from source code using AST parsing for Python and hardened Regex heuristics for JavaScript/TypeScript.
**Key Exports:**
- `ImportScanner.scan(path, language): List[str]` - Returns a sorted list of unique import targets found within a file.
**Dependencies:** None (Standard Library)

### `src/analysis/snapshot_comparator.py`
**Role:** Identifies structural drift and content changes between two repository snapshots.
**Key Exports:**
- `SnapshotComparator.compare(manifest_a, manifest_b, graph_a, graph_b): SnapshotDiffReport` - Generates a diff identifying added, removed, or modified files and dependency edges.
**Dependencies:** `src.core.types`

### `src/api/server.py`
**Role:** Exposes the core snapshotting and slicing logic via a FastAPI REST interface for remote context ingestion.
**Key Exports:**
- `create_snapshot(req): dict` - API endpoint to trigger a full repository scan.
- `slice_snapshot(snapshot_id, req): dict` - API endpoint to generate compressed context with token telemetry.
- `compare_snapshots(req): SnapshotDiffReport` - API endpoint to calculate structural differences.
**Dependencies:** `src.core.controller`, `src.snapshot.snapshot_loader`, `src.analysis.context_slicer`, `src.analysis.snapshot_comparator`, `src.observability.token_telemetry`

### `src/cli/main.py`
**Role:** Provides a command-line interface for manual snapshot creation, artifact exporting, and launching the GUI.
**Key Exports:**
- `main()` - Entry point for CLI argument parsing and execution flow.
**Dependencies:** `src.core.controller`, `src.gui.app`

### `src/core/controller.py`
**Role:** The primary orchestrator that coordinates scanning, fingerprinting, normalization, and snapshot writing.
**Key Exports:**
- `run_snapshot(...): str` - Executes the full pipeline to create a deterministic structural snapshot and returns its ID.
- `run_export_flatten(...): str` - Loads a snapshot and renders it into a Markdown file with optional context slicing.
**Dependencies:** `src.analysis.import_scanner`, `src.analysis.graph_builder`, `src.fingerprint.file_fingerprint`, `src.normalize.path_normalizer`, `src.scanner.filesystem_scanner`, `src.snapshot.snapshot_writer`, `src.exporters.flatten_markdown_exporter`

### `src/core/types.py`
**Role:** Defines the Pydantic data models used for system-wide type safety and JSON serialization.
**Key Exports:**
- `FileEntry` - Model representing a file's state (SHA256, stable_id, imports).
- `Manifest` - The root model for a repository snapshot, including config, stats, and files.
- `SnapshotDiffReport` - Model representing the result of a comparison between two snapshots.
**Dependencies:** `pydantic`

### `src/entry_point.py`
**Role:** Handles high-level initialization, including High-DPI Windows settings, and routes to CLI or GUI based on arguments.
**Key Exports:**
- `launch()` - Determines if the application should start in terminal or graphical mode.
**Dependencies:** `src.cli.main`, `src.gui.app`

### `src/exporters/flatten_markdown_exporter.py`
**Role:** Renders repository snapshots into a single Markdown document tailored for LLM context windows.
**Key Exports:**
- `FlattenMarkdownExporter.export(...): str` - Writes the tree structure and file contents to a `.md` file.
- `FlattenOptions` - Configuration state for export scope (full, module, or specific list).
**Dependencies:** None (Standard Library)

### `src/fingerprint/file_fingerprint.py`
**Role:** Performs low-level file analysis to determine cryptographic hashes and programming language mapping.
**Key Exports:**
- `FileFingerprint.fingerprint(path): Dict` - Computes SHA256 and identifies language based on file extension.
**Dependencies:** None (Standard Library)

### `src/gui/app.py`
**Role:** Orchestrates the Tkinter-based graphical user interface, managing thread workers for non-blocking UI scans.
**Key Exports:**
- `RepoRunnerApp` - Main window class managing UI state and event routing.
- `run_gui()` - Initializes and starts the Tkinter main loop.
**Dependencies:** `src.scanner.filesystem_scanner`, `src.core.controller`, `src.gui.components.*`

### `src/normalize/path_normalizer.py`
**Role:** Enforces platform-agnostic pathing and security boundaries to prevent directory traversal.
**Key Exports:**
- `PathNormalizer.normalize(absolute_path): str` - Converts absolute paths to lowercase, forward-slash, repo-relative strings.
- `PathNormalizer.file_id(normalized_path): str` - Generates a stable identifier prefixed with `file:`.
**Dependencies:** None (Standard Library)

### `src/observability/token_telemetry.py`
**Role:** Calculates and formats heuristics regarding context window usage and estimated LLM input costs.
**Key Exports:**
- `TokenTelemetry.calculate_telemetry(...): str` - Returns a Markdown formatted block of token counts and cost estimates.
**Dependencies:** None (Standard Library)

### `src/scanner/filesystem_scanner.py`
**Role:** Recursively walks the local filesystem to identify relevant files while respecting depth and ignore constraints.
**Key Exports:**
- `FileSystemScanner.scan(root_paths, progress_callback): List[str]` - Performs the walk and returns absolute paths to discovered files.
**Dependencies:** None (Standard Library)

### `src/snapshot/snapshot_loader.py`
**Role:** Utility for resolving and loading serialized snapshot manifests and structures from the output directory.
**Key Exports:**
- `SnapshotLoader.resolve_snapshot_dir(snapshot_id): str` - Locates a specific snapshot or defaults to the "current" pointer.
**Dependencies:** None (Standard Library)

### `src/snapshot/snapshot_writer.py`
**Role:** Serializes internal data models to disk in a timestamped snapshot directory.
**Key Exports:**
- `SnapshotWriter.write(manifest, structure, graph, write_current_pointer): str` - Persists JSON artifacts and optionally updates the `current.json` link.
**Dependencies:** `src.core.types`

### `src/structure/structure_builder.py`
**Role:** Organizes flat file lists into a hierarchical module-based structure for the repository manifest.
**Key Exports:**
- `StructureBuilder.build(repo_id, files): Dict` - Groups files by their directory paths into a "repo" modules schema.
**Dependencies:** `src.core.types`