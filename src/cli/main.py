import argparse
import os
import sys
from src.core.controller import run_snapshot, run_export_flatten
from src.core.config_loader import ConfigLoader

def _parse_args():
    parser = argparse.ArgumentParser(prog="repo-runner", description="repo-runner v0.2")
    sub = parser.add_subparsers(dest="command", required=True)

    # snapshot
    snap = sub.add_parser("snapshot", help="Create a deterministic structural snapshot")
    snap.add_argument("repo_root", help="Repository root path")
    snap.add_argument("--output-root", required=False, default=None, help="Output root directory for snapshots")
    snap.add_argument("--depth", type=int, default=None)
    snap.add_argument("--ignore", nargs="*", default=None)
    snap.add_argument("--include-extensions", nargs="*", default=None)
    
    # Boolean overrides (default None allows us to detect if user passed them)
    snap.add_argument("--include-readme", action="store_true", default=None)
    snap.add_argument("--no-include-readme", action="store_false", dest="include_readme")
    
    snap.add_argument("--write-current-pointer", action="store_true", default=None)
    snap.add_argument("--no-write-current-pointer", action="store_false", dest="write_current_pointer")
    
    snap.add_argument("--skip-graph", action="store_true", default=None, help="Skip dependency graph generation (faster)")
    snap.add_argument("--no-skip-graph", action="store_false", dest="skip_graph")
    
    snap.add_argument("--export-flatten", action="store_true", default=None, help="Automatically generate flatten.md export")
    snap.add_argument("--no-export-flatten", action="store_false", dest="export_flatten")


    # slice
    slice_cmd = sub.add_parser("slice", help="Generate a context slice (Markdown) from a snapshot")
    slice_cmd.add_argument("--repo-root", required=True, help="Repo root path (used to read file contents)")
    slice_cmd.add_argument("--output-root", required=False, default=None, help="Output root directory where snapshots live")
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
    flatten.add_argument("--repo-root", required=True, help="Repo root path (used to read file contents)")
    flatten.add_argument("--output-root", required=False, default=None, help="Output root directory where snapshots live")
    flatten.add_argument(
        "--snapshot-id",
        required=False,
        default=None,
        help="Snapshot id to export from (defaults to current)",
    )
    flatten.add_argument(
        "--output",
        required=False,
        default=None,
        help="Output path for markdown (defaults to snapshot exports/flatten.md)",
    )
    flatten.add_argument("--tree-only", action="store_true", default=False)
    flatten.add_argument("--include-readme", action="store_true", default=None)
    flatten.add_argument("--no-include-readme", action="store_false", dest="include_readme")
    flatten.add_argument("--scope", required=False, default="full")
    flatten.add_argument("--title", required=False, default=None)

    # ui
    sub.add_parser("ui", help="Launch the graphical control panel")

    return parser.parse_args()


def main():
    args = _parse_args()

    if args.command == "snapshot":
        # Merge config
        config = ConfigLoader.load_config(args.repo_root)
        
        output_root = args.output_root if args.output_root is not None else config.output_root
        if not output_root:
            print("Error: --output-root must be provided via CLI flag or 'repo-runner.json'")
            sys.exit(1)

        depth = args.depth if args.depth is not None else config.depth
        ignore = args.ignore if args.ignore is not None else config.ignore
        include_extensions = args.include_extensions if args.include_extensions is not None else config.include_extensions
        include_readme = args.include_readme if args.include_readme is not None else config.include_readme
        skip_graph = args.skip_graph if args.skip_graph is not None else config.skip_graph
        export_flatten = args.export_flatten if args.export_flatten is not None else config.export_flatten
        
        # Pointer write logic is specific to runtime, defaults to True if not specified
        write_current = args.write_current_pointer if args.write_current_pointer is not None else True

        snap_id = run_snapshot(
            repo_root=args.repo_root,
            output_root=output_root,
            depth=depth,
            ignore=ignore,
            include_extensions=include_extensions,
            include_readme=include_readme,
            write_current_pointer=write_current,
            skip_graph=skip_graph,
            export_flatten=export_flatten,
        )
        
        abs_out = os.path.abspath(os.path.join(output_root, snap_id))
        print(f"Snapshot created:\n  {abs_out}")
        
        if export_flatten:
            abs_export = os.path.join(abs_out, "exports", "flatten.md")
            print(f"Auto-export flattened:\n  {abs_export}")
            
        return

    if args.command == "slice":
        config = ConfigLoader.load_config(args.repo_root)
        output_root = args.output_root if args.output_root is not None else config.output_root
        if not output_root:
            print("Error: --output-root must be provided via CLI flag or 'repo-runner.json'")
            sys.exit(1)
            
        out = run_export_flatten(
            output_root=output_root,
            repo_root=args.repo_root,
            snapshot_id=args.snapshot_id,
            output_path=args.output,
            tree_only=False,
            include_readme=True,
            scope="full", 
            title=f"Context Slice: {args.focus}",
            focus_id=args.focus,
            radius=args.radius,
            max_tokens=args.max_tokens
        )
        abs_out = os.path.abspath(out) if out else "None"
        print(f"Slice generated:\n  {abs_out}")
        return

    if args.command == "export" and args.export_command == "flatten":
        config = ConfigLoader.load_config(args.repo_root)
        output_root = args.output_root if args.output_root is not None else config.output_root
        if not output_root:
            print("Error: --output-root must be provided via CLI flag or 'repo-runner.json'")
            sys.exit(1)
            
        include_readme = args.include_readme if args.include_readme is not None else config.include_readme
            
        out = run_export_flatten(
            output_root=output_root,
            repo_root=args.repo_root,
            snapshot_id=args.snapshot_id,
            output_path=args.output,
            tree_only=args.tree_only,
            include_readme=include_readme,
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