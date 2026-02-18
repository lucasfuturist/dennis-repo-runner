import argparse
import os
from typing import List, Optional

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


def _parse_args():
    parser = argparse.ArgumentParser(prog="repo-runner", description="repo-runner v0.1")
    sub = parser.add_subparsers(dest="command", required=True)

    # snapshot
    snap = sub.add_parser("snapshot", help="Create a deterministic structural snapshot")
    snap.add_argument("repo_root", help="Repository root path")
    snap.add_argument("--output-root", required=True, help="Output root directory for snapshots")
    snap.add_argument("--depth", type=int, default=25)
    snap.add_argument(
        "--ignore",
        nargs="*",
        default=[".git", "node_modules", "__pycache__", "dist", "build", ".next", ".expo", ".venv"],
    )
    snap.add_argument("--include-extensions", nargs="*", default=[])
    snap.add_argument("--include-readme", action="store_true", default=True)
    snap.add_argument("--no-include-readme", action="store_false", dest="include_readme")
    snap.add_argument("--write-current-pointer", action="store_true", default=True)
    snap.add_argument("--no-write-current-pointer", action="store_false", dest="write_current_pointer")

    # export
    exp = sub.add_parser("export", help="Export derived artifacts from a snapshot")
    exp_sub = exp.add_subparsers(dest="export_command", required=True)

    flatten = exp_sub.add_parser(
        "flatten",
        help="Generate deterministic flatten markdown (list_tree alternative)",
    )
    flatten.add_argument("--output-root", required=True, help="Output root directory where snapshots live")
    flatten.add_argument(
        "--snapshot-id",
        required=False,
        default=None,
        help="Snapshot id to export from (defaults to current)",
    )
    flatten.add_argument("--repo-root", required=True, help="Repo root path (used to read file contents)")
    flatten.add_argument(
        "--output",
        required=False,
        default=None,
        help="Output path for markdown (defaults to snapshot exports/flatten.md)",
    )
    flatten.add_argument("--tree-only", action="store_true", default=False)
    flatten.add_argument("--include-readme", action="store_true", default=True)
    flatten.add_argument("--no-include-readme", action="store_false", dest="include_readme")
    flatten.add_argument("--scope", required=False, default="full")
    flatten.add_argument("--title", required=False, default=None)

    # ui
    sub.add_parser("ui", help="Launch the graphical control panel")

    return parser.parse_args()


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
) -> str:
    """
    Creates a snapshot.
    If explicit_file_list is provided, it skips the directory scan and uses that exact list.
    """
    repo_root_abs = os.path.abspath(repo_root)

    if explicit_file_list is not None:
        # UI Override Mode: Use the list exactly as provided
        absolute_files = [os.path.abspath(f) for f in explicit_file_list]
    else:
        # CLI / Default Mode: Scan the disk
        scanner = FileSystemScanner(depth=depth, ignore_names=set(ignore))
        absolute_files = scanner.scan([repo_root_abs])
        absolute_files = _filter_by_extensions(absolute_files, include_extensions)

    normalizer = PathNormalizer(repo_root_abs)
    file_entries = []
    total_bytes = 0
    seen_ids = set()

    for abs_path in absolute_files:
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
        
        # Fingerprint might fail if file was deleted between scan and click
        try:
            fp = FileFingerprint.fingerprint(abs_path)
            total_bytes += fp["size_bytes"]
            
            file_entries.append(
                {
                    "stable_id": stable_id,
                    "path": normalized,
                    "module_path": module_path,
                    **fp,
                }
            )
        except OSError:
            # If a file is unreadable or deleted, we skip it
            continue

    file_entries = sorted(file_entries, key=lambda x: x["path"])

    structure = StructureBuilder().build(
        repo_id=PathNormalizer.repo_id(),
        files=file_entries,
    )

    manifest = {
        "schema_version": "1.0",
        "tool": {"name": "repo-runner", "version": "0.1.0"},
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
        },
        "files": file_entries,
    }

    writer = SnapshotWriter(output_root)
    snapshot_id = writer.write(
        manifest,
        structure,
        write_current_pointer=write_current_pointer,
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


def main():
    args = _parse_args()

    if args.command == "snapshot":
        snap_id = run_snapshot(
            repo_root=args.repo_root,
            output_root=args.output_root,
            depth=args.depth,
            ignore=args.ignore,
            include_extensions=args.include_extensions,
            include_readme=args.include_readme,
            write_current_pointer=args.write_current_pointer,
        )
        print(f"Snapshot created: {snap_id}")
        return

    if args.command == "export" and args.export_command == "flatten":
        out = run_export_flatten(
            output_root=args.output_root,
            repo_root=args.repo_root,
            snapshot_id=args.snapshot_id,
            output_path=args.output,
            tree_only=args.tree_only,
            include_readme=args.include_readme,
            scope=args.scope,
            title=args.title,
        )
        print(f"Wrote: {out}")
        return
    
    if args.command == "ui":
        from src.gui.app import run_gui
        run_gui()
        return

    raise RuntimeError("Unhandled command")


if __name__ == "__main__":
    main()