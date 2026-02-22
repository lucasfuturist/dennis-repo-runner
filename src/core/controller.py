import os
import json
from typing import List, Optional, Set

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
from src.analysis.import_scanner import ImportScanner
from src.analysis.graph_builder import GraphBuilder
from src.analysis.context_slicer import ContextSlicer
from src.analysis.snapshot_comparator import SnapshotComparator
from src.observability.token_telemetry import TokenTelemetry
from src.exporters.flatten_markdown_exporter import (
    FlattenMarkdownExporter,
    FlattenOptions,
)
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
    out = []

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
) -> str:
    """
    Creates a snapshot. Automatically ignores the output_root if it is inside the repo_root.
    """
    repo_root_abs = os.path.abspath(repo_root)
    output_root_abs = os.path.abspath(output_root)

    if not os.path.isdir(repo_root_abs):
        raise ValueError(f"Repository root does not exist: {repo_root_abs}")

    # --- Self-Ignore Logic ---
    # If the output directory is inside the repository, we must ignore it
    # to avoid recursive snapshots and noise in diffs.
    effective_ignore = set(ignore)
    try:
        # Check if output_root is a child of repo_root
        if os.path.commonpath([repo_root_abs, output_root_abs]) == repo_root_abs:
            rel_to_out = os.path.relpath(output_root_abs, repo_root_abs)
            # We ignore the top-level segment of the output path relative to repo root
            # e.g., if output is 'out/snapshots', we ignore 'out'
            top_level_segment = rel_to_out.split(os.sep)[0]
            if top_level_segment and top_level_segment != '.':
                effective_ignore.add(top_level_segment)
    except ValueError:
        # Handles cases on Windows where paths are on different drives
        pass

    if explicit_file_list is not None:
        absolute_files = [os.path.abspath(f) for f in explicit_file_list]
    else:
        # Scanner uses the effective_ignore set which now includes the output folder
        scanner = FileSystemScanner(depth=depth, ignore_names=effective_ignore)
        absolute_files = scanner.scan([repo_root_abs])
        absolute_files = _filter_by_extensions(absolute_files, include_extensions)

    normalizer = PathNormalizer(repo_root_abs)
    file_entries: List[FileEntry] = []
    total_bytes = 0
    seen_ids: Set[str] = set()

    for abs_path in absolute_files:
        if not os.path.exists(abs_path):
            continue

        normalized = normalizer.normalize(abs_path)

        if explicit_file_list is None:
            if not include_readme and os.path.basename(normalized).lower().startswith("readme"):
                continue

        stable_id = normalizer.file_id(normalized)

        if stable_id in seen_ids:
            if explicit_file_list:
                continue
            raise RuntimeError(f"Path collision after normalization: {stable_id}")

        seen_ids.add(stable_id)
        module_path = normalizer.module_path(normalized)
        
        try:
            fp = FileFingerprint.fingerprint(abs_path)
            total_bytes += fp["size_bytes"]
            
            try:
                scan_res = ImportScanner.scan(abs_path, fp["language"])
                imports = scan_res.get("imports", [])
                symbols = scan_res.get("symbols", [])
            except Exception:
                imports = []
                symbols = []

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

    file_entries = sorted(file_entries, key=lambda x: x.path)

    structure = StructureBuilder().build(
        repo_id=PathNormalizer.repo_id(),
        files=file_entries,
    )

    graph = None
    external_deps = []

    if not skip_graph:
        graph = GraphBuilder().build(file_entries)
        external_deps = sorted([
            n.id.replace("external:", "") 
            for n in graph.nodes 
            if n.type == "external"
        ])

    manifest = Manifest(
        tool={"name": "repo-runner", "version": "0.2.0"},
        snapshot={}, 
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
            manual_override=explicit_file_list is not None
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
        write_current_pointer=write_current_pointer,
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
    max_tokens: Optional[int] = None
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