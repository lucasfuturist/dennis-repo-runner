### `repo-runner` Source Module: High-Resolution Interface Map

## The Tree
```
└── src
    ├── __init__.py
    ├── analysis
    │   ├── __init__.py
    │   ├── graph_builder.py
    │   └── import_scanner.py
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
    ├── scanner
    │   └── filesystem_scanner.py
    ├── snapshot
    │   ├── snapshot_loader.py
    │   └── snapshot_writer.py
    └── structure
        └── structure_builder.py
```

## File Summaries

### `src/analysis/graph_builder.py`
**Role:** Transforms flat file entries into a directed dependency graph showing internal and external imports.
**Key Exports:**
- `GraphBuilder.build(files): GraphStructure` - Converts list of file data into a schema-compliant node/edge graph.
**Dependencies:** `src.core.types`

### `src/analysis/import_scanner.py`
**Role:** Statically analyzes file content to extract import statements for Python, JavaScript, and TypeScript.
**Key Exports:**
- `ImportScanner.scan(path, language): List[str]` - Returns unique, sorted import targets found in a file.
**Dependencies:** Built-in `ast` and `re` modules.

### `src/cli/main.py`
**Role:** Entry point for command-line interactions, handling snapshot creation and export triggers.
**Key Exports:**
- `main()` - Orchestrates execution based on parsed subcommands (`snapshot`, `export`, `ui`).
**Dependencies:** `src.core.controller`, `src.gui.app`

### `src/core/controller.py`
**Role:** The central architectural coordinator that links the scanner, analysis engines, and writers to perform snapshots.
**Key Exports:**
- `run_snapshot(...) : str` - High-level orchestrator that scans, fingerprints, analyzes, and saves a repository state.
- `run_export_flatten(...) : str` - Orchestrator for generating text-based exports from existing snapshots.
**Dependencies:** `src.scanner`, `src.normalize`, `src.fingerprint`, `src.analysis`, `src.snapshot`, `src.structure`, `src.exporters`

### `src/core/types.py`
**Role:** Defines the core data models and TypeHints used throughout the application to ensure schema consistency.
**Key Exports:**
- `FileEntry` - Model for file metadata (path, hash, imports, language).
- `Manifest` - Model for the complete snapshot metadata file.
- `GraphStructure` - Model for the dependency graph nodes and edges.
**Dependencies:** None

### `src/entry_point.py`
**Role:** Primary system execution wrapper that handles GUI DPI awareness and forks between CLI and GUI modes.
**Key Exports:**
- `launch()` - Determines whether to boot the application in terminal or graphical mode.
**Dependencies:** `src.cli.main`, `src.gui.app`

### `src/exporters/flatten_markdown_exporter.py`
**Role:** Generates human-readable and LLM-ready Markdown representations of a repository's file tree and contents.
**Key Exports:**
- `FlattenMarkdownExporter.generate_content(...): str` - Produces the raw Markdown string for a set of files.
- `FlattenOptions` - Data class holding configuration for export scoping and detail level.
- `TEXT_EXTENSIONS` - Set of file extensions eligible for text-based inclusion in exports.
**Dependencies:** `src.core.types` (implicit via manifest structure).

### `src/fingerprint/file_fingerprint.py`
**Role:** Generates unique identification data (hashes) and classifies the programming language of individual files.
**Key Exports:**
- `FileFingerprint.fingerprint(path): Dict` - Returns SHA256 hash, size, and detected language for a file.
- `LANGUAGE_MAP` - Configuration mapping extensions to canonical language names.
**Dependencies:** Built-in `hashlib`.

### `src/gui/app.py`
**Role:** Main application controller for the Tkinter GUI, managing window state and background worker threads.
**Key Exports:**
- `RepoRunnerApp` - The root window class containing the UI layout and interaction logic.
- `run_gui()` - Initializes and starts the Tkinter main loop.
**Dependencies:** `src.core.controller`, `src.gui.components.*`, `src.scanner`, `src.normalize`

### `src/gui/components/config_tabs.py`
**Role:** GUI component for managing scan parameters, ignore rules, and export configurations.
**Key Exports:**
- `ConfigTabs` - A notebook widget containing `depth_var`, `ignore_var`, and `include_readme_var` state.
**Dependencies:** Built-in `tkinter.ttk`.

### `src/gui/components/export_preview.py`
**Role:** Modal window providing a preview of the Markdown export and token usage estimations for AI context windows.
**Key Exports:**
- `ExportPreviewWindow` - Displays generated text and calculates context health based on character counts.
**Dependencies:** Built-in `tkinter`.

### `src/gui/components/preview_pane.py`
**Role:** Visual component for inspecting individual file metadata and raw contents during the selection process.
**Key Exports:**
- `PreviewPanel.load_file(abs_path, stable_id)` - Updates the view with file properties and text preview.
**Dependencies:** `src.fingerprint`, `src.analysis.import_scanner`

### `src/gui/components/progress_window.py`
**Role:** Modal overlay used to signal long-running background tasks (scanning, hashing) and provide cancellation hooks.
**Key Exports:**
- `ProgressWindow` - Indeterminate progress tracker with messaging and `cancelled` state.
**Dependencies:** Built-in `tkinter`.

### `src/gui/components/tree_view.py`
**Role:** Interactive file explorer with checkbox-based selection for granular snapshot control.
**Key Exports:**
- `FileTreePanel` - Tree widget managing checked/unchecked states for files and folders.
- `get_checked_files(): List[str]` - Returns paths for all items selected in the UI.
**Dependencies:** Built-in `tkinter`.

### `src/normalize/path_normalizer.py`
**Role:** Standardizes system paths into a deterministic, repo-relative format used for IDs across all artifacts.
**Key Exports:**
- `PathNormalizer.normalize(abs_path): str` - Converts absolute paths to lowercased, forward-slash relative strings.
- `PathNormalizer.file_id(path): str` - Generates a stable "file:..." URI.
**Dependencies:** Built-in `os`.

### `src/scanner/filesystem_scanner.py`
**Role:** Robust directory crawler that handles symlink cycles, permission errors, and depth limits.
**Key Exports:**
- `FileSystemScanner.scan(root_paths, progress_callback): List[str]` - Returns a sorted list of all files found within constraints.
**Dependencies:** Built-in `os`.

### `src/snapshot/snapshot_loader.py`
**Role:** Utility for resolving and reading previously saved snapshot manifests and structures from the filesystem.
**Key Exports:**
- `SnapshotLoader.resolve_snapshot_dir(snapshot_id): str` - Locates the folder for a given ID or the "current" pointer.
- `load_manifest(snapshot_dir): dict` - Deserializes the manifest JSON.
**Dependencies:** Built-in `json`.

### `src/snapshot/snapshot_writer.py`
**Role:** Persists captured repository states to disk, organizing metadata into versioned JSON files.
**Key Exports:**
- `SnapshotWriter.write(manifest, structure, graph, ...): str` - Saves the core snapshot files and updates the `current.json` pointer.
**Dependencies:** Built-in `json`, `datetime`.

### `src/structure/structure_builder.py`
**Role:** Logic for grouping flat file lists into a hierarchical module/directory containment structure.
**Key Exports:**
- `StructureBuilder.build(repo_id, files): Dict` - Organizes files into a structured JSON representation of the repo.
**Dependencies:** None (Self-contained).