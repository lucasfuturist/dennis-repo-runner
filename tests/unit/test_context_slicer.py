import unittest
from src.analysis.context_slicer import ContextSlicer

class TestContextSlicer(unittest.TestCase):
    def setUp(self):
        # Mock Manifest
        self.manifest = {
            "files": [
                {"stable_id": "file:a.py"},
                {"stable_id": "file:b.py"},
                {"stable_id": "file:c.py"},
                {"stable_id": "file:d.py"}
            ],
            "stats": {"file_count": 4}
        }
        
        # Mock Graph representing a linear dependency chain: A -> B -> C -> D
        self.graph = {
            "nodes": [],
            "edges": [
                {"source": "file:a.py", "target": "file:b.py", "relation": "imports"},
                {"source": "file:b.py", "target": "file:c.py", "relation": "imports"},
                {"source": "file:c.py", "target": "file:d.py", "relation": "imports"}
            ]
        }

    def test_radius_zero(self):
        """Radius 0 = Only the focus file itself."""
        sliced = ContextSlicer.slice_manifest(self.manifest, self.graph, "file:b.py", radius=0)
        files = [f["stable_id"] for f in sliced["files"]]
        
        self.assertEqual(files, ["file:b.py"])
        self.assertEqual(sliced["stats"]["file_count"], 1)

    def test_radius_one_bidirectional(self):
        """
        Radius 1 = Focus file + immediate parents + immediate children.
        From B, it should grab A (parent) and C (child).
        """
        sliced = ContextSlicer.slice_manifest(self.manifest, self.graph, "file:b.py", radius=1)
        files = sorted([f["stable_id"] for f in sliced["files"]])
        
        self.assertEqual(files, ["file:a.py", "file:b.py", "file:c.py"])

    def test_radius_two(self):
        """
        Radius 2 from B should yield A, B, C, and branch out to D.
        """
        sliced = ContextSlicer.slice_manifest(self.manifest, self.graph, "file:b.py", radius=2)
        files = sorted([f["stable_id"] for f in sliced["files"]])
        
        self.assertEqual(files, ["file:a.py", "file:b.py", "file:c.py", "file:d.py"])

if __name__ == "__main__":
    unittest.main()