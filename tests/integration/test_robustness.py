import unittest
import tempfile
import shutil
import os
import sys
from src.core.controller import run_snapshot
from src.snapshot.snapshot_loader import SnapshotLoader

class TestRobustness(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_root = os.path.join(self.test_dir, "repo")
        self.output_root = os.path.join(self.test_dir, "output")
        os.makedirs(self.repo_root)
        os.makedirs(self.output_root)

    def tearDown(self):
        try:
            shutil.rmtree(self.test_dir)
        except OSError:
            pass

    def test_snapshot_with_mixed_health(self):
        # 1. Valid Files
        with open(os.path.join(self.repo_root, "valid.py"), "w") as f:
            f.write("print('ok')")
            
        # 2. Ignored Files
        os.makedirs(os.path.join(self.repo_root, "node_modules"))
        with open(os.path.join(self.repo_root, "node_modules", "ignore.js"), "w") as f:
            f.write("ignore")

        # 3. Symlink Cycle (Unix only)
        if sys.platform != 'win32':
            os.symlink(self.repo_root, os.path.join(self.repo_root, "loop"))

        # Run Snapshot
        # This should succeed despite the complexity
        snap_id = run_snapshot(
            repo_root=self.repo_root,
            output_root=self.output_root,
            depth=10,
            ignore=["node_modules"],
            include_extensions=[],
            include_readme=True,
            write_current_pointer=True
        )

        # Verify Manifest
        loader = SnapshotLoader(self.output_root)
        manifest = loader.load_manifest(os.path.join(self.output_root, snap_id))
        
        files = manifest["files"]
        paths = [f["path"] for f in files]
        
        self.assertIn("valid.py", paths)
        self.assertNotIn("node_modules/ignore.js", paths)
        
        # Ensure we didn't index the loop infinitely
        # The loop link itself might be skipped or included as a file depending on classification,
        # but the cycle must be broken.
        loop_matches = [p for p in paths if "loop" in p]
        self.assertLess(len(loop_matches), 2)

if __name__ == "__main__":
    unittest.main()