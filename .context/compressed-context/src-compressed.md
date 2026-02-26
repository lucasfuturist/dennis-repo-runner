# High-Resolution Interface Map: `repo-runner`

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
    │   ├── config_loader.py
    │   ├── controller.py
    │   ├── repo-runner.code-workspace
    │   └── types.py
    ├── entry_point.py
    ├── exporters
    │   ├── drawio_exporter.py
    │   ├── flatten_markdown_exporter.py
    │   └── mermaid_exporter.py
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
**Role:** Deterministically prunes repository manifests based on graph topology to fit LLM context windows.
**Key Exports:**
- `ContextSlicer.slice_manifest(manifest, graph, focus_id, radius, max_tokens): Dict` - Filters manifest to files within N-degree hops of a focus node, respecting token budgets.
**Dependencies:** `TokenTelemetry`

### `src/analysis/graph_builder.py`
**Role:** Constructs a dependency graph from file entries by resolving imports and detecting cycles.
**Key Exports:**
- `GraphBuilder.build(files): GraphStructure` - processing list of files into nodes, edges, and cycles.
**Dependencies:** `FileEntry`, `GraphStructure`, `GraphNode`, `GraphEdge`

### `src/analysis/import_scanner.py`
**Role:** Scans file content (Python, JS, TS) to extract import statements and defined symbols using Regex and AST.
**Key Exports:**
- `ImportScanner.scan(path, language): Dict` - Returns a dictionary containing lists of `imports` and `symbols`.
**Dependencies:** `re`, `ast`

### `src/analysis/snapshot_comparator.py`
**Role:** Deterministic diff engine that compares two snapshots to identify structural drift, file modifications, and edge changes.
**Key Exports:**
- `SnapshotComparator.compare(manifest_a, manifest_b, graph_a, graph_b): SnapshotDiffReport` - Generates a report detailing added/removed/modified files and edges.
**Dependencies:** `Manifest`, `GraphStructure`, `SnapshotDiffReport`

### `src/api/server.py`
**Role:** FastAPI backend providing endpoints to trigger snapshots, context slicing, and comparisons.
**Key Exports:**
- `app` - The FastAPI application instance.
- `create_snapshot(SnapshotRequest): JSON` - Endpoint to trigger repo scanning.
- `slice_snapshot(snapshot_id, SliceRequest): JSON` - Endpoint to generate pruned context.
- `compare_snapshots(CompareRequest): SnapshotDiffReport` - Endpoint to diff two snapshots.
**Dependencies:** `run_snapshot`, `ContextSlicer`, `SnapshotComparator`, `TokenTelemetry`

### `src/cli/main.py`
**Role:** Entry point for the CLI, parsing arguments for snapshotting, slicing, diffing, and diagram generation.
**Key Exports:**
- `main()` - Orchestrates command routing based on `sys.argv`.
- `cli_progress(phase, current, total)` - Renders terminal-based progress updates.
**Dependencies:** `run_snapshot`, `run_compare`, `run_export_flatten`, `run_export_diagram`, `ConfigLoader`

### `src/core/config_loader.py`
**Role:** Loads and validates the `repo-runner.json` project configuration file.
**Key Exports:**
- `ConfigLoader.load_config(repo_root): RepoRunnerConfig` - Returns configuration object, falling back to defaults on error.
**Dependencies:** `RepoRunnerConfig`

### `src/core/controller.py`
**Role:** Central orchestration layer connecting scanning, analysis, graph building, and exporting logic.
**Key Exports:**
- `run_snapshot(...)` - Orchestrates the full scanning, fingerprinting, and writing workflow.
- `run_export_flatten(...)` - Generates a monolithic Markdown export of the repository.
- `run_export_diagram(...)` - Orchestrates visual diagram generation (Mermaid/Draw.io).
- `run_compare(...)` - Loads snapshots and triggers the comparator.
**Dependencies:** `FileSystemScanner`, `GraphBuilder`, `SnapshotWriter`, `ImportScanner`, `FlattenMarkdownExporter`

### `src/core/types.py`
**Role:** Defines Pydantic data models used throughout the system for validation and serialization.
**Key Exports:**
- `RepoRunnerConfig` - Schema for configuration files.
- `FileEntry` - Model for individual file metadata (path, SHA, symbols).
- `GraphStructure` - Model for nodes, edges, and cycles.
- `Manifest` - Root model for the snapshot artifact.
- `SnapshotDiffReport` - Model for diff results.
**Dependencies:** `pydantic`

### `src/entry_point.py`
**Role:** Application bootstrapper that detects environment and launches either the CLI or GUI.
**Key Exports:**
- `launch()` - Determines launch mode based on arguments.
**Dependencies:** `src.cli.main`, `src.gui.app`

### `src/exporters/drawio_exporter.py`
**Role:** Converts the dependency graph into a Draw.io compatible CSV format with auto-layout configuration.
**Key Exports:**
- `DrawioExporter.export(snapshot_dir, graph, ...): str` - Writes the CSV artifact to disk.
**Dependencies:** `GraphStructure`

### `src/exporters/flatten_markdown_exporter.py`
**Role:** Generates a single Markdown file containing the repo tree and file contents.
**Key Exports:**
- `FlattenMarkdownExporter.export(..., options): str` - Orchestrates the export process.
- `FlattenMarkdownExporter.generate_content(...)` - Builds the markdown string in memory.
- `FlattenOptions` - Dataclass for export configuration (scope, tree_only).
**Dependencies:** Standard Lib only.

### `src/exporters/mermaid_exporter.py`
**Role:** Converts the dependency graph into Mermaid.js diagram syntax.
**Key Exports:**
- `MermaidExporter.export(snapshot_dir, graph, ...): str` - Generates `.mmd` file with styling for cycles and modules.
**Dependencies:** `GraphStructure`

### `src/fingerprint/file_fingerprint.py`
**Role:** Computes SHA256 hashes and detects file language based on extension.
**Key Exports:**
- `FileFingerprint.fingerprint(path): Dict` - Returns SHA256, size, and language.
- `LANGUAGE_MAP` - Dictionary mapping extensions to language IDs.
**Dependencies:** `hashlib`

### `src/gui/app.py`
**Role:** Main Tkinter GUI application window handling the event loop and layout orchestration.
**Key Exports:**
- `RepoRunnerApp` - Main `tk.Tk` class.
- `run_gui()` - Initializes and runs the main loop.
**Dependencies:** `FileSystemScanner`, `PathNormalizer`, `ConfigTabs`, `FileTreePanel`, `PreviewPanel`

### `src/gui/components/config_tabs.py`
**Role:** GUI component managing configuration inputs (depth, ignore rules, export settings).
**Key Exports:**
- `ConfigTabs` - `ttk.Notebook` subclass containing configuration controls.
- `depth_var`, `ignore_var`, `ext_var` - Tkinter variables holding config state.
**Dependencies:** `tkinter`

### `src/gui/components/export_preview.py`
**Role:** Modal window for previewing generated Markdown and estimating token counts.
**Key Exports:**
- `ExportPreviewWindow` - `tk.Toplevel` subclass for displaying content and stats.
**Dependencies:** `tkinter`

### `src/gui/components/preview_pane.py`
**Role:** Panel displaying file metadata (imports/symbols) and syntax-highlighted source code.
**Key Exports:**
- `PreviewPanel` - `ttk.Frame` subclass for file visualization.
- `load_file(abs_path, stable_id)` - Triggers on-demand analysis and display.
**Dependencies:** `FileFingerprint`, `ImportScanner`

### `src/gui/components/progress_window.py`
**Role:** Modal dialog showing determinate or indeterminate progress bars.
**Key Exports:**
- `ProgressWindow` - `tk.Toplevel` subclass for blocking progress feedback.
- `update_progress(current, total)` - Updates the bar state.
**Dependencies:** `tkinter`

### `src/gui/components/tree_view.py`
**Role:** Interactive file tree widget with checkboxes for file selection.
**Key Exports:**
- `FileTreePanel` - `ttk.Frame` subclass managing the `Treeview`.
- `get_checked_files(): list` - Returns list of selected file paths.
**Dependencies:** `tkinter`

### `src/normalize/path_normalizer.py`
**Role:** Standardizes file paths (lowercased, forward slashes) relative to the repo root to ensure ID stability.
**Key Exports:**
- `PathNormalizer.normalize(absolute_path): str` - Converts absolute path to relative, normalized string.
- `file_id(path)` / `module_id(path)` / `repo_id()` - Helpers for generating stable IDs.
**Dependencies:** None

### `src/observability/token_telemetry.py`
**Role:** Provides utilities for estimating token usage and costs.
**Key Exports:**
- `TokenTelemetry.estimate_tokens(size_bytes, language): int` - Heuristic token counting.
- `TokenTelemetry.calculate_telemetry(...)` - Generates markdown summary of context reduction and cost.
**Dependencies:** None

### `src/scanner/filesystem_scanner.py`
**Role:** Traverses the filesystem to find files, respecting depth limits and ignore rules.
**Key Exports:**
- `FileSystemScanner.scan(root_paths, progress_callback): List[str]` - Returns sorted list of absolute file paths.
**Dependencies:** `os`

### `src/snapshot/snapshot_loader.py`
**Role:** Resolves snapshot directories and loads JSON artifacts (manifests, graphs).
**Key Exports:**
- `SnapshotLoader.resolve_snapshot_dir(snapshot_id): str` - Finds path, handling "current" alias.
- `SnapshotLoader.load_manifest(dir): dict` - Reads manifest.json.
**Dependencies:** None

### `src/snapshot/snapshot_writer.py`
**Role:** Serializes manifest, structure, and graph objects to JSON files on disk.
**Key Exports:**
- `SnapshotWriter.write(manifest, structure, graph, ...): str` - Writes artifacts and updates `current.json` pointer.
**Dependencies:** `Manifest`, `GraphStructure`

### `src/structure/structure_builder.py`
**Role:** Organizes flat file entries into a hierarchical module structure.
**Key Exports:**
- `StructureBuilder.build(repo_id, files): Dict` - Returns the nested directory structure dictionary.
**Dependencies:** `FileEntry`