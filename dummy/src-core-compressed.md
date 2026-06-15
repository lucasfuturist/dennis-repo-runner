# Module: src/core

> *Direct compressed architectural slice, excluding raw implementation code.*

## Module Directory Tree

```text
.
└── src/
    └── core/
        ├── __init__.py
        ├── config_loader.py
        ├── controller.py
        ├── repo-runner.code-workspace
        └── types.py
```

---

### `src/core/__init__.py`
**Role:** Initializes the core directory as a Python package.
**Key Interfaces:**
- None
**Dependencies:** None

---

### src/core/config_loader.py
**Role:** Responsible for locating, parsing, and validating the repository's JSON configuration file into a strongly-typed data model.
**Key Interfaces:**
- `ConfigLoader` - Static utility class serving as the configuration resolution mechanism.
- `load_config(repo_root: str): RepoRunnerConfig` - Accepts a repository root directory path and returns the parsed (or default) configuration object.
- `CONFIG_FILENAME / str` - Constant defining the expected configuration file name.
**Dependencies:** os, json, typing, src.core.types.RepoRunnerConfig

---

### `src/core/controller.py`
**Role:** Orchestrates the primary application workflows including repository snapshot generation, architecture graph building, snapshot diffing, file exporting, and direct LLM-based context compression.
**Key Interfaces:**
- `run_snapshot(repo_root, output_root, depth, ignore, include_extensions, include_readme, write_current_pointer, skip_graph, explicit_file_list, export_flatten, progress_callback, manual_override): str` - Executes the pipeline to scan the filesystem, fingerprint files, build relationship graphs, write the manifest via SnapshotWriter, and returns the snapshot ID.
- `run_export_flatten(output_root, repo_root, snapshot_id, output_path, tree_only, include_readme, scope, title, focus_id, radius, max_tokens, print_summary): str` - Processes a snapshot via SnapshotLoader and ContextSlicer to export a flattened Markdown document, returning the output file path.
- `run_export_diagram(output_root, repo_root, snapshot_id, output_path, title, format): str` - Generates a visual architecture diagram (Mermaid or Drawio) from a loaded snapshot graph and returns the exported file path.
- `run_compare(output_root, base_id, target_id): SnapshotDiffReport` - Evaluates structural differences between two loaded snapshots via SnapshotComparator and returns the detailed diff report.
- `run_export_compression_state(output_root, base_id, target_id, state_dir): Dict[str, Any]` - Calculates incremental state updates for LLM compression queues based on snapshot diffs and returns execution statistics.
- `run_batch_module_compression_stateless(repo_root, selected_modules, export_dir, model, delay, progress_callback): Dict[str, str]` - Utilizes the external Gemini API to generate structural summaries for selected codebase modules and returns a mapping of modules to their exported file paths.
**Dependencies:** src.core.types, src.core.config_loader, src.analysis.import_scanner, src.analysis.graph_builder, src.analysis.context_slicer, src.analysis.snapshot_comparator, src.observability.token_telemetry, src.exporters.flatten_markdown_exporter, src.exporters.mermaid_exporter, src.exporters.drawio_exporter, src.fingerprint.file_fingerprint, src.normalize.path_normalizer, src.scanner.filesystem_scanner, src.snapshot.snapshot_loader, src.snapshot.snapshot_writer, src.structure.structure_builder, google.genai, dotenv

---

### `src/core/repo-runner.code-workspace`
**Role:** Configures the VS Code multi-root workspace environment to simultaneously load the primary codebase and the external generated `repo-runner-output` directory.
**Key Interfaces:**
- `folders` - Configures the array of relative directory paths included in the IDE workspace.
- `settings` - Defines workspace-level editor configuration and overrides.
**Dependencies:** None

---

### `src/core/types.py`
**Role:** This file serves as the central domain model and schema definition layer, utilizing Pydantic to enforce data validation for configurations, repository snapshots, dependency graphs, and structural diffs.
**Key Interfaces:**
- `RepoRunnerConfig` - Pydantic model defining system-wide configuration defaults and ignore rules for snapshot runs.
- `FileEntry` - Pydantic model representing a normalized, hashed, and validated file entity within the repository snapshot.
- `GraphNode` - Pydantic model representing a vertex (file, module, or external) in the dependency graph.
- `GraphEdge` - Pydantic model representing a directed relationship (e.g., imports) between two graph nodes.
- `UnresolvedReference` - Pydantic model tracking import references that fail to map to a valid file or external package.
- `GraphStructure` - Pydantic model defining the complete dependency graph, encompassing nodes, edges, cycle detection, and unresolved references.
- `ManifestStats` - Pydantic model aggregating high-level snapshot statistics like file count, size, and external dependencies.
- `GitMetadata` - Pydantic model tracking the git repository status and commit hash associated with a snapshot.
- `ManifestInputs` - Pydantic model specifying the directory roots and metadata used to generate the manifest.
- `ManifestConfig` - Pydantic model capturing the configuration state applied during the snapshot generation.
- `Manifest` - Pydantic model representing the complete, hierarchical state of a repository snapshot.
- `FileDiff` - Pydantic model tracking the addition, removal, or modification of a file between two snapshots.
- `EdgeDiff` - Pydantic model tracking the addition or removal of dependency graph edges between two snapshots.
- `SnapshotDiffReport` - Pydantic model aggregating overall diff statistics and granular file/edge diffs to compare two repository snapshots.
**Dependencies:** typing, pydantic

---

