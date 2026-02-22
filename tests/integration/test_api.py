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
        os.makedirs(self.repo_root, exist_ok=True)
        os.makedirs(self.output_root, exist_ok=True)
        
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

    def test_slice_with_token_limit(self):
        """
        Tests that setting max_tokens strictly limits the returned files.
        """
        # Create a heavy dependency chain: A -> B (Heavy)
        self._create_file("a.py", "import b")
        # 1 token ~= 4 chars. Create ~1000 tokens (4000 chars)
        self._create_file("b.py", "#" * 4000) 

        # Snapshot
        resp = self.client.post("/snapshots", json={
            "repo_root": self.repo_root,
            "output_root": self.output_root,
            "include_extensions": [".py"]
        })
        snap_id = resp.json()["snapshot_id"]

        # Request slice with small limit (e.g. 50 tokens)
        # Should include A (focus, small) but EXCLUDE B (too big)
        slice_resp = self.client.post(f"/snapshots/{snap_id}/slice", json={
            "output_root": self.output_root,
            "focus_id": "file:a.py",
            "radius": 1,
            "max_tokens": 50
        })
        
        data = slice_resp.json()
        files = [f["stable_id"] for f in data["sliced_manifest"]["files"]]
        
        self.assertIn("file:a.py", files)
        self.assertNotIn("file:b.py", files)
        
        # Telemetry should reflect the drop
        self.assertIn("Usage:", data["telemetry_markdown"])
        # Estimated tokens should be low (just A)
        stats = data["sliced_manifest"]["stats"]
        self.assertTrue(stats["estimated_tokens"] < 100)

if __name__ == "__main__":
    unittest.main()