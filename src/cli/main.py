import argparse
from src.core.controller import run_snapshot, run_export_flatten

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
    snap.add_argument("--export-flatten", action="store_true", help="Automatically generate flatten.md export")

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
            export_flatten=args.export_flatten,
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