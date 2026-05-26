# Codebase Architectural Context

> *This document contains high-resolution structural maps of the codebase, compressed to exclude implementation logic.*

## Directory Tree

```text
.
├── scripts/
│   ├── build_exe.ps1
│   ├── export-signal.ps1
│   ├── llm_compressor.py
│   ├── llm_stitcher.py
│   ├── package-repo.ps1
│   └── verify.ps1
├── src/
│   ├── analysis/
│   │   ├── context_slicer.py
│   │   ├── graph_builder.py
│   │   ├── import_scanner.py
│   │   └── snapshot_comparator.py
│   ├── api/
│   │   ├── init.py
│   │   └── server.py
│   ├── cli/
│   │   └── main.py
│   ├── core/
│   │   ├── config_loader.py
│   │   ├── controller.py
│   │   ├── repo-runner.code-workspace
│   │   └── types.py
│   ├── entry_point.py
│   ├── exporters/
│   │   ├── drawio_exporter.py
│   │   ├── flatten_markdown_exporter.py
│   │   └── mermaid_exporter.py
│   ├── fingerprint/
│   │   └── file_fingerprint.py
│   ├── gui/
│   │   ├── app.py
│   │   └── components/
│   │       ├── compression_queue_dialog.py
│   │       ├── config_tabs.py
│   │       ├── export_preview.py
│   │       ├── preview_pane.py
│   │       ├── progress_window.py
│   │       └── tree_view.py
│   ├── normalize/
│   │   └── path_normalizer.py
│   ├── observability/
│   │   ├── init.py
│   │   └── token_telemetry.py
│   ├── scanner/
│   │   └── filesystem_scanner.py
│   ├── snapshot/
│   │   ├── snapshot_loader.py
│   │   └── snapshot_writer.py
│   └── structure/
│       └── structure_builder.py
└── tests/
    ├── conftest.py
    ├── integration/
    │   ├── __init__.py
    │   ├── test_api.py
    │   ├── test_cli_diff.py
    │   ├── test_cli_slice.py
    │   ├── test_compression_state.py
    │   ├── test_e2e_snapshot.py
    │   ├── test_export_flow.py
    │   ├── test_golden.py
    │   ├── test_graph_snapshot.py
    │   └── test_robustness.py
    └── unit/
        ├── test_collision_logic.py
        ├── test_config_loader.py
        ├── test_context_slicer.py
        ├── test_drawio_exporter.py
        ├── test_file_fingerprint.py
        ├── test_filesystem_scanner.py
        ├── test_flatten_exporter.py
        ├── test_graph_builder.py
        ├── test_graph_builder_unresolved.py
        ├── test_ignore_logic.py
        ├── test_import_scanner.py
        ├── test_mermaid_exporter.py
        ├── test_path_normalizer.py
        ├── test_scanner_constants.py
        ├── test_snapshot_comparator.py
        ├── test_snapshot_loader.py
        ├── test_structure_builder.py
        ├── test_token_telemetry.py
        └── test_types.py
```

---

### `scripts/build_exe.ps1`
**Role:** Orchestrates the build pipeline by clearing old build artifacts and invoking PyInstaller to compile the Python source code into a standalone Windows executable.
**Key Interfaces:**
- `$ExePath` - The critical output state representing the file path of the successfully compiled executable artifact (`dist\repo-runner.exe`).
**Dependencies:** PyInstaller, src/entry_point.py, tkinter (hidden import), src/ (bundled directory)

---

### scripts/export-signal.ps1
**Role:** Orchestrates the aggregation and export of essential repository source code and documentation into a single flattened Markdown file and a ZIP archive based on configurable inclusion and exclusion filters.
**Key Interfaces:**
- `export-signal.ps1(OutDir: string, IncludeGlobs: string[], ExcludeDirs: string[], ExcludeExts: string[]): void` - Accepts filter configurations and an output directory to trigger the file aggregation and archiving process.
- `$FlattenOut / String` - The absolute file path to the resulting exported Markdown document containing the concatenated repository contents.
- `$ZipOut / String` - The absolute file path to the resulting ZIP archive of the matched repository files.
**Dependencies:** System.IO.Path, System.Collections.Generic, System.Text.StringBuilder, System.Text.RegularExpressions, Compress-Archive (PowerShell Cmdlet)

---

### `scripts/llm_compressor.py`
**Role:** Serves as a CLI orchestrator that queries the Google Gemini API to generate architectural summaries for modified source files and updates a centralized JSON state repository.
**Key Interfaces:**
- `main(): None` - Executes the compression pipeline by reading CLI arguments (repository path, state directory), interfacing with the Gemini API, and writing output directly to context state files.
- `SYSTEM_PROMPT / str` - Defines the strict architectural rules and schema sent to the LLM for compressing file contexts.
**Dependencies:** `os`, `sys`, `json`, `time`, `argparse`, `typing`, `dotenv`, `google.genai`

---

### `scripts/llm_stitcher.py`
**Role:** Generates a unified Markdown architectural context document by stitching together compressed JSON representations and generating an ASCII directory tree.
**Key Interfaces:**
- `render_ascii_tree(paths: List[str]): str` - Converts a list of relative file paths into a formatted ASCII directory tree string.
- `main(): None` - Parses CLI arguments, reads the compressed JSON state, and writes the final stitched Markdown document.
- `None` - No critical exported state, constants, or data structures.
**Dependencies:** `os`, `json`, `argparse`, `typing`

---

### `scripts/package-repo.ps1`
**Role:** A build and packaging script responsible for creating a clean, filtered directory copy and a deployable ZIP archive of the repository.
**Key Interfaces:**
- `package-repo.ps1(OutDir, CopyFolderName, ZipFileName, ExcludeDirs, ExcludeFiles, VerboseCopy): Void` - Executes the packaging process using provided output configurations and exclusion filters to generate distribution artifacts.
- `$CopyOut / String` - The absolute path to the generated clean repository copy directory.
- `$ZipOut / String` - The absolute path to the generated repository ZIP archive.
- `$RoboLog / String` - The log file generated during the copy process.
**Dependencies:** `robocopy` (Windows native utility), `Compress-Archive` (PowerShell native module)

---

### `scripts/verify.ps1`
**Role:** Serves as the primary continuous integration and verification entry point to validate the project's "Definition of Done" by executing the complete test suite.
**Key Interfaces:**
- `verify.ps1` - Executes the global testing process, returning exit code 0 upon complete success or 1 if any tests fail.
**Dependencies:** python, pytest

---

### `src/analysis/context_slicer.py`
**Role:** Deterministically prunes repository manifests based on graph topology and token budgets to compress LLM context windows around a target focus file.
**Key Interfaces:**
- `ContextSlicer` - A static utility class responsible for graph-based manifest filtering.
- `slice_manifest(manifest: Union[Dict, Any], graph: Union[Dict, Any], focus_id: str, radius: int, max_tokens: Optional[int]): Dict[str, Any]` - Accepts a repository manifest, dependency graph, target file/symbol, search radius, and token budget, returning a pruned manifest dictionary containing only the reachable files.
- `VariableName / TypeName` - None
**Dependencies:** `src.observability.token_telemetry`, `typing`, `collections`, `logging`

---

### `src/analysis/graph_builder.py`
**Role:** Constructs a language-aware dependency graph from parsed source files by resolving internal imports, normalizing external packages, and detecting cyclic dependencies.
**Key Interfaces:**
- `GraphBuilder` - Service responsible for orchestrating the conversion of parsed file metadata into a connected dependency graph system.
- `build(files: List[FileEntry]): GraphStructure` - Accepts a collection of parsed file models and returns a fully constructed graph containing resolved nodes, edges, detected cycles, and unresolved references.
- `None` - No critical exported state, constants, or data structures.
**Dependencies:** `os`, `typing`, `src.core.types` (`FileEntry`, `GraphStructure`, `GraphNode`, `GraphEdge`, `UnresolvedReference`)

---

### `src/analysis/import_scanner.py`
**Role:** Extracts import statements and defined symbols from Python, JavaScript, and TypeScript source files to facilitate static code dependency analysis.
**Key Interfaces:**
- `ImportScanner` - A static utility class responsible for orchestrating language-specific parsing of source files.
- `scan(path: str, language: str): Dict[str, List[str]]` - Accepts a source file path and language identifier, returning a dictionary containing lists of its parsed 'imports' and declared 'symbols'.
- `None`
**Dependencies:** `re`, `ast`, `typing`

---

### src/analysis/snapshot_comparator.py
**Role:** Acts as a deterministic diff engine that computes structural and dependency drift between two repository snapshots.
**Key Interfaces:**
- `SnapshotComparator` - A stateless service class responsible for evaluating structural and file-level comparisons between repository states.
- `compare(manifest_a, manifest_b, graph_a, graph_b): SnapshotDiffReport` - Ingests base and target manifests alongside their optional dependency graphs to compute and return a comprehensive report of added, removed, or modified files and edges.
- `Variables / Types` - None
**Dependencies:** typing, src.core.types

---

### `src/api/init.py`
**Role:** Initializes the API package, acting as the structural entry point for API-related modules.
**Key Interfaces:**
- None
**Dependencies:** None

---

### `src/api/server.py`
**Role:** Acts as the primary HTTP controller routing requests to core engine services for repository snapshot generation, context slicing, and structural comparison.
**Key Interfaces:**
- `SnapshotRequest` - Pydantic model defining configuration parameters for scanning and fingerprinting a repository.
- `SliceRequest` - Pydantic model defining target file, radius, and token constraints for generating an LLM context slice.
- `CompareRequest` - Pydantic model defining base and target snapshot IDs for structural diffing.
- `root(): RedirectResponse` - Redirects the root endpoint to the interactive API documentation.
- `create_snapshot(req: SnapshotRequest): dict` - Triggers repository ingestion via the `run_snapshot` service and returns the generated snapshot ID.
- `slice_snapshot(snapshot_id: str, req: SliceRequest): dict` - Invokes `ContextSlicer` to build an isolated dependency slice and returns the compressed manifest alongside token telemetry.
- `compare_snapshots(req: CompareRequest): SnapshotDiffReport` - Uses `SnapshotComparator` to structurally diff two snapshots and returns a comprehensive drift report.
- `app / FastAPI` - The exported FastAPI web application instance.
**Dependencies:** os, json, fastapi, pydantic, typing, src.core.controller, src.snapshot.snapshot_loader, src.analysis.context_slicer, src.analysis.snapshot_comparator, src.observability.token_telemetry, src.core.types

---

### `src/cli/main.py`
**Role:** Acts as the primary Command-Line Interface (CLI) entry point, parsing arguments and routing commands to the underlying core controller services.
**Key Interfaces:**
- `main(): None` - Evaluates command-line arguments and delegates execution to the corresponding core service (e.g., snapshot, slice, diff, diagram, export, ui).
- `cli_progress(phase: str, current: int, total: int): None` - Provides a standardized terminal progress tracking callback for long-running core operations.
**Dependencies:** `src.core.controller`, `src.core.config_loader`, `src.gui.app`, `argparse`, `os`, `sys`

---

### `src/core/config_loader.py`
**Role:** Parses and loads the project's configuration file into a validated internal configuration model.
**Key Interfaces:**
- `ConfigLoader` - Utility class responsible for locating and parsing project-level configuration files.
- `load_config(repo_root: str): RepoRunnerConfig` - Accepts a repository root directory path and returns a validated configuration state object.
- `CONFIG_FILENAME` - Constant defining the expected configuration file name.
**Dependencies:** `os`, `json`, `src.core.types` (`RepoRunnerConfig`)

---

### src/core/controller.py
**Role:** Acts as the primary orchestrator for the system, wiring together filesystem scanning, dependency analysis, snapshot persistence, comparison, and export workflows.
**Key Interfaces:**
- `run_snapshot(repo_root, output_root, depth, ignore, include_extensions, include_readme, write_current_pointer, skip_graph, explicit_file_list, export_flatten, progress_callback, manual_override): str` - Orchestrates the `FileSystemScanner`, `FileFingerprint`, `GraphBuilder`, and `SnapshotWriter` to create and persist a new codebase snapshot, returning the generated snapshot ID.
- `run_export_flatten(output_root, repo_root, snapshot_id, output_path, tree_only, include_readme, scope, title, focus_id, radius, max_tokens, print_summary): str` - Uses `SnapshotLoader` and `ContextSlicer` to load and optionally filter a snapshot, passing it to `FlattenMarkdownExporter` to generate a markdown file and returning the output path.
- `run_export_diagram(output_root, repo_root, snapshot_id, output_path, title, format): str` - Loads a snapshot's graph data and delegates to `MermaidExporter` or `DrawioExporter` to generate an architectural diagram.
- `run_compare(output_root, base_id, target_id): SnapshotDiffReport` - Uses `SnapshotLoader` to retrieve two snapshot manifests and delegates to `SnapshotComparator` to generate a structural difference report.
- `run_export_compression_state(output_root, base_id, target_id, state_dir): Dict[str, Any]` - Analyzes diffs between snapshots to synchronize external JSON state files (`master_compressed_context.json`, `file_changed_bool.json`) for incremental processing pipelines.
- `VariableName / TypeName` - None
**Dependencies:** src.core.types (Manifest, FileEntry, etc.), src.analysis (ImportScanner, GraphBuilder, ContextSlicer, SnapshotComparator), src.exporters (FlattenMarkdownExporter, MermaidExporter, DrawioExporter), src.snapshot (SnapshotLoader, SnapshotWriter), src.scanner.filesystem_scanner, src.fingerprint.file_fingerprint, src.normalize.path_normalizer, src.structure.structure_builder, src.observability.token_telemetry, os, time, json, collections, typing

---

### `src/core/repo-runner.code-workspace`
**Role:** Configures the VS Code workspace environment to simultaneously mount the main project repository and the external `repo-runner-output` directory for unified development and execution context.
**Key Interfaces:**
- `folders / Array` - Defines the relative directory paths included in the workspace (the project root and the output directory).
- `settings / Object` - Contains workspace-specific editor configurations (currently empty).
**Dependencies:** None

---

### `src/core/types.py`
**Role:** Acts as the central domain model layer, defining Pydantic schemas for system configuration, repository file snapshots, dependency graphs, and structural diffing.
**Key Interfaces:**
- `RepoRunnerConfig` - Defines the system-wide default configuration parameters for repository snapshot runs.
- `FileEntry` - Represents a single normalized file in a snapshot, storing metadata, imports, and extracted symbols.
- `GraphNode` - Represents a structural entity (file, module, or external dependency) within the dependency graph.
- `GraphEdge` - Represents a directed relationship (such as an import) between two graph nodes.
- `UnresolvedReference` - Captures broken or unresolvable import references within the parsed repository.
- `GraphStructure` - Contains the complete parsed dependency graph, tracking nodes, edges, cycles, and unresolved links.
- `ManifestStats` - Aggregates summary statistics for a snapshot, such as file count, total bytes, and external dependencies.
- `GitMetadata` - Captures the git repository state and commit context for a snapshot.
- `ManifestInputs` - Records the repository paths and environment context used to initiate a snapshot run.
- `ManifestConfig` - Captures the precise configuration state applied during the generation of a snapshot.
- `Manifest` - The root aggregate model representing a complete, versioned repository snapshot including files, stats, config, and metadata.
- `FileDiff` - Represents the mutation state (added, removed, modified) of a single file between two structural snapshots.
- `EdgeDiff` - Represents the addition or removal of a dependency relationship between snapshots.
- `SnapshotDiffReport` - Aggregates all file and edge diffs into a comprehensive comparison report spanning two snapshots.
**Dependencies:** `typing`, `pydantic`

---

### `src/entry_point.py`
**Role:** Serves as the root bootstrap mechanism for the application, delegating execution to either the Command Line Interface (CLI) or Graphical User Interface (GUI) based on launch arguments.
**Key Interfaces:**
- `launch(): None` - Evaluates startup arguments to dynamically import and invoke the appropriate application mode.
**Dependencies:** `sys`, `multiprocessing`, `ctypes`, `src.cli.main`, `src.gui.app`

---

### src/exporters/drawio_exporter.py
**Role:** Translates the internal dependency graph representation into a Draw.io Auto-Layout CSV file for visual rendering of modules, nodes, and relationships.
**Key Interfaces:**
- `DrawioExporter` - Exporter class responsible for converting graph models into styled Draw.io CSV files.
- `export(snapshot_dir: str, graph: GraphStructure, output_path: Optional[str], title: Optional[str]): str` - Generates the Draw.io CSV representation of the graph, writes it to disk, and returns the output file path.
- `Exported Variables / Types` - None
**Dependencies:** os, csv, io, collections.defaultdict, typing.Optional, src.core.types.GraphStructure

---

### `src/exporters/flatten_markdown_exporter.py`
**Role:** Generates and exports a single, aggregated Markdown document containing a structural file tree and the textual contents of a repository based on scoping rules.
**Key Interfaces:**
- `FlattenOptions` - Configuration dataclass defining export boundaries, scope criteria, and content inclusion flags.
- `FlattenMarkdownExporter` - Service class responsible for assembling repository manifest data into a formatted Markdown document.
- `generate_content(repo_root, manifest, options, title, snapshot_id): str` - Processes the manifest and configuration to return the fully assembled Markdown content string.
- `export(repo_root, snapshot_dir, manifest, output_path, options, title): str` - Writes the generated Markdown string to a file on disk and returns the saved file path.
- `TEXT_EXTENSIONS / set` - Constant defining the allowed file extensions that can be read and rendered as plaintext code blocks.
**Dependencies:** os, dataclasses, typing

---

### `src/exporters/mermaid_exporter.py`
**Role:** Acts as a presentation layer component that serializes internal dependency graph structures into visual Mermaid.js diagram files.
**Key Interfaces:**
- `MermaidExporter` - Service class responsible for translating graph nodes, sub-modules, and cycle data into Mermaid.js syntax.
- `export(snapshot_dir, graph, output_path, title): str` - Accepts a `GraphStructure` payload and writes a formatted `.mmd` file to disk, returning the output file path.
- `None` - No critical exported state, constants, or data structures.
**Dependencies:** `os`, `typing`, `src.core.types`

---

### src/fingerprint/file_fingerprint.py
**Role:** Generates metadata fingerprints for individual files containing their cryptographic hash, file size, and inferred programming language.
**Key Interfaces:**
- `FileFingerprint` - Utility class encapsulating file hashing and language identification logic.
- `fingerprint(path: str): Dict` - Accepts a file path string and returns a dictionary containing the computed SHA256 hash, byte size, and language identifier.
- `LANGUAGE_MAP` - Constant dictionary mapping file extensions to their corresponding programming language string.
**Dependencies:** hashlib, os, typing

---

### `src/gui/app.py`
**Role:** Acts as the primary Tkinter-based GUI Controller, orchestrating user interactions, asynchronous filesystem scanning, repository snapshotting, context exporting, and LLM compression pipelines by delegating to underlying core services.
**Key Interfaces:**
- `RepoRunnerApp` - The main application window and state manager that wires together configuration tabs, file trees, preview panels, and asynchronous worker tasks.
- `run_gui(): None` - Bootstraps and executes the main Tkinter application event loop.
- `repo_root / scan_worker / status_var` - Critical application state tracking the active repository directory path, the current background processing thread, and the global UI status indicator.
**Dependencies:** tkinter, threading, subprocess, json, os, re, sys, datetime, platform, ctypes, src.scanner.filesystem_scanner, src.normalize.path_normalizer, src.core.controller, src.exporters.flatten_markdown_exporter, src.gui.components.config_tabs, src.gui.components.tree_view, src.gui.components.preview_pane, src.gui.components.export_preview, src.gui.components.progress_window, src.gui.components.compression_queue_dialog

---

### src/gui/components/compression_queue_dialog.py
**Role:** Acts as a GUI dialog component responsible for presenting a pre-compression summary of changed files, allowing users to preview file diffs and filter which files to include or skip before executing the LLM compression service.
**Key Interfaces:**
- `CompressionQueueDialog` - A Tkinter modal dialog component for managing the file compression queue state.
- `__init__(parent, state_dir, repo_root, on_confirm_callback, on_cancel_callback): CompressionQueueDialog` - Initializes the modal view, loads the pending file state from disk, and wires up the lifecycle callbacks.
- `queue / dict` - The parsed JSON state dictionary tracking the compression status of repository files.
- `pending_files / list` - A sorted list of stable file identifiers currently flagged for compression.
- `file_states / dict` - In-memory state tracking the user's toggled inclusion/exclusion preferences before saving to disk.
**Dependencies:** tkinter, json, os, subprocess

---

### `src/gui/components/config_tabs.py`
**Role:** A GUI component extending `ttk.Notebook` responsible for rendering and managing user configuration states (scan settings, ignore rules, and export options) for the application.
**Key Interfaces:**
- `ConfigTabs` - A Tkinter Notebook widget class that encapsulates the application's configuration tabs and state variables.
- `__init__(parent): None` - Initializes the notebook, instantiates configuration state variables, and attaches the component to the parent GUI.
- `depth_var / tk.IntVar`, `ignore_var / tk.StringVar`, `ext_var / tk.StringVar`, `include_readme_var / tk.BooleanVar`, `write_current_var / tk.BooleanVar`, `export_tree_only_var / tk.BooleanVar` - Exported state variables holding user configuration data.
- `btn_apply_selection / ttk.Button`, `txt_quick_select / tk.Text` - Exposed GUI widget references intended for external event binding by the main application controller.
**Dependencies:** tkinter, tkinter.ttk

---

### `src/gui/components/export_preview.py`
**Role:** A GUI presentation component that provides a read-only dialog for users to review compiled context, evaluate LLM token estimations, and export the final payload.
**Key Interfaces:**
- `ExportPreviewWindow` - A Tkinter Toplevel window component that encapsulates the context review interface and export actions.
- `__init__(parent, content, default_filename): None` - Initializes the preview dialog and token estimator with the raw text payload to be evaluated.
- `VariableName / TypeName` - None
**Dependencies:** tkinter, tkinter.ttk, tkinter.filedialog, tkinter.messagebox

---

### src/gui/components/preview_pane.py
**Role:** Acts as a GUI view component that coordinates with backend analysis services to display file metadata, structural symbols, and syntax-highlighted source code.
**Key Interfaces:**
- `PreviewPanel` - A Tkinter UI frame responsible for rendering the metadata header and source code text area.
- `clear(): None` - Resets the preview panel's metadata labels and clears the text content.
- `load_file(abs_path, stable_id): None` - Requests file data from the fingerprinting and import scanning services to populate the view with metadata, imports, symbols, and raw source code.
- `None` - No critical exported state, constants, or data structures.
**Dependencies:** tkinter, src.fingerprint.file_fingerprint, src.analysis.import_scanner

---

### `src/gui/components/progress_window.py`
**Role:** Provides a modal GUI dialog component to display task progress and capture user cancellation requests during long-running operations.
**Key Interfaces:**
- `ProgressWindow` - A modal `tk.Toplevel` window component for displaying determinate or indeterminate progress states.
- `__init__(parent, title, message): ProgressWindow` - Initializes the modal window attached to a parent UI component.
- `update_message(text): None` - Updates the primary status text displayed to the user.
- `update_progress(current, total): None` - Adjusts the progress bar value and automatically toggles between determinate and indeterminate modes based on the provided totals.
- `cancel(): None` - Triggers the cancellation state and updates the UI to reflect the pending abort.
- `close(): None` - Releases modal focus and destroys the window instance.
- `cancelled` - Boolean state indicating whether a user cancellation request has been triggered.
**Dependencies:** tkinter, tkinter.ttk

---

### `src/gui/components/tree_view.py`
**Role:** Provides an interactive Tkinter-based GUI component for displaying, selecting, and grouping a hierarchical file system structure into logical modules.
**Key Interfaces:**
- `FileTreePanel` - A custom Tkinter Frame widget representing an interactive file and folder tree with checkbox states.
- `__init__(parent, on_select_callback): None` - Initializes the UI layout, sets up tree columns, and registers the selection event handler.
- `clear(): None` - Empties all nodes from the visual tree.
- `check_specific_files(target_stable_ids): int` - Selects specific files matching the provided IDs and returns the count of successfully matched items.
- `populate(tree_structure): None` - Builds the visual tree hierarchy from a provided data dictionary.
- `get_checked_files(parent_id): list` - Traverses the tree and returns a list of absolute file paths for all currently checked items.
- `get_modules(): dict` - Aggregates and returns a mapping of module names to lists of their checked file paths based on user-defined folder locks.
- `on_select_callback / Callable` - Injected event handler triggered when a user selects a file node.
- `tree / ttk.Treeview` - The core UI widget managing the display, columns, and tag states of the file structure.
**Dependencies:** os, tkinter, tkinter.ttk

---

### `src/normalize/path_normalizer.py`
**Role:** Standardizes system file paths into secure, repository-relative formats and generates consistent entity identifiers for files, modules, and the repository root.
**Key Interfaces:**
- `PathNormalizer` - A utility class responsible for cross-OS path sanitization, normalization, and standardized ID generation relative to a repository root.
- `normalize(absolute_path: str): str` - Converts an absolute file path into a secure, lowercased, and repository-relative string.
- `module_path(normalized_file_path: str): str` - Extracts the standardized directory path from a given normalized file path.
- `file_id(normalized_path: str): str` - Generates a unique, formatted identifier string for a file node.
- `module_id(module_path: str): str` - Generates a unique, formatted identifier string for a module/directory node.
- `repo_id(): str` - Returns the constant identifier string representing the repository root.
- `None` - No critical exported state, constants, or data structures.
**Dependencies:** os

---

### `src/observability/init.py`
**Role:** Acts as the initialization point for the observability module, responsible for tracking LLM tokenomics, performance heuristics, and system telemetry.
**Key Interfaces:**
- None
**Dependencies:** None

---

### `src/observability/token_telemetry.py`
**Role:** Provides static utilities and heuristics to estimate LLM token counts, calculate context size limits, and generate markdown telemetry reports for context slicing operations.
**Key Interfaces:**
- `TokenTelemetry` - A static utility class containing operations for calculating and reporting LLM token metrics and cost savings.
- `estimate_tokens(size_bytes: int, language: str = "unknown"): int` - Estimates the number of LLM tokens based on the provided byte size.
- `format_usage(current: int, max_tokens: int): str` - Returns a human-readable string representing current token usage against a maximum threshold.
- `calculate_telemetry(original_manifest: Dict[str, Any], sliced_manifest: Dict[str, Any], focus_id: str, radius: int): str` - Computes the reduction metrics between an original and sliced repository manifest and returns a formatted Markdown report with token counts and estimated cost.
- `TOKENS_PER_BYTE`, `COST_PER_1M_INPUT` - Heuristic constants used to convert byte sizes into estimated tokens and dollar costs.
**Dependencies:** typing

---

### `src/scanner/filesystem_scanner.py`
**Role:** Provides a configurable file system traversal service that safely enumerates files across directories while avoiding symlink cycles and respecting depth and exclusion rules.
**Key Interfaces:**
- `FileSystemScanner` - A service class instantiated with directory depth limits and exclusion rules responsible for safely discovering files.
- `scan(root_paths: List[str], progress_callback: Optional[Callable[[int], None]]): List[str]` - Takes a list of starting paths and an optional progress callback, returning a comprehensively gathered and sorted list of valid absolute file paths.
- `None`
**Dependencies:** os, typing

---

### `src/snapshot/snapshot_loader.py`
**Role:** Utility class responsible for resolving snapshot directory paths and loading snapshot JSON artifacts from the filesystem.
**Key Interfaces:**
- `SnapshotLoader` - Utility entity for locating and parsing snapshot data directories.
- `resolve_snapshot_dir(snapshot_id: Optional[str]): str` - Takes an explicit snapshot ID or alias (like "current") and returns the resolved absolute directory path.
- `load_manifest(snapshot_dir: str): dict` - Takes a resolved snapshot directory path and returns the parsed manifest artifact.
- `load_structure(snapshot_dir: str): dict` - Takes a resolved snapshot directory path and returns the parsed structure artifact.
- `None` - No critical exported state, constants, or standalone data structures.
**Dependencies:** json, os, typing

---

### src/snapshot/snapshot_writer.py
**Role:** Handles the persistence layer for repository snapshots by serializing core models (manifests, file structures, AST graphs, and symbols) to a timestamped directory on disk.
**Key Interfaces:**
- `SnapshotWriter` - A utility class responsible for orchestrating the filesystem serialization of the system's snapshot state.
- `write(manifest: Manifest, structure: Dict, graph: Optional[GraphStructure], symbols: Optional[Dict[str, List[str]]], write_current_pointer: bool): str` - Serializes the various snapshot components to a new directory and optionally updates the active snapshot pointer, returning the generated snapshot ID.
- `None` - No explicitly exported constants or independent data structures.
**Dependencies:** os, json, datetime, typing, src.core.types (Manifest, GraphStructure)

---

### `src/structure/structure_builder.py`
**Role:** Transforms a flat list of repository files into a hierarchical, module-based structural dictionary schema.
**Key Interfaces:**
- `StructureBuilder` - Service class responsible for constructing the hierarchical structural representation of a repository.
- `build(repo_id: str, files: List[FileEntry]): Dict[str, Any]` - Accepts a repository identifier and a list of file entries to generate and return a structured JSON-like schema representation.
- `None` - No critical exported state, constants, or standalone data structures.
**Dependencies:** `typing`, `src.core.types`

---

### `tests/conftest.py`
**Role:** Provides shared Pytest fixtures for generating isolated, temporary mock repositories and utilities for asserting snapshot determinism across test runs.
**Key Interfaces:**
- `temp_repo_root() -> Generator[str, None, None]` - Yields a unique, normalized temporary directory path for isolated test execution and handles lifecycle teardown.
- `create_file(temp_repo_root) -> Callable` - Provides a factory function to dynamically write files with specific paths and content within the temporary test repository.
- `simple_repo(temp_repo_root, create_file) -> str` - Bootstraps the temporary repository with a minimal Python project structure and returns the root path.
- `complex_repo(temp_repo_root, create_file) -> str` - Bootstraps the temporary repository with a mixed-language project structure including mock node_modules, .git configs, and front-end code.
- `scrub_json(data: Any) -> Any` - Recursively strips volatile fields like timestamps and dynamic paths from JSON data to enable deterministic comparison.
- `assert_snapshot_determinism() -> Callable` - Returns a validation function that asserts the logical equivalence of generated JSON snapshot files between two output directories.
**Dependencies:** pytest, os, shutil, tempfile, json, pathlib, typing

---

### `tests/integration/__init__.py`
**Role:** Designates the integration tests directory as a Python package to enable test suite discovery and module imports.
**Key Interfaces:**
- None
**Dependencies:** None

---

### `tests/integration/test_api.py`
**Role:** Provides end-to-end integration testing for the FastAPI server, validating the complete system lifecycle including snapshot generation, dependency-based context slicing, and snapshot diff comparisons.
**Key Interfaces:**
- `TestAPI` - Integration test suite class responsible for executing API endpoint workflows against the FastAPI application instance.
- `test_full_api_lifecycle(self): None` - Validates the sequential HTTP API workflow of creating snapshots, performing context slices, and executing structural diff comparisons.
- `test_slice_with_token_limit(self): None` - Verifies that the context slicing API correctly enforces maximum token limits by omitting oversized file dependencies.
- `VariableName / TypeName` - None
**Dependencies:** `unittest`, `tempfile`, `shutil`, `os`, `time`, `fastapi.testclient`, `src.api.server`

---

### `tests/integration/test_cli_diff.py`
**Role:** Acts as an integration test suite verifying that the CLI diff command correctly parses user arguments and delegates them to the comparison controller.
**Key Interfaces:**
- `TestCLIDiff` - Integration test suite for the command-line interface diff functionality.
- `test_diff_command_parsing(mock_config, mock_compare): None` - Verifies that the base and target snapshot arguments are correctly parsed from the CLI and passed to the `run_compare` logic.
- `None` - No critical exported state, constants, or data structures.
**Dependencies:** `unittest`, `unittest.mock`, `src.cli.main.main`, `sys`

---

### tests/integration/test_cli_slice.py
**Role:** Integration test suite verifying that the CLI `slice` command correctly parses user arguments and triggers the `run_export_flatten` controller.
**Key Interfaces:**
- `TestCLISlice` - Unittest suite validating the CLI argument parsing and controller delegation for the slice command.
- `test_slice_command_invocation(mock_export): None` - Verifies that explicit CLI arguments are accurately parsed and dispatched to the export controller.
- `test_slice_defaults(mock_export): None` - Verifies the correct application of default parameters (like radius and max_tokens) when optional CLI arguments are omitted.
- `None`
**Dependencies:** `unittest`, `unittest.mock`, `src.cli.main`, `sys`

---

### `tests/integration/test_compression_state.py`
**Role:** Verifies the end-to-end lifecycle and correctness of the compression-state synchronization logic by simulating snapshot creation and state updates across file modifications, additions, and deletions.
**Key Interfaces:**
- `test_compression_state_lifecycle(temp_repo_root, create_file): None` - Executes the integration test sequence validating compression state sync behavior based on temporary file fixtures.
**Dependencies:** `os`, `json`, `unittest.mock`, `src.core.controller`

---

### `tests/integration/test_e2e_snapshot.py`
**Role:** Acts as an end-to-end integration test suite verifying the complete snapshot generation lifecycle orchestrated by the core controller and verified by the snapshot loader.
**Key Interfaces:**
- `TestFullSnapshot` - An integration test suite validating directory generation, dependency extraction, and configuration handling during full repository snapshot creation.
- `test_snapshot_creation_with_graph_and_auto_export(self): None` - Tests the end-to-end snapshot process with graph mapping and flat export generation enabled, verifying output artifacts and manifest statistics.
- `test_snapshot_skip_graph(self): None` - Tests the snapshot process with graph generation explicitly disabled, verifying the absence of graph artifacts and correct configuration reflection.
**Dependencies:** `unittest`, `tempfile`, `shutil`, `os`, `src.core.controller`, `src.snapshot.snapshot_loader`

---

### `tests/integration/test_export_flow.py`
**Role:** Integration test suite verifying the end-to-end functionality of generating repository snapshots and flattening them into structured markdown exports via the core controller.
**Key Interfaces:**
- `TestExportFlow` - Test suite validating full and scoped repository export flows.
- `test_export_full_with_tokens(self): None` - Verifies the generation of a complete markdown export containing all tracked repository files and token statistics.
- `test_export_scoped(self): None` - Verifies the generation of a targeted markdown export filtered to include only specific module scopes.
**Dependencies:** unittest, tempfile, shutil, os, src.core.controller

---

### tests/integration/test_golden.py
**Role:** Executes integration tests against a predefined "golden" standard to verify that the `run_snapshot` controller accurately generates correct graph nodes, dependency edges, and valid schema manifests without regressions.
**Key Interfaces:**
- `TestGoldenSnapshot` - A test suite that validates the system's generated snapshot artifacts against a strict, human-verified baseline.
- `test_matches_golden_expectations(self): None` - Validates that the snapshot graph output contains all expected nodes with their correct types.
- `test_golden_edges(self): None` - Verifies that the expected source-to-target dependency relationships exist in the generated graph.
- `test_manifest_schema_version(self): None` - Ensures the generated manifest complies with the pinned v1.0 schema structure and sorted file ordering.
- `GOLDEN_GRAPH_SUBSET` - A dictionary constant defining the canonical source of truth for expected baseline nodes and edges.
**Dependencies:** unittest, os, json, pytest, src.core.controller, src.snapshot.snapshot_loader, tests.conftest

---

### `tests/integration/test_graph_snapshot.py`
**Role:** Integration test suite validating the end-to-end execution, determinism, and dependency resolution of the snapshot generation controller.
**Key Interfaces:**
- `TestGraphSnapshot` - Test suite verifying the artifacts produced by `run_snapshot` and read by `SnapshotLoader`.
- `test_end_to_end_graph_generation(self): None` - Validates the complete pipeline from repository parsing to accurate internal and external graph node and edge creation.
- `test_external_id_canonicalization(self): None` - Ensures external package dependencies with casing or subpath variations are normalized into unified canonical nodes.
- `test_snapshot_determinism(self): None` - Asserts that multiple snapshot executions on identical repository states yield bit-for-bit identical output artifacts.
**Dependencies:** `unittest`, `tempfile`, `shutil`, `os`, `json`, `pytest`, `src.core.controller`, `src.snapshot.snapshot_loader`, `tests.conftest`

---

### `tests/integration/test_robustness.py`
**Role:** Integration test suite validating the fault tolerance and edge-case handling of the snapshot generation process against file system anomalies like cyclical symlinks and ignored directories.
**Key Interfaces:**
- `TestRobustness` - Test suite containing integration test cases for validating system robustness.
- `test_snapshot_with_mixed_health(self): None` - Validates `run_snapshot` execution and `SnapshotLoader` manifest parsing when processing environments containing valid files, ignored paths, and cyclical symlinks.
**Dependencies:** `unittest`, `tempfile`, `shutil`, `os`, `sys`, `src.core.controller`, `src.snapshot.snapshot_loader`

---

### `tests/unit/test_collision_logic.py`
**Role:** Verifies that the core controller enforces strict file ID uniqueness to prevent data loss from case-sensitive filesystem collisions during snapshots.
**Key Interfaces:**
- `TestCollisionLogic` - Unit test class validating the file ID collision detection logic.
- `test_detects_case_collision(mock_config_loader, mock_scanner_cls): None` - Tests that `run_snapshot` raises a ValueError on file path case collisions.
- `test_no_collision_on_distinct_files(mock_config_loader, mock_scanner_cls): None` - Tests that `run_snapshot` succeeds without error when file paths are distinctly named.
**Dependencies:** `unittest`, `unittest.mock`, `os`, `pytest`, `src.core.controller`

---

### `tests/unit/test_config_loader.py`
**Role:** Validates the `ConfigLoader` component to ensure reliable application configuration fallback, custom JSON parsing, and error recovery upon invalid input.
**Key Interfaces:**
- `TestConfigLoader` - Unit test suite defining the expected behaviors, schema validations, and edge cases for the configuration loading logic.
**Dependencies:** `unittest`, `tempfile`, `shutil`, `os`, `json`, `src.core.config_loader.ConfigLoader`

---

### `tests/unit/test_context_slicer.py`
**Role:** Unit test suite responsible for validating the graph-based slicing, token budget enforcement, and symbol resolution mechanisms of the `ContextSlicer`.
**Key Interfaces:**
- `TestContextSlicer` - Unit test class containing isolated test cases for the `ContextSlicer` module.
- `test_radius_logic_standard(self): None` - Validates standard file inclusion based on graph adjacency radius without token constraints.
- `test_token_budget_enforcement(self): None` - Verifies that neighboring files are excluded when their inclusion would exceed the maximum token budget.
- `test_focus_exceeds_budget(self): None` - Ensures the primary focus file is always included in the slice regardless of the token limit.
- `test_cycle_stats_reporting(self): None` - Checks that cyclic dependencies occurring within the requested slice radius are accurately counted in the telemetry.
- `test_cycle_stats_exclusion(self): None` - Verifies that cycles existing entirely outside the defined slice radius are ignored.
- `test_symbol_focus_resolution(self): None` - Tests the mapping of a requested symbol to its host file before executing the standard graph traversal slice.
- `test_symbol_not_found(self): None` - Ensures an empty, safe slice representation is returned when querying a non-existent symbol.
**Dependencies:** `unittest`, `src.analysis.context_slicer.ContextSlicer`, `src.core.types.FileEntry`

---

### `tests/unit/test_drawio_exporter.py`
**Role:** Validates the `DrawioExporter` to ensure it correctly transforms internal graph structures into properly formatted Draw.io auto-layout CSV files.
**Key Interfaces:**
- `TestDrawioExporter` - Unit test suite for the Draw.io exporter component.
- `test_csv_generation(self): None` - Asserts that graph nodes, edges, and module container relationships are correctly mapped into the target Draw.io CSV schema.
**Dependencies:** `unittest`, `os`, `shutil`, `tempfile`, `csv`, `io`, `src.exporters.drawio_exporter.DrawioExporter`, `src.core.types`

---

### tests/unit/test_file_fingerprint.py
**Role:** Unit test suite responsible for verifying the robustness and correctness of the `FileFingerprint` service against valid, empty, and missing files.
**Key Interfaces:**
- `TestFingerprintHardening` - A test suite entity extending `unittest.TestCase` that validates file fingerprinting outcomes and error handling.
- `test_valid_file(): None` - Verifies accurate SHA-256 generation, byte sizing, and language resolution for standard populated files.
- `test_empty_file(): None` - Validates that zero-byte files are successfully fingerprinted and correctly identified by their extension.
- `test_locked_or_missing_file(): None` - Asserts that the fingerprinting service correctly surfaces `OSError` exceptions when target files are inaccessible.
- `None` - No critical exported state, constants, or data structures.
**Dependencies:** unittest, tempfile, shutil, os, hashlib, src.fingerprint.file_fingerprint.FileFingerprint

---

### `tests/unit/test_filesystem_scanner.py`
**Role:** Validates the behavior and resilience of the `FileSystemScanner`, ensuring correct directory traversal, ignore list processing, symlink cycle prevention, and permission error handling.
**Key Interfaces:**
- `TestFileSystemScanner` - A test case suite for verifying the functionality of the filesystem scanning module.
- `setUp(): None` - Initializes the temporary file and directory hierarchy for test execution.
- `tearDown(): None` - Cleans up temporary filesystem artifacts after test execution.
- `test_scanner_ignores(): None` - Asserts that the scanner omits files and folders matching the provided ignore criteria.
- `test_symlink_cycle_detection(): None` - Asserts that the scanner safely halts recursion when encountering circular symbolic links.
- `test_permission_error_handling(mock_listdir): None` - Asserts that the scanner catches and handles filesystem permission errors gracefully without crashing.
- `None` - No critical exported state, constants, or data structures.
**Dependencies:** `unittest`, `tempfile`, `shutil`, `os`, `sys`, `unittest.mock`, `src.scanner.filesystem_scanner.FileSystemScanner`

---

### tests/unit/test_flatten_exporter.py
**Role:** Validates the content generation, directory tree rendering, and scope-based filtering mechanisms of the flatten markdown exporter.
**Key Interfaces:**
- `TestFlattenExporter` - Unit test suite defining the behavioral expectations for the `FlattenMarkdownExporter`.
- `test_tree_generation(): None` - Tests the exporter's ability to render a valid hierarchical directory tree from a provided manifest.
- `test_scope_filtering(): None` - Verifies that the exporter correctly filters the inclusion of files based on specified scope parameters.
- `test_binary_placeholder(): None` - Checks the generation of predefined placeholder text used when encountering skipped or binary files.
**Dependencies:** `unittest`, `os`, `src.exporters.flatten_markdown_exporter`

---

### `tests/unit/test_graph_builder.py`
**Role:** Validates the architectural construction of dependency graphs by the `GraphBuilder` service, ensuring accurate language-specific import resolution, external package normalization, graph determinism, and cycle detection using `FileEntry` models.
**Key Interfaces:**
- `TestGraphBuilder` - Unit test suite defining the validation scenarios and correctness assertions for the `GraphBuilder` component.
**Dependencies:** `unittest`, `src.analysis.graph_builder`, `src.core.types`

---

### `tests/unit/test_graph_builder_unresolved.py`
**Role:** Unit test suite responsible for verifying that the `GraphBuilder` correctly identifies and tracks broken or unresolvable module imports during dependency graph construction.
**Key Interfaces:**
- `TestGraphBuilderUnresolved` - A test case class validating the unresolved reference tracking logic of the graph builder across different languages.
- `test_captures_unresolved_references(self): None` - Asserts that invalid TypeScript relative/absolute imports are correctly flagged as unresolved while valid internal/external dependencies are resolved.
- `test_python_unresolved(self): None` - Asserts that invalid Python relative imports are correctly captured as unresolved references.
**Dependencies:** `unittest`, `src.analysis.graph_builder.GraphBuilder`, `src.core.types.FileEntry`

---

### `tests/unit/test_ignore_logic.py`
**Role:** Acts as a unit test suite to verify that the `FileSystemScanner` correctly applies exclusion rules to ignore specific directories during filesystem traversal.
**Key Interfaces:**
- `TestIgnoreLogic` - A `unittest.TestCase` class that defines the test environment and assertions for the scanner's ignore logic.
- `test_scanner_ignores(): None` - Evaluates the scanner's output against a mock filesystem structure to ensure excluded paths are successfully omitted.
**Dependencies:** `unittest`, `tempfile`, `shutil`, `os`, `src.scanner.filesystem_scanner.FileSystemScanner`

---

### `tests/unit/test_import_scanner.py`
**Role:** Acts as the unit testing suite for the `ImportScanner` service, verifying AST-based Python parsing, Regex-based JS/TS parsing, and system safety constraints for file handling.
**Key Interfaces:**
- `TestImportScanner` - Unit test suite responsible for validating import extraction, symbol detection, and boundary conditions (like file size limits and unknown languages) against the scanner.
- `functionName(params): ReturnType` - None
- `VariableName / TypeName` - None
**Dependencies:** `unittest`, `os`, `tempfile`, `shutil`, `src.analysis.import_scanner.ImportScanner`

---

### tests/unit/test_mermaid_exporter.py
**Role:** Acts as the unit test suite for the `MermaidExporter`, validating the generation of valid Mermaid markdown syntax, proper visual styling of dependency cycles, and the safe sanitization of node identifiers.
**Key Interfaces:**
- `TestMermaidExporter` - Unit test suite class verifying the graph rendering logic of the `MermaidExporter`.
- `test_basic_export_syntax(self): None` - Verifies that the exporter correctly transforms standard nodes, edges, and subgraphs into compliant Mermaid markdown files.
- `test_cycle_highlighting(self): None` - Verifies that cyclical dependencies in the graph structure correctly apply specific visual cycle classes and edge styling.
- `test_id_escaping(self): None` - Verifies that node IDs containing special characters are correctly sanitized to prevent breaking the Mermaid renderer.
**Dependencies:** `unittest`, `os`, `shutil`, `tempfile`, `src.exporters.mermaid_exporter`, `src.core.types`

---

### `tests/unit/test_path_normalizer.py`
**Role:** Serves as the unit test suite verifying the path parsing, structural resolution, casing policies, and standard ID generation logic of the `PathNormalizer` component.
**Key Interfaces:**
- `TestPathNormalizer` - Unit test class validating the structural and string-formatting behaviors of the path normalization logic.
- `None` - No public functions or shared state are exported for external consumption.
**Dependencies:** `unittest`, `os`, `src.normalize.path_normalizer.PathNormalizer`

---

### tests/unit/test_scanner_constants.py
**Role:** Verifies that the `ImportScanner` correctly extracts global constant symbols from source code across multiple languages like Python and TypeScript.
**Key Interfaces:**
- `TestScannerConstants` - Unit test class responsible for validating constant symbol extraction logic.
- `test_python_constants(self): None` - Validates that the scanner captures Python UPPER_CASE variables and ignores lowercase or mixed-case variables.
- `test_js_constants(self): None` - Validates that the scanner captures JavaScript/TypeScript UPPER_CASE `const` declarations and arrow functions while ignoring `let` or mixed-case variables.
- `test_python_assignment_unpacking(self): None` - Documents and verifies the scanner's current limitations regarding constants declared via tuple unpacking.
**Dependencies:** unittest, src.analysis.import_scanner.ImportScanner, tempfile, os, shutil

---

### `tests/unit/test_snapshot_comparator.py`
**Role:** Unit test suite responsible for verifying that the `SnapshotComparator` accurately detects state changes in files and dependency graphs between two project manifests.
**Key Interfaces:**
- `TestSnapshotComparator` - Test suite class verifying the snapshot diffing and comparison logic.
- `test_file_diffing(): None` - Asserts the correct identification of added, removed, and modified files by comparing `FileEntry` cryptographic hashes across snapshots.
- `test_graph_diffing(): None` - Asserts the accurate detection of newly introduced or removed architectural dependencies between different versions of a `GraphStructure`.
- `None` - No critical exported state, constants, or data structures.
**Dependencies:** `unittest`, `src.analysis.snapshot_comparator.SnapshotComparator`, `src.core.types`

---

### `tests/unit/test_snapshot_loader.py`
**Role:** Serves as an empty placeholder file intended for unit tests that will verify the functionality of the snapshot loading mechanism.
**Key Interfaces:**
- None
**Dependencies:** None

---

### `tests/unit/test_structure_builder.py`
**Role:** Unit test suite responsible for validating the logic of `StructureBuilder` as it constructs a repository schema hierarchy from file entries.
**Key Interfaces:**
- `TestStructureBuilder` - Test suite class verifying the structure generation process.
- `test_build_structure(): None` - Validates the conversion of a list of `FileEntry` models into a structured schema grouped by module paths.
**Dependencies:** `unittest`, `src.structure.structure_builder.StructureBuilder`, `src.core.types.FileEntry`

---

### `tests/unit/test_token_telemetry.py`
**Role:** Verifies the mathematical accuracy of file reduction, token estimation, and API cost calculations produced by the TokenTelemetry observability module.
**Key Interfaces:**
- `TestTokenTelemetry` - A unit test suite for validating telemetry metrics generation.
- `test_telemetry_calculations(): None` - Asserts the correctness of byte reductions, token counts, and cost estimations based on original and sliced manifest inputs.
**Dependencies:** `unittest`, `src.observability.token_telemetry.TokenTelemetry`

---

### tests/unit/test_types.py
**Role:** Serves as the unit test suite verifying the data validation and normalization behaviors of the core `FileEntry` domain model.
**Key Interfaces:**
- `TestTypes` - Unit test suite verifying schema constraints for the `FileEntry` data model.
- `test_path_normalization_validator(self): None` - Asserts that the `FileEntry` model automatically normalizes inconsistent file paths upon instantiation.
- `test_stable_id_validation(self): None` - Asserts that the `FileEntry` model correctly rejects improperly formatted stable identifiers.
- `State / Constants` - None
**Dependencies:** `unittest`, `pydantic`, `src.core.types`

---

