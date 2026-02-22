import unittest
from src.analysis.context_slicer import ContextSlicer
from src.core.types import FileEntry

class TestContextSlicer(unittest.TestCase):
    def setUp(self):
        # 1 token ~= 4 bytes. 
        # File A: 40 bytes -> 10 tokens
        # File B: 40 bytes -> 10 tokens
        # File C: 400 bytes -> 100 tokens
        self.manifest = {
            "files": [
                {"stable_id": "file:a.py", "size_bytes": 40},
                {"stable_id": "file:b.py", "size_bytes": 40},
                {"stable_id": "file:c.py", "size_bytes": 400},
                {"stable_id": "file:d.py", "size_bytes": 40}
            ],
            "stats": {"file_count": 4}
        }
        
        # A <-> B (Cycle), B -> C -> D
        # Adjacency (Bidirectional):
        # A: [B]
        # B: [A, C]
        # C: [B, D]
        # D: [C]
        self.graph = {
            "nodes": [],
            "edges": [
                {"source": "file:a.py", "target": "file:b.py", "relation": "imports"},
                {"source": "file:b.py", "target": "file:a.py", "relation": "imports"},
                {"source": "file:b.py", "target": "file:c.py", "relation": "imports"},
                {"source": "file:c.py", "target": "file:d.py", "relation": "imports"}
            ],
            "cycles": [
                ["file:a.py", "file:b.py"]
            ]
        }

    def test_radius_logic_standard(self):
        """Standard radius checks without token limits."""
        sliced = ContextSlicer.slice_manifest(self.manifest, self.graph, "file:b.py", radius=1)
        files = sorted([f["stable_id"] for f in sliced["files"]])
        # Neighbors of B are A (parent) and C (child).
        self.assertEqual(files, ["file:a.py", "file:b.py", "file:c.py"])

    def test_token_budget_enforcement(self):
        """
        Focus B (10 tokens). Neighbors A (10) and C (100).
        Limit = 50.
        Should include B (10) + A (10) = 20.
        Should EXCLUDE C (100) because 20 + 100 > 50.
        """
        sliced = ContextSlicer.slice_manifest(
            self.manifest, 
            self.graph, 
            "file:b.py", 
            radius=1, 
            max_tokens=50
        )
        files = sorted([f["stable_id"] for f in sliced["files"]])
        
        self.assertIn("file:b.py", files) # Focus
        self.assertIn("file:a.py", files) # Fits in budget
        self.assertNotIn("file:c.py", files) # Too big
        
        self.assertTrue(sliced["stats"]["estimated_tokens"] <= 50)

    def test_focus_exceeds_budget(self):
        """
        Focus C (100 tokens). Limit = 50.
        Must still include C (Focus rule).
        """
        sliced = ContextSlicer.slice_manifest(
            self.manifest, 
            self.graph, 
            "file:c.py", 
            radius=1, 
            max_tokens=50
        )
        files = [f["stable_id"] for f in sliced["files"]]
        self.assertEqual(files, ["file:c.py"])
        self.assertEqual(sliced["stats"]["estimated_tokens"], 100)

    def test_cycle_stats_reporting(self):
        """
        Slice including A and B should report 1 cycle included.
        """
        sliced = ContextSlicer.slice_manifest(
            self.manifest, 
            self.graph, 
            "file:a.py", 
            radius=1
        )
        # Should include A and B
        self.assertEqual(sliced["stats"]["cycles_included"], 1)

    def test_cycle_stats_exclusion(self):
        """
        Slice D (leaf). Radius 1.
        Neighbors: C.
        Cycle (A, B) is at distance 2 from C, so dist 3 from D.
        Should be clean.
        """
        sliced = ContextSlicer.slice_manifest(
            self.manifest, 
            self.graph, 
            "file:d.py", 
            radius=1
        )
        self.assertEqual(sliced["stats"]["cycles_included"], 0)

if __name__ == "__main__":
    unittest.main()