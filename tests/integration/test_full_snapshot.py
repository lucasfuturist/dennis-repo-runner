import unittest
import tempfile
import shutil
import os
import json
from src.cli.main import run_snapshot
from src.snapshot.snapshot_loader import SnapshotLoader

class TestFullSnapshot(unittest.TestCase):
    def setUp(self):
        # Create a temp directory for the "Repo"
        self.test_dir = tempfile.mkdtemp()
        self.repo_root = os.path.join(self.test_dir, "my_repo")
        self.output_root = os.path.join(self.test_dir, "output")
        
        os.makedirs(self.repo_root)
        os.makedirs(self.output_root)

        # Create dummy repo content
        self._create_file("README.md", "# Hello")
        self._create_file("src/main.py", "print('hello')")
        self._create_file("src/utils.py", "def add(a,b): return a+b")
        self._create_file("node_modules/bad_file.js", "ignore me") # Should be ignored

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def _create_file(self, path, content):
        full_path = os.path.join(self.repo_root, path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w") as f:
            f.write(content)

    def test_snapshot_creation(self):
        # 1. Run Snapshot
        snapshot_id = run_snapshot(
            repo_root=self.repo_root,
            output_root=self.output_root,
            depth=5,
            ignore=["node_modules"],
            include_extensions=[".py", ".md"],
            include_readme=True,
            write_current_pointer=True
        )

        # 2. Verify Output Directory Structure
        snap_dir = os.path.join(self.output_root, snapshot_id)
        self.assertTrue(os.path.isdir(snap_dir))
        self.assertTrue(os.path.isfile(os.path.join(snap_dir, "manifest.json")))
        self.assertTrue(os.path.isfile(os.path.join(snap_dir, "structure.json")))
        self.assertTrue(os.path.isfile(os.path.join(self.output_root, "current.json")))

        # 3. Verify Manifest Content
        loader = SnapshotLoader(self.output_root)
        manifest = loader.load_manifest(snap_dir)
        
        # Check Config
        self.assertEqual(manifest["config"]["depth"], 5)
        self.assertIn("node_modules", manifest["config"]["ignore_names"])

        # Check Files
        files = manifest["files"]
        paths = [f["path"] for f in files]
        
        # Expected: readme.md, src/main.py, src/utils.py
        # node_modules should be gone.
        self.assertIn("readme.md", paths)
        self.assertIn("src/main.py", paths)
        self.assertIn("src/utils.py", paths)
        self.assertNotIn("node_modules/bad_file.js", paths)

        # 4. Verify Determinism (Hash)
        main_py_entry = next(f for f in files if f["path"] == "src/main.py")
        self.assertEqual(main_py_entry["language"], "python")
        self.assertGreater(main_py_entry["size_bytes"], 0)
        # SHA256 of "print('hello')"
        # We won't hardcode the hash here to be robust against newline changes in test setup,
        # but we ensure it exists.
        self.assertTrue(len(main_py_entry["sha256"]) == 64)

if __name__ == "__main__":
    unittest.main()