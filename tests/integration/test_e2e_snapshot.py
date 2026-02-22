import unittest
import tempfile
import shutil
import os
from src.core.controller import run_snapshot
from src.snapshot.snapshot_loader import SnapshotLoader

class TestFullSnapshot(unittest.TestCase):
    def setUp(self):
        # Resolve real path immediately to avoid Windows 8.3 short-path / relpath bugs
        self.test_dir = os.path.realpath(tempfile.mkdtemp())
        self.repo_root = os.path.join(self.test_dir, "my_repo")
        self.output_root = os.path.join(self.test_dir, "output")
        
        os.makedirs(self.repo_root)
        os.makedirs(self.output_root)

        self._create_file("README.md", "# Hello")
        self._create_file("src/main.py", "import os\nprint('hello')")
        self._create_file("src/utils.py", "def add(a,b): return a+b")
        self._create_file("node_modules/bad_file.js", "ignore me")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _create_file(self, path, content):
        full_path = os.path.join(self.repo_root, path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w") as f:
            f.write(content)

    def test_snapshot_creation_with_graph_and_auto_export(self):
        # 1. Run Snapshot with v0.2 features enabled
        snapshot_id = run_snapshot(
            repo_root=self.repo_root,
            output_root=self.output_root,
            depth=5,
            ignore=["node_modules"],
            include_extensions=[".py", ".md"],
            include_readme=True,
            write_current_pointer=True,
            skip_graph=False,
            export_flatten=True
        )

        snap_dir = os.path.join(self.output_root, snapshot_id)
        
        # 2. Verify Output Directory Structure
        self.assertTrue(os.path.isdir(snap_dir))
        self.assertTrue(os.path.isfile(os.path.join(snap_dir, "manifest.json")))
        self.assertTrue(os.path.isfile(os.path.join(snap_dir, "structure.json")))
        self.assertTrue(os.path.isfile(os.path.join(snap_dir, "graph.json")), "Graph should be generated")
        self.assertTrue(os.path.isfile(os.path.join(snap_dir, "exports", "flatten.md")), "Auto-export should exist")

        # 3. Verify Manifest Stats (External Deps)
        loader = SnapshotLoader(self.output_root)
        manifest = loader.load_manifest(snap_dir)
        stats = manifest["stats"]
        self.assertIn("os", stats.get("external_dependencies", []))

    def test_snapshot_skip_graph(self):
        # 1. Run Snapshot with Graph Skipped
        snapshot_id = run_snapshot(
            repo_root=self.repo_root,
            output_root=self.output_root,
            depth=5,
            ignore=["node_modules"],
            include_extensions=[".py", ".md"],
            include_readme=True,
            write_current_pointer=True,
            skip_graph=True,
            export_flatten=False
        )

        snap_dir = os.path.join(self.output_root, snapshot_id)
        
        # 2. Verify Graph Absence
        self.assertFalse(os.path.exists(os.path.join(snap_dir, "graph.json")), "Graph should NOT be generated")
        
        # 3. Verify Manifest Reflects Config
        loader = SnapshotLoader(self.output_root)
        manifest = loader.load_manifest(snap_dir)
        self.assertTrue(manifest["config"]["skip_graph"])
        self.assertEqual(manifest["stats"].get("external_dependencies", []), [])

if __name__ == "__main__":
    unittest.main()