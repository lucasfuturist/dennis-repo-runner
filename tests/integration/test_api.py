import unittest
import tempfile
import shutil
import os
import time
from fastapi.testclient import TestClient

# Must import the FastAPI app instance
from src.api.server import app

class TestAPI(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.realpath(tempfile.mkdtemp())
        self.repo_root = os.path.join(self.test_dir, "repo")
        self.output_root = os.path.join(self.test_dir, "output")
        os.makedirs(self.repo_root)
        os.makedirs(self.output_root)
        
        # Setup test client
        self.client = TestClient(app)

    def tearDown(self):
        try:
            shutil.rmtree(self.test_dir)
        except OSError:
            pass

    def _create_file(self, rel_path, content):
        path = os.path.join(self.repo_root, rel_path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(content)

    def test_full_api_lifecycle(self):
        """
        Tests the entire lifecycle: Create Snapshot -> Slice Context -> Compare
        """
        # 1. Setup initial repo state
        self._create_file("main.py", "import utils\nprint('hello')")
        self._create_file("utils.py", "def helper(): pass")

        # 2. Test POST /snapshots (v1)
        response_v1 = self.client.post("/snapshots", json={
            "repo_root": self.repo_root,
            "output_root": self.output_root,
            "include_extensions": [".py"]
        })
        self.assertEqual(response_v1.status_code, 200)
        snap_v1_id = response_v1.json()["snapshot_id"]

        # 3. Test POST /snapshots/{id}/slice
        slice_resp = self.client.post(f"/snapshots/{snap_v1_id}/slice", json={
            "output_root": self.output_root,
            "focus_id": "file:main.py",
            "radius": 1
        })
        self.assertEqual(slice_resp.status_code, 200)
        slice_data = slice_resp.json()
        self.assertIn("telemetry_markdown", slice_data)
        
        # Ensure 'utils.py' is pulled into context via the 'main.py' import edge
        sliced_files = [f["stable_id"] for f in slice_data["sliced_manifest"]["files"]]
        self.assertIn("file:utils.py", sliced_files)

        # 4. Mutate the Repo (Remove utils, add config)
        os.remove(os.path.join(self.repo_root, "utils.py"))
        self._create_file("main.py", "import config\nprint('hello v2')") # modified
        self._create_file("config.py", "ENV='prod'") # added

        # FIX: Sleep for >1 second to ensure the second snapshot gets a unique timestamp ID
        time.sleep(1.1)

        # 5. Test POST /snapshots (v2)
        response_v2 = self.client.post("/snapshots", json={
            "repo_root": self.repo_root,
            "output_root": self.output_root,
            "include_extensions": [".py"]
        })
        snap_v2_id = response_v2.json()["snapshot_id"]
        
        # Verify IDs are actually different
        self.assertNotEqual(snap_v1_id, snap_v2_id, "Snapshots executed too fast, IDs collided.")

        # 6. Test POST /snapshots/compare
        compare_resp = self.client.post("/snapshots/compare", json={
            "output_root": self.output_root,
            "base_id": snap_v1_id,
            "target_id": snap_v2_id
        })
        self.assertEqual(compare_resp.status_code, 200)
        diff_report = compare_resp.json()

        # Validate Structural Diff matches our OS mutations
        self.assertEqual(diff_report["files_added"], 1)     # config.py
        self.assertEqual(diff_report["files_removed"], 1)   # utils.py
        self.assertEqual(diff_report["files_modified"], 1)  # main.py
        
        # Validate Dependency Graph Diff matches our code mutations
        self.assertTrue(diff_report["edges_added"] > 0)     # Edge to config added
        self.assertTrue(diff_report["edges_removed"] > 0)   # Edge to utils removed

if __name__ == "__main__":
    unittest.main()