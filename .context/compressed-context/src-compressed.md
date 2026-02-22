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

### 2. File Summaries

#### `src/analysis/context_slicer.py`
**Role:** Deterministically prunes repository manifests based on graph distance from a focus file and token budgets.
**Key Exports:**
- `slice_manifest(manifest, graph, focus_id, radius, max_tokens): Dict` - Filters the manifest to include only files within a specific hop-radius of the focus file while respecting token limits.
**Dependencies:** `src.observability.token_telemetry`

#### `src/analysis/graph_builder.py`
**Role:** Constructs a directed dependency graph by resolving import statements to stable file IDs.
**Key Exports:**
- `build(files: List[FileEntry]): GraphStructure` - Orchestrates the conversion of file entries into a node-edge graph including cycle detection.
- `_detect_cycles(adj, nodes): List[List[str]]` - Identifies circular dependencies within the graph using depth-first search.
**Dependencies:** `src.core.types`

#### `src/analysis/import_scanner.py`
**Role:** Performs regex and AST-based scanning to extract import statements and defined symbols from source code.
**Key Exports:**
- `scan(path, language): Dict[str, List[str]]` - Dispatches scanning logic based on file extension to extract imports and class/function names.
**Dependencies:** Python `ast` module, `re`

#### `src/analysis/snapshot_comparator.py`
**Role:** Compares two repository snapshots to identify structural drift and file modifications.
**Key Exports:**
- `compare(manifest_a, manifest_b, graph_a, graph_b): SnapshotDiffReport` - Calculates the delta of added, removed, and modified files and dependency edges between two snapshots.
**Dependencies:** `src.core.types`

#### `src/api/server.py`
**Role:** Exposes a FastAPI REST interface for triggering snapshots, context slicing, and comparisons.
**Key Exports:**
- `app` - The FastAPI application instance serving the context engine.
- `create_snapshot(req: SnapshotRequest)` - Endpoint to trigger a new repository scan and fingerprinting run.
- `slice_snapshot(snapshot_id, req: SliceRequest)` - Endpoint to generate and return a tailored LLM context manifest.
**Dependencies:** `src.core.controller`, `src.analysis.context_slicer`, `src.analysis.snapshot_comparator`

#### `src/cli/main.py`
**Role:** Provides a command-line interface for executing snapshots, exports, and structural diffs.
**Key Exports:**
- `main()` - The entry point for parsing arguments and dispatching commands to the controller.
**Dependencies:** `src.core.controller`, `src.core.config_loader`

#### `src/core/config_loader.py`
**Role:** Locates and parses the `repo-runner.json` project-level configuration file.
**Key Exports:**
- `load_config(repo_root): RepoRunnerConfig` - Attempts to read local settings or returns default system-wide configuration.
**Dependencies:** `src.core.types`

#### `src/core/controller.py`
**Role:** The central orchestrator that manages the pipeline from filesystem scanning to snapshot persistence.
**Key Exports:**
- `run_snapshot(...)` - Executes the full sequence: scan, fingerprint, analyze imports, build graph, and write snapshot.
- `run_export_flatten(...)` - Handles the generation of flattened Markdown artifacts for LLM consumption.
- `run_compare(...)` - High-level wrapper for diffing two stored snapshots.
**Dependencies:** `src.scanner`, `src.fingerprint`, `src.analysis`, `src.snapshot`, `src.exporters`

#### `src/core/types.py`
**Role:** Defines the Pydantic data models used for system-wide type safety and JSON serialization.
**Key Exports:**
- `Manifest` - The primary data structure containing repo metadata and a flat list of file entries.
- `FileEntry` - Represents a single file including its path, hash, language, and symbols.
- `GraphStructure` - Represents the dependency relationships and detected cycles.
- `RepoRunnerConfig` - Defines the schema for persistent user settings.

#### `src/exporters/flatten_markdown_exporter.py`
**Role:** Converts repository manifests into single, LLM-friendly Markdown documents containing file trees and source code.
**Key Exports:**
- `generate_content(repo_root, manifest, options, title, snapshot_id): str` - Produces the Markdown string including a tree, file contents, and token telemetry.
- `export(...)` - Generates the content and persists it to a file within the snapshot directory.

#### `src/fingerprint/file_fingerprint.py`
**Role:** Generates cryptographic hashes and identifies source languages for individual files.
**Key Exports:**
- `fingerprint(path): Dict` - Calculates SHA256 hashes and maps extensions to programming language names.

#### `src/gui/app.py`
**Role:** Implements the graphical control panel and manages background worker threads for UI responsiveness.
**Key Exports:**
- `RepoRunnerApp(tk.Tk)` - The main application class providing the window and event handling.
- `run_gui()` - Initializes and starts the Tkinter event loop.
**Dependencies:** `src.core.controller`, `src.gui.components`

#### `src/normalize/path_normalizer.py`
**Role:** Ensures consistent path naming and stable IDs across different operating systems.
**Key Exports:**
- `normalize(absolute_path): str` - Converts absolute paths to repo-relative, lowercase, forward-slash strings.
- `file_id(normalized_path): str` - Generates a URN-style stable ID for a file (e.g., `file:src/main.py`).

#### `src/observability/token_telemetry.py`
**Role:** Provides language-aware heuristics for estimating LLM token usage.
**Key Exports:**
- `estimate_tokens(size_bytes, language): int` - Calculates token counts using language-specific character-to-token ratios.
- `format_usage(current, max): str` - Generates human-readable percentage strings for context budgeting.

#### `src/scanner/filesystem_scanner.py`
**Role:** Recursively walks the filesystem to identify files while respecting depth limits and ignore rules.
**Key Exports:**
- `scan(root_paths, progress_callback): List[str]` - Returns a list of absolute paths found, avoiding symlink cycles and ignored directories.

#### `src/snapshot/snapshot_loader.py`
**Role:** Resolves snapshot identifiers (including the "latest" alias) to physical directories on disk.
**Key Exports:**
- `resolve_snapshot_dir(snapshot_id): str` - Determines the path to a snapshot, resolving via `current.json` if necessary.

#### `src/snapshot/snapshot_writer.py`
**Role:** Persists the computed manifest, graph, and structure artifacts to the output directory.
**Key Exports:**
- `write(manifest, structure, graph, symbols, write_current_pointer): str` - Saves all snapshot metadata and optionally updates the "current" pointer.

#### `src/structure/structure_builder.py`
**Role:** Organizes flat file lists into a module-oriented hierarchical structure for navigation.
**Key Exports:**
- `build(repo_id, files): Dict` - Maps file entries to their respective directory modules.

---
*Note: No dedicated test files (`test_*.py` or `*_test.py`) were detected in the provided source module scan.*