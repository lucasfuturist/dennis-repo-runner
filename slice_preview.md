
## Context Telemetry
- **Focus:** `file:src/cli/main.py`
- **Radius:** 1
- **Usage:** 4687/5000 tokens (93.7%)
- **Cycles Included:** 0


# Context Slice: file:src/cli/main.py

- repo_root: `C:\projects\repo-runner`
- snapshot_id: `2026-02-22T19-14-09Z`
- file_count: `5`
- tree_only: `False`
## Tree

```
├── src
│   ├── cli
│   │   └── main.py
│   ├── core
│   │   └── controller.py
│   └── entry_point.py
└── tests
    ├── integration
    │   └── test_snapshot_flow.py
    └── unit
        └── test_cli_slice.py
```

## File Contents

### `src/cli/main.py`

```
﻿import argparse
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
```

### `src/core/controller.py`

```
import os
import json
from typing import List, Optional, Set

from src.core.types import (
    Manifest, 
    FileEntry, 
    ManifestInputs, 
    ManifestConfig, 
    ManifestStats, 
    GitMetadata
)
from src.analysis.import_scanner import ImportScanner
from src.analysis.graph_builder import GraphBuilder
from src.analysis.context_slicer import ContextSlicer
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
    Creates a snapshot.
    """
    repo_root_abs = os.path.abspath(repo_root)

    if not os.path.isdir(repo_root_abs):
        raise ValueError(f"Repository root does not exist: {repo_root_abs}")

    if explicit_file_list is not None:
        absolute_files = [os.path.abspath(f) for f in explicit_file_list]
    else:
        scanner = FileSystemScanner(depth=depth, ignore_names=set(ignore))
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
                imports = ImportScanner.scan(abs_path, fp["language"])
            except Exception:
                imports = []

            entry = FileEntry(
                stable_id=stable_id,
                path=normalized,
                module_path=module_path,
                sha256=fp["sha256"],
                size_bytes=fp["size_bytes"],
                language=fp["language"],
                imports=imports
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
            ignore_names=ignore,
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
    max_tokens: Optional[int] = None # NEW ARG
) -> str:
    """
    Exports a snapshot to Markdown.
    Injects Token Telemetry header if Context Slicing is utilized.
    """
    loader = SnapshotLoader(output_root)
    snapshot_dir = loader.resolve_snapshot_dir(snapshot_id)
    manifest = loader.load_manifest(snapshot_dir)

    telemetry_md = None

    # Context Slicing & Telemetry Layer
    if focus_id:
        graph_path = os.path.join(snapshot_dir, "graph.json")
        if not os.path.exists(graph_path):
            raise FileNotFoundError(f"Cannot slice context: graph.json missing in {snapshot_dir}")
        
        with open(graph_path, "r") as f:
            graph_data = json.load(f)
            
        # Pass max_tokens to slicer
        sliced_manifest = ContextSlicer.slice_manifest(
            manifest=manifest, 
            graph=graph_data, 
            focus_id=focus_id, 
            radius=radius,
            max_tokens=max_tokens
        )
        
        # Telemetry: Use sliced manifest stats for accurate reporting
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

    # Prepend Telemetry Header to the final file
    if telemetry_md and out_path and os.path.exists(out_path):
        with open(out_path, 'r', encoding='utf-8') as f:
            content = f.read()
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(telemetry_md + "\n\n" + content)

    return out_path
```

### `src/entry_point.py`

```
# src/entry_point.py
import sys
import multiprocessing

if sys.platform.startswith('win'):
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

def launch():
    if len(sys.argv) > 1:
        from src.cli.main import main
        main()
    else:
        from src.gui.app import run_gui
        run_gui()

if __name__ == "__main__":
    multiprocessing.freeze_support()
    launch()
```

### `tests/integration/test_snapshot_flow.py`

```
﻿import unittest
import tempfile
import shutil
import os
from src.cli.main import run_snapshot
from src.snapshot.snapshot_loader import SnapshotLoader

class TestSnapshotFlow(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.realpath(tempfile.mkdtemp())
        self.repo_root = os.path.join(self.test_dir, "my_repo")
        self.output_root = os.path.join(self.test_dir, "output")
        os.makedirs(self.repo_root)
        os.makedirs(self.output_root)

        self._create_file("README.md", "# Hello")
        self._create_file("src/main.py", "print('hello')")
        self._create_file("node_modules/bad_file.js", "ignore me")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _create_file(self, path, content):
        full_path = os.path.join(self.repo_root, path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w") as f:
            f.write(content)

    def test_snapshot_creation(self):
        snapshot_id = run_snapshot(
            repo_root=self.repo_root,
            output_root=self.output_root,
            depth=5,
            ignore=["node_modules"],
            include_extensions=[".py", ".md"],
            include_readme=True,
            write_current_pointer=True,
            skip_graph=True
        )

        snap_dir = os.path.join(self.output_root, snapshot_id)
        self.assertTrue(os.path.isdir(snap_dir))
        self.assertTrue(os.path.isfile(os.path.join(snap_dir, "manifest.json")))

        loader = SnapshotLoader(self.output_root)
        manifest = loader.load_manifest(snap_dir)
        
        paths = [f["path"] for f in manifest["files"]]
        self.assertIn("readme.md", paths)
        self.assertIn("src/main.py", paths)
        self.assertNotIn("node_modules/bad_file.js", paths)

if __name__ == "__main__":
    unittest.main()
```

### `tests/unit/test_cli_slice.py`

```
import unittest
from unittest.mock import patch, MagicMock
from src.cli.main import _parse_args, main
import sys

class TestCLISlice(unittest.TestCase):
    
    @patch('src.cli.main.run_export_flatten')
    def test_slice_command_invocation(self, mock_export):
        """
        Verify that `repo-runner slice` parses args correctly and calls the controller.
        """
        # Mock sys.argv
        test_args = [
            "slice",
            "--output-root", "./out",
            "--repo-root", "./repo",
            "--focus", "file:src/app.py",
            "--radius", "2",
            "--max-tokens", "5000"
        ]
        
        with patch.object(sys, 'argv', ["repo-runner"] + test_args):
            # Run main, which calls _parse_args internally
            main()
            
            # Assert controller was called with correct types
            mock_export.assert_called_once()
            _, kwargs = mock_export.call_args
            
            self.assertEqual(kwargs["focus_id"], "file:src/app.py")
            self.assertEqual(kwargs["radius"], 2)
            self.assertEqual(kwargs["max_tokens"], 5000)
            self.assertEqual(kwargs["repo_root"], "./repo")

    @patch('src.cli.main.run_export_flatten')
    def test_slice_defaults(self, mock_export):
        """
        Verify default values for radius and max_tokens.
        """
        test_args = [
            "slice",
            "--output-root", "./out",
            "--repo-root", "./repo",
            "--focus", "file:main.py"
        ]
        
        with patch.object(sys, 'argv', ["repo-runner"] + test_args):
            main()
            
            _, kwargs = mock_export.call_args
            self.assertEqual(kwargs["radius"], 1) # Default
            self.assertIsNone(kwargs["max_tokens"]) # Default None

if __name__ == "__main__":
    unittest.main()
```

---
## Context Stats
- **Total Characters:** 19,012
- **Estimated Tokens:** ~4,753 (assuming ~4 chars/token)
- **Model Fit:** GPT-4 (8k)
v