import unittest
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