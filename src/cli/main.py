import argparse
import os
import sys
from src.core.controller import run_snapshot, run_export_flatten, run_compare
from src.core.config_loader import ConfigLoader

def _parse_args():
    parser = argparse.ArgumentParser(prog="repo-runner", description="repo-runner v0.2")
    sub = parser.add_subparsers(dest="command", required=True)

    # snapshot
    snap = sub.add_parser("snapshot", help="Create a deterministic structural snapshot")
    snap.add_argument("repo_root", help="Repository root path")
    snap.add_argument("--output-root", required=False, default=None, help="Output root directory")
    snap.add_argument("--depth", type=int, default=None)
    snap.add_argument("--ignore", nargs="*", default=None)
    snap.add_argument("--include-extensions", nargs="*", default=None)
    snap.add_argument("--include-readme", action="store_true", default=None)
    snap.add_argument("--no-include-readme", action="store_false", dest="include_readme")
    snap.add_argument("--write-current-pointer", action="store_true", default=None)
    snap.add_argument("--no-write-current-pointer", action="store_false", dest="write_current_pointer")
    snap.add_argument("--skip-graph", action="store_true", default=None)
    snap.add_argument("--no-skip-graph", action="store_false", dest="skip_graph")
    snap.add_argument("--export-flatten", action="store_true", default=None)
    snap.add_argument("--no-export-flatten", action="store_false", dest="export_flatten")

    # slice
    slice_cmd = sub.add_parser("slice", help="Generate a context slice (Markdown)")
    slice_cmd.add_argument("--repo-root", required=True)
    slice_cmd.add_argument("--output-root", required=False, default=None)
    slice_cmd.add_argument("--snapshot-id", required=False, default=None)
    slice_cmd.add_argument("--focus", required=True)
    slice_cmd.add_argument("--radius", type=int, default=1)
    slice_cmd.add_argument("--max-tokens", type=int, default=None)
    slice_cmd.add_argument("--output", required=False, default=None)

    # diff (NEW)
    diff_cmd = sub.add_parser("diff", help="Compare two structural snapshots")
    diff_cmd.add_argument("--base", required=True, help="Base snapshot ID or 'current'")
    diff_cmd.add_argument("--target", required=True, help="Target snapshot ID or 'current'")
    diff_cmd.add_argument("--output-root", required=False, default=None)
    # Allows locating repo-runner.json to find output-root if not provided
    diff_cmd.add_argument("--repo-root", required=False, default=".", help="Repo root to search for config")

    # export
    exp = sub.add_parser("export", help="Export derived artifacts")
    exp_sub = exp.add_subparsers(dest="export_command", required=True)
    flatten = exp_sub.add_parser("flatten")
    flatten.add_argument("--repo-root", required=True)
    flatten.add_argument("--output-root", required=False, default=None)
    flatten.add_argument("--snapshot-id", required=False, default=None)
    flatten.add_argument("--output", required=False, default=None)
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
        config = ConfigLoader.load_config(args.repo_root)
        output_root = args.output_root if args.output_root is not None else config.output_root
        if not output_root:
            print("Error: --output-root must be provided via CLI flag or 'repo-runner.json'")
            sys.exit(1)

        snap_id = run_snapshot(
            repo_root=args.repo_root,
            output_root=output_root,
            depth=args.depth if args.depth is not None else config.depth,
            ignore=args.ignore if args.ignore is not None else config.ignore,
            include_extensions=args.include_extensions if args.include_extensions is not None else config.include_extensions,
            include_readme=args.include_readme if args.include_readme is not None else config.include_readme,
            write_current_pointer=args.write_current_pointer if args.write_current_pointer is not None else True,
            skip_graph=args.skip_graph if args.skip_graph is not None else config.skip_graph,
            export_flatten=args.export_flatten if args.export_flatten is not None else config.export_flatten,
        )
        print(f"Snapshot created:\n  {os.path.abspath(os.path.join(output_root, snap_id))}")
        return

    if args.command == "diff":
        config = ConfigLoader.load_config(args.repo_root)
        output_root = args.output_root if args.output_root is not None else config.output_root
        if not output_root:
            print("Error: --output-root must be provided via CLI flag or 'repo-runner.json'")
            sys.exit(1)

        report = run_compare(output_root, args.base, args.target)
        
        print(f"\nStructural Diff: {report.base_snapshot_id} -> {report.target_snapshot_id}")
        print("="*60)
        print(f"Files:  +{report.files_added}  -{report.files_removed}  ~{report.files_modified}")
        print(f"Edges:  +{report.edges_added}  -{report.edges_removed}")
        print("-"*60)

        for fd in report.file_diffs:
            symbol = "  [~] " if fd.status == "modified" else "  [+] " if fd.status == "added" else "  [-] "
            print(f"{symbol}{fd.stable_id}")
            
        if report.edge_diffs:
            print("\nDependency Drift:")
            for ed in report.edge_diffs:
                symbol = "  (+) " if ed.status == "added" else "  (-) "
                print(f"{symbol}{ed.source} -> {ed.target}")
        print("="*60 + "\n")
        return

    if args.command == "slice":
        config = ConfigLoader.load_config(args.repo_root)
        output_root = args.output_root if args.output_root is not None else config.output_root
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
        print(f"Slice generated:\n  {os.path.abspath(out) if out else 'None'}")
        return

    if args.command == "export":
        config = ConfigLoader.load_config(args.repo_root)
        output_root = args.output_root if args.output_root is not None else config.output_root
        out = run_export_flatten(
            output_root=output_root,
            repo_root=args.repo_root,
            snapshot_id=args.snapshot_id,
            output_path=args.output,
            tree_only=args.tree_only,
            include_readme=args.include_readme if args.include_readme is not None else config.include_readme,
            scope=args.scope,
            title=args.title,
        )
        print(f"Wrote Export:\n  {os.path.abspath(out)}")
        return
    
    if args.command == "ui":
        from src.gui.app import run_gui
        run_gui()
        return

if __name__ == "__main__":
    main()