## 1. The Tree

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

## 2. File Summaries

### `src/analysis/graph_builder.py`
**Role:** Constructs a directed dependency graph by resolving raw import strings into internal file IDs or external package IDs.
**Key Exports:**
- `build(files: List[FileEntry]): GraphStructure` - Orchestrates node creation and edge resolution for an entire file set.
- `_resolve_external(import_str, language): Optional[str]` - Heuristically identifies top-level package names (e.g., `pandas` from `pandas.core`).
**Dependencies:** `src.core.types`, `os`.

### `src/analysis/import_scanner.py`
**Role:** Performs static analysis to extract import targets from source code using AST for Python and Regex for JS/TS.
**Key Exports:**
- `scan(path, language): List[str]` - Reads a file and returns a sorted list of unique raw import strings.
- `_scan_python(content, imports)` - Uses `ast.parse` to find `Import` and `ImportFrom` nodes.
**Dependencies:** `ast`, `re`, `os`.

### `src/cli/main.py`
**Role:** Defines the command-line interface and maps user arguments to the core pipeline controllers.
**Key Exports:**
- `main()` - Entry point for CLI execution handling `snapshot`, `export`, and `ui` commands.
- `_parse_args()` - Configures command-line flags for depth, ignore rules, and export options.
**Dependencies:** `src.core.controller`, `argparse`.

### `src/core/controller.py`
**Role:** The central pipeline orchestrator that sequences scanning, normalization, analysis, and snapshot writing.
**Key Exports:**
- `run_snapshot(...): str` - Executes the full creation pipeline and returns the resulting `snapshot_id`.
- `run_export_flatten(...): str` - Loads a snapshot and generates a flattened markdown projection.
**Dependencies:** `src.scanner`, `src.normalize`, `src.fingerprint`, `src.analysis`, `src.structure`, `src.snapshot`, `src.exporters`.

### `src/core/types.py`
**Role:** Defines the canonical data schemas (TypedDicts) for manifests, file entries, and graph structures.
**Key Exports:**
- `FileEntry` - Schema for individual file metadata (path, hash, language, imports).
- `Manifest` - Schema for the root snapshot metadata file.
- `GraphStructure` - Schema for the node-and-edge dependency graph.
**Dependencies:** `typing`.

### `src/entry_point.py`
**Role:** Primary system entry point that manages Windows DPI awareness and toggles between CLI and GUI modes.
**Key Exports:**
- `launch()` - Determines runtime mode based on the presence of command-line arguments.
**Dependencies:** `src.cli.main`, `src.gui.app`, `multiprocessing`.

### `src/exporters/flatten_markdown_exporter.py`
**Role:** Generates a deterministic, human-readable markdown representation of a snapshot’s tree and file contents.
**Key Exports:**
- `generate_content(repo_root, manifest, options, ...): str` - Produces a markdown string containing the tree and file bodies.
- `export(...): str` - Physical writer that saves the generated markdown to the snapshot's `exports/` directory.
**Dependencies:** `dataclasses`, `os`.

### `src/fingerprint/file_fingerprint.py`
**Role:** Computes file-level technical metadata, including SHA256 hashes and extension-based language detection.
**Key Exports:**
- `fingerprint(path): Dict` - Computes SHA256, file size, and identifies the programming language.
- `LANGUAGE_MAP` - Static mapping of file extensions to canonical language names.
**Dependencies:** `hashlib`, `os`.

### `src/gui/app.py`
**Role:** Main application controller for the graphical user interface, handling threading and UI layout.
**Key Exports:**
- `RepoRunnerApp` - The main Tkinter window class managing the scan/snapshot/export state.
- `_scan()` - Triggers an asynchronous filesystem scan.
**Dependencies:** `src.gui.components`, `src.core.controller`, `src.scanner`, `src.normalize`.

### `src/gui/components/config_tabs.py`
**Role:** Provides a tabbed interface for managing scan depths, ignore patterns, and export settings.
**Key Exports:**
- `ConfigTabs` - UI component for configuring `ignore_names`, `include_extensions`, and snapshot behaviors.
**Dependencies:** `tkinter.ttk`.

### `src/gui/components/export_preview.py`
**Role:** A modal window for inspecting, copying, or saving generated markdown exports.
**Key Exports:**
- `ExportPreviewWindow` - UI component displaying generated text with stats (line/char counts).
**Dependencies:** `tkinter.ttk`.

### `src/gui/components/preview_pane.py`
**Role:** Displays detailed metadata and source code previews for files selected in the tree view.
**Key Exports:**
- `load_file(abs_path, stable_id)` - Updates the pane with a file's fingerprint, imports, and raw content.
**Dependencies:** `src.fingerprint`, `src.analysis.import_scanner`.

### `src/gui/components/tree_view.py`
**Role:** Interactive hierarchical file explorer with checkbox support for manual snapshot selection.
**Key Exports:**
- `get_checked_files(): list` - Recursively collects absolute paths of all items marked with a checkmark.
- `populate(tree_structure)` - Dynamically builds the UI tree from a directory dictionary.
**Dependencies:** `tkinter.ttk`, `os`.

### `src/normalize/path_normalizer.py`
**Role:** Enforces deterministic path formatting (lowercase, forward slashes) and generates stable identifiers.
**Key Exports:**
- `normalize(absolute_path): str` - Converts absolute local paths into repo-relative, canonical strings.
- `file_id(normalized_path): str` - Formats the `file:` prefixed stable ID.
**Dependencies:** `os`.

### `src/scanner/filesystem_scanner.py`
**Role:** Implements a deterministic, depth-limited directory walker with cycle detection.
**Key Exports:**
- `scan(root_paths): List[str]` - Returns a sorted list of absolute paths while respecting ignore rules.
- `_walk(directory, depth, ...)` - Recursive internal walker with symlink cycle protection.
**Dependencies:** `os`.

### `src/snapshot/snapshot_loader.py`
**Role:** Provides utilities for locating and loading existing snapshot metadata from the output root.
**Key Exports:**
- `resolve_snapshot_dir(snapshot_id): str` - Finds the directory for a specific ID or the `current.json` pointer.
- `load_manifest(snapshot_dir): dict` - Loads the JSON manifest for a given snapshot.
**Dependencies:** `json`, `os`.

### `src/snapshot/snapshot_writer.py`
**Role:** Handles the atomic creation of snapshot folders and serialization of canonical metadata files.
**Key Exports:**
- `write(manifest, structure, graph, ...): str` - Writes `manifest.json`, `structure.json`, and `graph.json` to an immutable folder.
**Dependencies:** `json`, `os`, `datetime`.

### `src/structure/structure_builder.py`
**Role:** Groups a flat list of file entries into a hierarchical "module" structure based on directory containment.
**Key Exports:**
- `build(repo_id, files): Dict` - Returns the `structure.json` model representing the repository's logical containment.
**Dependencies:** `collections.defaultdict`.