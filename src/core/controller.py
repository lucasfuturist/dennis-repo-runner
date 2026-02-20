import os
from typing import List, Optional, Set

from src.core.types import Manifest, FileEntry
from src.analysis.import_scanner import ImportScanner
from src.analysis.graph_builder import GraphBuilder
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
    explicit_file_list: Optional[List[str]] = None,
    export_flatten: bool = False,
) -> str:
    """
    Creates a snapshot.
    If explicit_file_list is provided, it skips the directory scan and uses that exact list.
    """
    repo_root_abs = os.path.abspath(repo_root)

    # FAIL FAST: If the repo root doesn't exist, stop immediately.
    if not os.path.isdir(repo_root_abs):
        raise ValueError(f"Repository root does not exist or is not a directory: {repo_root_abs}")

    if explicit_file_list is not None:
        # UI Override Mode: Use the list exactly as provided
        absolute_files = [os.path.abspath(f) for f in explicit_file_list]
    else:
        # CLI / Default Mode: Scan the disk
        scanner = FileSystemScanner(depth=depth, ignore_names=set(ignore))
        absolute_files = scanner.scan([repo_root_abs])
        absolute_files = _filter_by_extensions(absolute_files, include_extensions)

    normalizer = PathNormalizer(repo_root_abs)
    file_entries: List[FileEntry] = []
    total_bytes = 0
    seen_ids: Set[str] = set()

    for abs_path in absolute_files:
        # Hardening: Check if file still exists before processing
        if not os.path.exists(abs_path):
            continue

        normalized = normalizer.normalize(abs_path)

        # In override mode, we assume the user already selected what they want, 
        # but we still respect the readme flag if scanning.
        if explicit_file_list is None:
            if not include_readme and os.path.basename(normalized).lower().startswith("readme"):
                continue

        stable_id = normalizer.file_id(normalized)

        if stable_id in seen_ids:
            # In explicit mode, we warn/skip instead of crashing to be robust to UI quirks
            if explicit_file_list:
                continue
            raise RuntimeError(f"Path collision after normalization: {stable_id}")

        seen_ids.add(stable_id)

        module_path = normalizer.module_path(normalized)
        
        # Fingerprint might fail if file was deleted between scan and click,
        # or if it is locked/unreadable.
        try:
            fp = FileFingerprint.fingerprint(abs_path)
            total_bytes += fp["size_bytes"]
            
            # Analyze Imports
            # If import scanning fails, we default to empty list rather than crashing
            try:
                imports = ImportScanner.scan(abs_path, fp["language"])
            except Exception:
                imports = []

            entry: FileEntry = {
                "stable_id": stable_id,
                "path": normalized,
                "module_path": module_path,
                "sha256": fp["sha256"],
                "size_bytes": fp["size_bytes"],
                "language": fp["language"],
                "imports": imports
            }
            file_entries.append(entry)
        except OSError:
            # File unreadable, locked, or vanished. Skip.
            continue

    file_entries = sorted(file_entries, key=lambda x: x["path"])

    # 1. Build Containment Structure
    structure = StructureBuilder().build(
        repo_id=PathNormalizer.repo_id(),
        files=file_entries,
    )

    # 2. Build Dependency Graph
    graph = GraphBuilder().build(file_entries)

    # Extract external dependencies for Manifest stats
    external_deps = sorted([
        n["id"].replace("external:", "") 
        for n in graph["nodes"] 
        if n["type"] == "external"
    ])

    # 3. Assemble Manifest
    manifest: Manifest = {
        "schema_version": "1.0",
        "tool": {"name": "repo-runner", "version": "0.2.0"},
        "inputs": {
            "repo_root": repo_root_abs.replace("\\", "/"),
            "roots": [repo_root_abs.replace("\\", "/")],
            "git": {
                "is_repo": os.path.isdir(os.path.join(repo_root_abs, ".git")),
                "commit": None,
            },
        },
        "config": {
            "depth": depth,
            "ignore_names": ignore,
            "include_extensions": include_extensions,
            "include_readme": include_readme,
            "tree_only": False,
            "manual_override": explicit_file_list is not None
        },
        "stats": {
            "file_count": len(file_entries),
            "total_bytes": total_bytes,
            "external_dependencies": external_deps
        },
        "files": file_entries,
        "snapshot": {} # Populated by SnapshotWriter
    }

    # 4. Write Snapshot
    writer = SnapshotWriter(output_root)
    snapshot_id = writer.write(
        manifest,
        structure,
        graph=graph,
        write_current_pointer=write_current_pointer,
    )

    # 5. Optional Auto-Export
    if export_flatten:
        exporter = FlattenMarkdownExporter()
        # Default options for auto-export
        options = FlattenOptions(
            tree_only=False,
            include_readme=True,
            scope="full"
        )
        snapshot_dir = os.path.join(output_root, snapshot_id)
        
        # We reuse the manifest we just built to avoid re-reading from disk
        exporter.export(
            repo_root=repo_root_abs,
            snapshot_dir=snapshot_dir,
            manifest=manifest,
            output_path=None, # Uses default: exports/flatten.md
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
) -> str:
    loader = SnapshotLoader(output_root)
    snapshot_dir = loader.resolve_snapshot_dir(snapshot_id)
    manifest = loader.load_manifest(snapshot_dir)

    exporter = FlattenMarkdownExporter()

    options = FlattenOptions(
        tree_only=tree_only,
        include_readme=include_readme,
        scope=scope,
    )

    return exporter.export(
        repo_root=os.path.abspath(repo_root),
        snapshot_dir=snapshot_dir,
        manifest=manifest,
        output_path=output_path,
        options=options,
        title=title,
    )