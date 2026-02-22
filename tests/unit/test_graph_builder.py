import unittest
from src.analysis.graph_builder import GraphBuilder
from src.core.types import FileEntry

class TestGraphBuilder(unittest.TestCase):
    def setUp(self):
        self.builder = GraphBuilder()

    def test_scoped_and_deep_external_packages(self):
        """Test that deep imports collapse to root packages, preserving NPM scopes."""
        files = [
            FileEntry(
                stable_id="file:src/app.ts",
                path="src/app.ts",
                language="typescript",
                # Imports testing various JS ecosystem quirks
                imports=[
                    "@mui/material/Button",  # Scoped + Subpath
                    "lodash/fp/map",         # Unscoped + Subpath
                    "@angular/core",         # Scoped strict
                    "react"                  # Unscoped strict
                ], 
                module_path="src",
                sha256="abc", 
                size_bytes=100
            )
        ]
        
        graph = self.builder.build(files)
        
        # NOTE: Pydantic models use attribute access (graph.nodes), not dict lookup
        node_ids = set(n.id for n in graph.nodes)
        
        # Ensure deep paths are collapsed to the canonical package name
        self.assertIn("external:@mui/material", node_ids)
        self.assertIn("external:lodash", node_ids)
        self.assertIn("external:@angular/core", node_ids)
        self.assertIn("external:react", node_ids)
        
        # Ensure raw paths aren't leaked
        self.assertNotIn("external:@mui/material/Button", node_ids)
        self.assertNotIn("external:lodash/fp/map", node_ids)

    def test_graph_determinism(self):
        """Test that Graph output is perfectly sorted regardless of input order."""
        # Define common kwargs to keep code clean
        common = {"module_path": ".", "sha256": "abc", "size_bytes": 0}

        files_a = [
            FileEntry(stable_id="file:b.py", path="b.py", language="python", imports=["z_ext", "a_ext"], **common),
            FileEntry(stable_id="file:a.py", path="a.py", language="python", imports=["m_ext"], **common),
        ]
        
        # Reversed input list and reversed import arrays
        files_b = [
            FileEntry(stable_id="file:a.py", path="a.py", language="python", imports=["m_ext"], **common),
            FileEntry(stable_id="file:b.py", path="b.py", language="python", imports=["a_ext", "z_ext"], **common),
        ]
        
        graph_a = self.builder.build(files_a)
        graph_b = self.builder.build(files_b)
        
        # Pydantic models support direct equality comparison
        self.assertEqual(graph_a, graph_b)
        
        # Verify specific sorting rules
        self.assertEqual(graph_a.nodes[0].id, "external:a_ext")
        self.assertEqual(graph_a.nodes[-1].id, "file:b.py")

    def test_cycle_detection_simple(self):
        """Test simple A <-> B cycle."""
        common = {"module_path": ".", "sha256": "abc", "size_bytes": 0, "language": "python"}
        files = [
            FileEntry(stable_id="file:a.py", path="a.py", imports=["b"], **common),
            FileEntry(stable_id="file:b.py", path="b.py", imports=["a"], **common),
        ]
        graph = self.builder.build(files)
        
        self.assertEqual(len(graph.cycles), 1)
        self.assertTrue(graph.has_cycles)
        # Cycle should be normalized to start with lowest ID
        self.assertEqual(graph.cycles[0], ["file:a.py", "file:b.py"])

    def test_cycle_detection_self_loop(self):
        """Test A -> A cycle."""
        common = {"module_path": ".", "sha256": "abc", "size_bytes": 0, "language": "python"}
        files = [
            FileEntry(stable_id="file:a.py", path="a.py", imports=["a"], **common),
        ]
        graph = self.builder.build(files)
        
        self.assertEqual(len(graph.cycles), 1)
        self.assertTrue(graph.has_cycles)
        self.assertEqual(graph.cycles[0], ["file:a.py"])

    def test_cycle_detection_triangular(self):
        """Test A -> B -> C -> A cycle."""
        common = {"module_path": ".", "sha256": "abc", "size_bytes": 0, "language": "python"}
        files = [
            FileEntry(stable_id="file:a.py", path="a.py", imports=["b"], **common),
            FileEntry(stable_id="file:b.py", path="b.py", imports=["c"], **common),
            FileEntry(stable_id="file:c.py", path="c.py", imports=["a"], **common),
        ]
        graph = self.builder.build(files)
        
        self.assertEqual(len(graph.cycles), 1)
        self.assertTrue(graph.has_cycles)
        # Should be sorted: a -> b -> c
        self.assertEqual(graph.cycles[0], ["file:a.py", "file:b.py", "file:c.py"])

    def test_no_false_positive_diamond(self):
        """Test Diamond (A->B, A->C, B->D, C->D) is NOT a cycle."""
        common = {"module_path": ".", "sha256": "abc", "size_bytes": 0, "language": "python"}
        files = [
            FileEntry(stable_id="file:a.py", path="a.py", imports=["b", "c"], **common),
            FileEntry(stable_id="file:b.py", path="b.py", imports=["d"], **common),
            FileEntry(stable_id="file:c.py", path="c.py", imports=["d"], **common),
            FileEntry(stable_id="file:d.py", path="d.py", imports=[], **common),
        ]
        graph = self.builder.build(files)
        
        self.assertEqual(len(graph.cycles), 0)
        self.assertFalse(graph.has_cycles)

if __name__ == "__main__":
    unittest.main()