import argparse
import os
from src.core.controller import run_snapshot, run_export_flatten

def _parse_args():
    parser = argparse.ArgumentParser(prog="repo-runner", description="repo-runner v0.2")
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
    snap.add_argument("--skip-graph", action="store_true", help="Skip dependency graph generation (faster)")
    snap.add_argument("--export-flatten", action="store_true", help="Automatically generate flatten.md export")

    # slice (NEW)
    slice_cmd = sub.add_parser("slice", help="Generate a context slice (Markdown) from a snapshot")
    slice_cmd.add_argument("--output-root", required=True, help="Output root directory where snapshots live")
    slice_cmd.add_argument("--repo-root", required=True, help="Repo root path (used to read file contents)")
    slice_cmd.add_argument("--snapshot-id", required=False, default=None, help="Snapshot ID (defaults to current)")
    slice_cmd.add_argument("--focus", required=True, help="Stable ID of the file to focus on (e.g. file:src/app.py)")
    slice_cmd.add_argument("--radius", type=int, default=1, help="Context radius (hops)")
    slice_cmd.add_argument("--max-tokens", type=int, default=None, help="Token budget limit")
    slice_cmd.add_argument("--output", required=False, default=None, help="Output path for the slice markdown")

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
            skip_graph=args.skip_graph,
            export_flatten=args.export_flatten,
        )
        
        abs_out = os.path.abspath(os.path.join(args.output_root, snap_id))
        print(f"Snapshot created:\n  {abs_out}")
        
        if args.export_flatten:
            abs_export = os.path.join(abs_out, "exports", "flatten.md")
            print(f"Auto-export flattened:\n  {abs_export}")
            
        return

    if args.command == "slice":
        out = run_export_flatten(
            output_root=args.output_root,
            repo_root=args.repo_root,
            snapshot_id=args.snapshot_id,
            output_path=args.output,
            tree_only=False,
            include_readme=True, # Usually we want context to include docs
            scope="full", # Slice handles pruning; we pass full scope to the exporter but with a pruned manifest
            title=f"Context Slice: {args.focus}",
            focus_id=args.focus,
            radius=args.radius,
            max_tokens=args.max_tokens
        )
        abs_out = os.path.abspath(out) if out else "None"
        print(f"Slice generated:\n  {abs_out}")
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
        abs_out = os.path.abspath(out)
        print(f"Wrote Export:\n  {abs_out}")
        return
    
    if args.command == "ui":
        from src.gui.app import run_gui
        run_gui()
        return

    raise RuntimeError("Unhandled command")


if __name__ == "__main__":
    main()