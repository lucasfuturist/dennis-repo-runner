# Module Export: core

- repo_root: `C:/projects/repo-runner`
- snapshot_id: `BATCH_EXPORT`
- file_count: `5`
- tree_only: `False`
## Tree

```
└── src
    └── core
        ├── __init__.py
        ├── config_loader.py
        ├── controller.py
        ├── repo-runner.code-workspace
        └── types.py
```

## File Contents

### `src/core/__init__.py`

```
# src/core/__init__.py
```

### `src/core/config_loader.py`

```
import os
import json
from typing import Optional
from src.core.types import RepoRunnerConfig

class ConfigLoader:
    """
    Locates and parses repo-runner.json project configuration files.
    """
    
    CONFIG_FILENAME = "repo-runner.json"

    @staticmethod
    def load_config(repo_root: str) -> RepoRunnerConfig:
        """
        Attempts to load the configuration from the target repository root.
        Returns a default RepoRunnerConfig if no file exists or if parsing fails.
        """
        config_path = os.path.join(repo_root, ConfigLoader.CONFIG_FILENAME)
        
        if not os.path.exists(config_path):
            return RepoRunnerConfig()
            
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return RepoRunnerConfig.model_validate(data)
        except json.JSONDecodeError as e:
            print(f"Warning: Invalid JSON in {config_path}. Using default configuration. Error: {e}")
            return RepoRunnerConfig()
        except Exception as e:
            print(f"Warning: Failed to load {config_path}. Using default configuration. Error: {e}")
            return RepoRunnerConfig()
```

### `src/core/controller.py`

```
import os
import time
import json
from collections import defaultdict
from typing import List, Optional, Set, Dict, Callable

from src.core.types import (
    Manifest, 
    FileEntry, 
    ManifestInputs, 
    ManifestConfig, 
    ManifestStats, 
    GitMetadata,
    GraphStructure,
    SnapshotDiffReport
)
from src.core.config_loader import ConfigLoader
from src.analysis.import_scanner import ImportScanner
from src.analysis.graph_builder import GraphBuilder
from src.analysis.context_slicer import ContextSlicer
from src.analysis.snapshot_comparator import SnapshotComparator
from src.observability.token_telemetry import TokenTelemetry
from src.exporters.flatten_markdown_exporter import (
    FlattenMarkdownExporter,
    FlattenOptions,
)
from src.exporters.mermaid_exporter import MermaidExporter
from src.exporters.drawio_exporter import DrawioExporter
from src.fingerprint.file_fingerprint import FileFingerprint
from src.normalize.path_normalizer import PathNormalizer
from src.scanner.filesystem_scanner import FileSystemScanner
from src.snapshot.snapshot_loader import SnapshotLoader
from src.snapshot.snapshot_writer import SnapshotWriter
from src.structure.structure_builder import StructureBuilder


def _filter_by_extensions(abs_files: List[str], include_exts: List[str]) -> List[str]:
    if not include_exts:
        return abs_files

    include = set([e.lower() for e in include_exts])
    out =[]

    for p in abs_files:
        ext = os.path.splitext(p)[1].lower()
        if ext in include:
            out.append(p)

    return out


def run_snapshot(
    repo_root: str,
    output_root: str,
    depth: int,
    ignore: List[str],
    include_extensions: List[str],
    include_readme: bool,
    write_current_pointer: bool,
    skip_graph: bool = False,
    explicit_file_list: Optional[List[str]] = None,
    export_flatten: bool = False,
    progress_callback: Optional[Callable[[str, int, int], None]] = None,
    manual_override: bool = False 
) -> str:
    """
    Creates a snapshot. Automatically ignores the output_root if it is inside the repo_root.
    Reports progress across 3 phases: Scanning, Fingerprinting, and Analysis.
    """
    repo_root_abs = os.path.abspath(repo_root)
    output_root_abs = os.path.abspath(output_root)

    if not os.path.isdir(repo_root_abs):
        raise ValueError(f"Repository root does not exist: {repo_root_abs}")

    # --- Self-Ignore Logic ---
    effective_ignore = set(ignore)
    try:
        if os.path.commonpath([repo_root_abs, output_root_abs]) == repo_root_abs:
            rel_to_out = os.path.relpath(output_root_abs, repo_root_abs)
            top_level_segment = rel_to_out.split(os.sep)[0]
            if top_level_segment and top_level_segment != '.':
                effective_ignore.add(top_level_segment)
    except ValueError:
        pass

    if explicit_file_list is not None:
        absolute_files =[os.path.abspath(f) for f in explicit_file_list]
    else:
        def scan_cb(count: int) -> bool:
            if progress_callback:
                progress_callback("Scanning Filesystem", count, 0)
            return True
            
        scanner = FileSystemScanner(depth=depth, ignore_names=list(effective_ignore))
        absolute_files = scanner.scan([repo_root_abs], progress_callback=scan_cb)
        absolute_files = _filter_by_extensions(absolute_files, include_extensions)

    normalizer = PathNormalizer(repo_root_abs)
    file_entries: List[FileEntry] =[]
    total_bytes = 0
    
    # COLLISION DETECTION STATE
    seen_ids: Dict[str, str] = {} 

    total_files = len(absolute_files)

    for i, abs_path in enumerate(absolute_files):
        # Progress Feedback for GUI/CLI
        if progress_callback and i % 10 == 0:
            progress_callback("Fingerprinting & Analysis", i, total_files)

        if not os.path.exists(abs_path):
            continue

        normalized = normalizer.normalize(abs_path)

        if explicit_file_list is None:
            if not include_readme and os.path.basename(normalized).lower().startswith("readme"):
                continue

        stable_id = normalizer.file_id(normalized)

        # COLLISION CHECK
        if stable_id in seen_ids:
            conflicting_path = seen_ids[stable_id]
            if explicit_file_list:
                if conflicting_path == abs_path:
                    continue
            
            raise ValueError(
                f"ID Collision Detected!\n"
                f"Stable ID: {stable_id}\n"
                f"Source 1: {conflicting_path}\n"
                f"Source 2: {abs_path}\n"
                f"Repo-runner enforces lowercase IDs. "
                f"Please rename one of these files to avoid ambiguity."
            )

        seen_ids[stable_id] = abs_path
        module_path = normalizer.module_path(normalized)
        
        try:
            fp = FileFingerprint.fingerprint(abs_path)
            total_bytes += fp["size_bytes"]
            
            # --- Analysis (Imports & Symbols) ---
            imports =[]
            symbols =[]
            if not skip_graph:
                try:
                    scan_res = ImportScanner.scan(abs_path, fp["language"])
                    imports = scan_res.get("imports",[])
                    symbols = scan_res.get("symbols",[])
                except Exception:
                    pass

            entry = FileEntry(
                stable_id=stable_id,
                path=normalized,
                module_path=module_path,
                sha256=fp["sha256"],
                size_bytes=fp["size_bytes"],
                language=fp["language"],
                imports=imports,
                symbols=symbols
            )
            file_entries.append(entry)
        except OSError:
            continue

    if progress_callback:
        progress_callback("Fingerprinting & Analysis", total_files, total_files)

    file_entries = sorted(file_entries, key=lambda x: x.path)

    if progress_callback:
        progress_callback("Building Graph & Structure", total_files, total_files)

    structure = StructureBuilder().build(
        repo_id=PathNormalizer.repo_id(),
        files=file_entries,
    )

    graph = None
    external_deps =[]

    if not skip_graph:
        graph = GraphBuilder().build(file_entries)
        if graph:
            external_deps = sorted([
                n.id.replace("external:", "") 
                for n in graph.nodes 
                if n.type == "external"
            ])
    # FIX: Removed the else block that was instantiating GraphStructure. 
    # SnapshotWriter expects None to skip file creation.

    symbols_index_raw = defaultdict(list)
    for entry in file_entries:
        for sym in entry.symbols:
            symbols_index_raw[sym].append(entry.stable_id)
            
    symbols_index = {
        sym: sorted(paths) 
        for sym, paths in sorted(symbols_index_raw.items())
    }

    timestamp = time.strftime("%Y-%m-%dT%H-%M-%SZ", time.gmtime())
    
    manifest = Manifest(
        tool={"name": "repo-runner", "version": "0.2.0"},
        snapshot={
            "snapshot_id": timestamp, 
            "created_utc": timestamp,
            "output_root": output_root_abs.replace("\\", "/")
        }, 
        inputs=ManifestInputs(
            repo_root=repo_root_abs.replace("\\", "/"),
            roots=[repo_root_abs.replace("\\", "/")],
            git=GitMetadata(
                is_repo=os.path.isdir(os.path.join(repo_root_abs, ".git")),
                commit=None
            )
        ),
        config=ManifestConfig(
            depth=depth,
            ignore_names=list(effective_ignore),
            include_extensions=include_extensions,
            include_readme=include_readme,
            tree_only=False,
            skip_graph=skip_graph,
            manual_override=explicit_file_list is not None or manual_override
        ),
        stats=ManifestStats(
            file_count=len(file_entries),
            total_bytes=total_bytes,
            external_dependencies=external_deps
        ),
        files=file_entries
    )

    writer = SnapshotWriter(output_root)
    snapshot_id = writer.write(
        manifest,
        structure,
        graph=graph,
        symbols=symbols_index,
        write_current_pointer=write_current_pointer
    )

    if export_flatten:
        exporter = FlattenMarkdownExporter()
        options = FlattenOptions(
            tree_only=False,
            include_readme=True,
            scope="full"
        )
        snapshot_dir = os.path.join(output_root, snapshot_id)
        
        exporter.export(
            repo_root=repo_root_abs,
            snapshot_dir=snapshot_dir,
            manifest=manifest.model_dump(mode='json'),
            output_path=None,
            options=options,
            title=f"Auto Export: {snapshot_id}"
        )

    return snapshot_id


def run_export_flatten(
    output_root: str,
    repo_root: str,
    snapshot_id: Optional[str],
    output_path: Optional[str],
    tree_only: bool,
    include_readme: bool,
    scope: str,
    title: Optional[str],
    focus_id: Optional[str] = None,
    radius: int = 1,
    max_tokens: Optional[int] = None,
    print_summary: bool = False
) -> str:
    """
    Exports a snapshot to Markdown.
    """
    loader = SnapshotLoader(output_root)
    snapshot_dir = loader.resolve_snapshot_dir(snapshot_id)
    manifest = loader.load_manifest(snapshot_dir)

    telemetry_md = None

    if focus_id:
        graph_path = os.path.join(snapshot_dir, "graph.json")
        if not os.path.exists(graph_path):
            raise FileNotFoundError(f"Cannot slice context: graph.json missing in {snapshot_dir}")
        
        with open(graph_path, "r") as f:
            graph_data = json.load(f)
            
        sliced_manifest = ContextSlicer.slice_manifest(
            manifest=manifest, 
            graph=graph_data, 
            focus_id=focus_id, 
            radius=radius,
            max_tokens=max_tokens
        )
        
        estimated = sliced_manifest.get("stats", {}).get("estimated_tokens", 0)
        usage_str = TokenTelemetry.format_usage(estimated, max_tokens or 0)
        cycles = sliced_manifest.get("stats", {}).get("cycles_included", 0)
        
        telemetry_md = f"""
## Context Telemetry
- **Focus:** `{focus_id}`
- **Radius:** {radius}
- **Usage:** {usage_str}
- **Cycles Included:** {cycles}
"""
        manifest = sliced_manifest
        
        if print_summary and "telemetry" in manifest:
            print("\n" + "="*45)
            print(" Context Slice Summary")
            print("="*45)
            print(f" Focus:    {manifest['telemetry']['focus_id']}")
            print(f" Resolved: {manifest['telemetry']['resolved_id']}")
            print(f" Radius:   {manifest['telemetry']['radius']} hops")
            print(f" Usage:    {usage_str}")
            print(f" Files:    {manifest['stats']['file_count']}")
            print(f" Cycles:   {cycles} captured")
            print("="*45 + "\n")

        if not title:
            title = f"Context Slice: {focus_id} (Radius: {radius})"

    exporter = FlattenMarkdownExporter()

    options = FlattenOptions(
        tree_only=tree_only,
        include_readme=include_readme,
        scope=scope,
    )

    out_path = exporter.export(
        repo_root=os.path.abspath(repo_root),
        snapshot_dir=snapshot_dir,
        manifest=manifest,
        output_path=output_path,
        options=options,
        title=title,
    )

    if telemetry_md and out_path and os.path.exists(out_path):
        with open(out_path, 'r', encoding='utf-8') as f:
            content = f.read()
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(telemetry_md + "\n\n" + content)

    return out_path


def run_export_diagram(
    output_root: str,
    repo_root: str,
    snapshot_id: Optional[str],
    output_path: Optional[str],
    title: Optional[str],
    format: str = "mermaid"
) -> str:
    """
    Orchestrates the creation of a visual diagram from an existing snapshot.
    """
    loader = SnapshotLoader(output_root)
    snapshot_dir = loader.resolve_snapshot_dir(snapshot_id)
    
    graph_path = os.path.join(snapshot_dir, "graph.json")
    if not os.path.exists(graph_path):
        raise FileNotFoundError(f"graph.json not found in {snapshot_dir}. Cannot generate diagram.")
        
    with open(graph_path, "r") as f:
        graph_data = json.load(f)
        
    graph = GraphStructure.model_validate(graph_data)
    
    if format == "mermaid":
        exporter = MermaidExporter()
    elif format == "drawio":
        exporter = DrawioExporter()
    else:
        raise ValueError(f"Unknown format: {format}")
        
    return exporter.export(snapshot_dir, graph, output_path, title)


def run_compare(
    output_root: str,
    base_id: str,
    target_id: str
) -> SnapshotDiffReport:
    """
    Loads two snapshots and performs a structural diff.
    """
    loader = SnapshotLoader(output_root)
    
    dir_a = loader.resolve_snapshot_dir(base_id)
    dir_b = loader.resolve_snapshot_dir(target_id)
    
    manifest_a = Manifest.model_validate(loader.load_manifest(dir_a))
    manifest_b = Manifest.model_validate(loader.load_manifest(dir_b))
    
    ga_path = os.path.join(dir_a, "graph.json")
    gb_path = os.path.join(dir_b, "graph.json")
    
    g_a, g_b = None, None
    if os.path.exists(ga_path):
        with open(ga_path, "r") as f:
            g_a = GraphStructure.model_validate(json.load(f))
    if os.path.exists(gb_path):
        with open(gb_path, "r") as f:
            g_b = GraphStructure.model_validate(json.load(f))

    return SnapshotComparator.compare(manifest_a, manifest_b, g_a, g_b)
```

### `src/core/repo-runner.code-workspace`

```
<<BINARY_OR_SKIPPED_FILE>>
size_bytes: 0
sha256: pre-snapshot
```

### `src/core/types.py`

```
from typing import List, Optional, Set, Any, Dict
from pydantic import BaseModel, Field, field_validator

class RepoRunnerConfig(BaseModel):
    """
    Schema for repo-runner.json configuration files.
    Defines system-wide defaults for snapshot runs.
    """
    output_root: Optional[str] = None
    depth: int = 25
    ignore: List[str] = [".git", "node_modules", "__pycache__", "dist", "build", ".next", ".expo", ".venv"]
    include_extensions: List[str] = Field(default_factory=list)
    include_readme: bool = True
    skip_graph: bool = False
    export_flatten: bool = False

class FileEntry(BaseModel):
    """
    Represents a single file in the snapshot.
    Enforces path normalization strategies at the model level.
    """
    path: str
    stable_id: str
    module_path: str
    sha256: str
    size_bytes: int
    language: str = "unknown"
    imports: List[str] = Field(default_factory=list)
    symbols: List[str] = Field(default_factory=list) 

    @field_validator('path', 'module_path')
    @classmethod
    def validate_path_normalization(cls, v: str) -> str:
        """
        Enforces that all paths stored in the system are:
        1. Forward-slash separated
        2. Lowercase (for case-insensitive consistency)
        """
        if not v:
            return v
        return v.replace('\\', '/').lower()

    @field_validator('stable_id')
    @classmethod
    def validate_stable_id(cls, v: str) -> str:
        if not v.startswith(('file:', 'module:', 'repo:', 'external:')):
             raise ValueError(f"Invalid stable_id format: {v}")
        return v.lower()


class GraphNode(BaseModel):
    id: str
    type: str  # 'file' | 'module' | 'external'
    metadata: Optional[Any] = None

class GraphEdge(BaseModel):
    source: str
    target: str
    relation: str = "imports"

class UnresolvedReference(BaseModel):
    """
    Represents an import statement that could not be resolved to 
    a file node OR a canonical external package.
    Commonly caused by broken relative paths or typos.
    """
    source: str
    import_ref: str

class GraphStructure(BaseModel):
    schema_version: str = "1.1" # Bumped from 1.0 for new field
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    cycles: List[List[str]] = Field(default_factory=list)
    has_cycles: bool = False
    
    # New in v1.1: Track broken links instead of silently dropping them
    unresolved_references: List[UnresolvedReference] = Field(default_factory=list)

class ManifestStats(BaseModel):
    file_count: int
    total_bytes: int
    external_dependencies: List[str] = Field(default_factory=list)

class GitMetadata(BaseModel):
    is_repo: bool
    commit: Optional[str] = None

class ManifestInputs(BaseModel):
    repo_root: str
    roots: List[str]
    git: GitMetadata

class ManifestConfig(BaseModel):
    depth: int
    ignore_names: List[str]
    include_extensions: List[str]
    include_readme: bool
    tree_only: bool
    skip_graph: bool
    manual_override: bool

class Manifest(BaseModel):
    schema_version: str = "1.0"
    tool: dict
    snapshot: dict
    inputs: ManifestInputs
    config: ManifestConfig
    stats: ManifestStats
    files: List[FileEntry]

# --- Structural Diff Models ---

class FileDiff(BaseModel):
    stable_id: str
    status: str # 'added', 'removed', 'modified'
    old_sha256: Optional[str] = None
    new_sha256: Optional[str] = None

class EdgeDiff(BaseModel):
    source: str
    target: str
    relation: str
    status: str # 'added', 'removed'

class SnapshotDiffReport(BaseModel):
    base_snapshot_id: str
    target_snapshot_id: str
    files_added: int = 0
    files_removed: int = 0
    files_modified: int = 0
    edges_added: int = 0
    edges_removed: int = 0
    file_diffs: List[FileDiff] = Field(default_factory=list)
    edge_diffs: List[EdgeDiff] = Field(default_factory=list)
```

---
## Context Stats
- **Total Characters:** 19,460
- **Estimated Tokens:** ~4,865 (assuming ~4 chars/token)
- **Model Fit:** GPT-4 (8k)
