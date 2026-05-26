import argparse
import os
import sys
from typing import List
from src.core.controller import (
    run_snapshot, 
    run_export_flatten, 
    run_compare, 
    run_export_diagram, 
    run_export_compression_state,
    run_batch_module_compression_stateless
)
from src.core.config_loader import ConfigLoader
from src.scanner.filesystem_scanner import FileSystemScanner
from src.normalize.path_normalizer import PathNormalizer

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

    # diff
    diff_cmd = sub.add_parser("diff", help="Compare two structural snapshots")
    diff_cmd.add_argument("--base", required=True, help="Base snapshot ID or 'current'")
    diff_cmd.add_argument("--target", required=True, help="Target snapshot ID or 'current'")
    diff_cmd.add_argument("--output-root", required=False, default=None)
    diff_cmd.add_argument("--repo-root", required=False, default=".", help="Repo root to search for config")

    # diagram 
    diag_cmd = sub.add_parser("diagram", help="Generate a visual architecture diagram")
    diag_cmd.add_argument("--repo-root", required=True)
    diag_cmd.add_argument("--output-root", required=False, default=None)
    diag_cmd.add_argument("--snapshot-id", required=False, default=None)
    diag_cmd.add_argument("--output", required=False, default=None)
    diag_cmd.add_argument("--title", required=False, default=None)
    diag_cmd.add_argument("--format", choices=["mermaid", "drawio"], default="mermaid", help="Output format (default: mermaid)")

    # export
    exp = sub.add_parser("export", help="Export derived artifacts")
    exp_sub = exp.add_subparsers(dest="export_command", required=True)
    
    # export flatten
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

    # export compression-state
    comp_state = exp_sub.add_parser("compression-state", help="Sync incremental context compression states")
    comp_state.add_argument("--base", required=True, help="Base snapshot ID, 'current', or 'empty'")
    comp_state.add_argument("--target", required=True, help="Target snapshot ID or 'current'")
    comp_state.add_argument("--state-dir", required=True, help="Directory to store JSON state files")
    comp_state.add_argument("--output-root", required=False, default=None)
    comp_state.add_argument("--repo-root", required=False, default=".")

    # export batch-compress
    batch_comp = exp_sub.add_parser("batch-compress", help="Perform direct stateless batch module compression")
    batch_comp.add_argument("--repo-root", required=True, help="Path to repository root")
    batch_comp.add_argument("--modules", nargs="+", required=True, help="Relative paths of modules/directories to compress")
    batch_comp.add_argument("--output-dir", required=True, help="Directory where compressed outputs will be saved")
    batch_comp.add_argument("--model", default="gemini-3.1-pro-preview", help="Gemini model to use")
    batch_comp.add_argument("--delay", type=float, default=2.0, help="Delay (seconds) between API calls")

    # ui
    sub.add_parser("ui", help="Launch the graphical control panel")

    return parser.parse_args()


def cli_progress(phase: str, current: int, total: int):
    """
    Renders an over-writable progress line suitable for standard terminals.
    """
    if total > 0:
        msg = f"[repo-runner] {phase}: {current}/{total}"
    else:
        msg = f"[repo-runner] {phase}: {current} files found..."
    
    sys.stdout.write(f"\r{msg:<70}")
    sys.stdout.flush()


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
            progress_callback=cli_progress
        )
        print(f"\nSnapshot created:\n  {os.path.abspath(os.path.join(output_root, snap_id))}")
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
            max_tokens=args.max_tokens,
            print_summary=True
        )
        print(f"Slice generated:\n  {os.path.abspath(out) if out else 'None'}")
        return

    if args.command == "diagram":
        config = ConfigLoader.load_config(args.repo_root)
        output_root = args.output_root if args.output_root is not None else config.output_root
        if not output_root:
            print("Error: --output-root must be provided via CLI flag or 'repo-runner.json'")
            sys.exit(1)

        out = run_export_diagram(
            output_root=output_root,
            repo_root=args.repo_root,
            snapshot_id=args.snapshot_id,
            output_path=args.output,
            title=args.title,
            format=args.format
        )
        print(f"Diagram generated ({args.format}):\n  {os.path.abspath(out)}")
        return

    if args.command == "export":
        config = ConfigLoader.load_config(args.repo_root)

        if args.export_command == "flatten":
            output_root = args.output_root if args.output_root is not None else config.output_root
            if not output_root:
                print("Error: --output-root must be provided via CLI flag or 'repo-runner.json'")
                sys.exit(1)

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
            
        elif args.export_command == "compression-state":
            output_root = args.output_root if args.output_root is not None else config.output_root
            if not output_root:
                print("Error: --output-root must be provided via CLI flag or 'repo-runner.json'")
                sys.exit(1)

            stats = run_export_compression_state(
                output_root=output_root,
                base_id=args.base,
                target_id=args.target,
                state_dir=args.state_dir
            )
            print(f"Compression State Synced in {os.path.abspath(args.state_dir)}")
            print(f"  Pending LLM Compression: {stats['pending_compression']} files")
            return

        elif args.export_command == "batch-compress":
            selected_modules = {}
            for rel_mod in args.modules:
                abs_mod_dir = os.path.normpath(os.path.join(args.repo_root, rel_mod))
                if not os.path.isdir(abs_mod_dir):
                    print(f"\nError: Module directory does not exist: {abs_mod_dir}")
                    sys.exit(1)
                
                # Fetch targets using core settings scanner
                scanner = FileSystemScanner(depth=config.depth, ignore_names=config.ignore)
                abs_files = scanner.scan([abs_mod_dir])
                abs_files = _filter_by_extensions(abs_files, config.include_extensions)

                if abs_files:
                    selected_modules[rel_mod] = abs_files

            if not selected_modules:
                print("\nError: No valid files matched in the selected modules.")
                sys.exit(1)

            print(f"Stateless batch compressing {len(selected_modules)} modules...")

            exported_paths = run_batch_module_compression_stateless(
                repo_root=args.repo_root,
                selected_modules=selected_modules,
                export_dir=args.output_dir,
                model=args.model,
                delay=args.delay,
                progress_callback=cli_progress
            )

            print(f"\n\nBatch Export Complete. Successfully wrote {len(exported_paths)} module files:")
            for path in sorted(exported_paths.values()):
                print(f"  - {os.path.abspath(path)}")
            return
    
    if args.command == "ui":
        from src.gui.app import run_gui
        run_gui()
        return

if __name__ == "__main__":
    main()