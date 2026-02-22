import unittest
from src.analysis.graph_builder import GraphBuilder
from src.core.types import FileEntry

class TestGraphBuilder(unittest.TestCase):
    def setUp(self):
        self.builder = GraphBuilder()

    # --- Resolution Logic (Migrated) ---

    def test_python_internal_resolution(self):
        """Test mapping imports to file IDs (Python)."""
        common = {"sha256": "h", "size_bytes": 1}
        
        files = [
            FileEntry(
                stable_id="file:src/main.py", path="src/main.py", language="python", 
                imports=["utils.logger", "config"], module_path="src", **common
            ),
            FileEntry(
                stable_id="file:src/utils/logger.py", path="src/utils/logger.py", language="python", 
                imports=[], module_path="src/utils", **common
            ),
            FileEntry(
                stable_id="file:config.py", path="config.py", language="python", 
                imports=[], module_path=".", **common
            )
        ]
        
        graph = self.builder.build(files)
        # Attribute access for Pydantic models
        edges = graph.edges
        
        self.assertTrue(any(
            e.source == "file:src/main.py" and e.target == "file:src/utils/logger.py"
            for e in edges
        ))
        
        self.assertTrue(any(
            e.source == "file:src/main.py" and e.target == "file:config.py"
            for e in edges
        ))

    def test_js_index_resolution(self):
        """Test resolving './components' to './components/index.tsx'."""
        common = {"sha256": "h", "size_bytes": 1}
        files = [
            FileEntry(
                stable_id="file:src/app.tsx", path="src/app.tsx", language="typescript",
                imports=["./components"], module_path="src", **common
            ),
            FileEntry(
                stable_id="file:src/components/index.tsx", path="src/components/index.tsx", language="typescript",
                imports=[], module_path="src/components", **common
            )
        ]
        
        graph = self.builder.build(files)
        edges = graph.edges
        
        self.assertTrue(any(
            e.source == "file:src/app.tsx" and e.target == "file:src/components/index.tsx"
            for e in edges
        ))

    def test_external_node_creation(self):
        """Test that unresolved imports become external nodes."""
        files = [
            FileEntry(
                stable_id="file:main.py", path="main.py", language="python",
                imports=["requests", "numpy"], module_path=".", sha256="h", size_bytes=1
            )
        ]
        
        graph = self.builder.build(files)
        nodes = {n.id for n in graph.nodes}
        
        self.assertIn("external:requests", nodes)
        self.assertIn("external:numpy", nodes)

    # --- Graph Construction Logic ---

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
        
        node_ids = set(n.id for n in graph.nodes)
        
        self.assertIn("external:@mui/material", node_ids)
        self.assertIn("external:lodash", node_ids)
        self.assertIn("external:@angular/core", node_ids)
        self.assertIn("external:react", node_ids)
        
        self.assertNotIn("external:@mui/material/Button", node_ids)
        self.assertNotIn("external:lodash/fp/map", node_ids)

    def test_graph_determinism(self):
        """Test that Graph output is perfectly sorted regardless of input order."""
        common = {"module_path": ".", "sha256": "abc", "size_bytes": 0}

        files_a = [
            FileEntry(stable_id="file:b.py", path="b.py", language="python", imports=["z_ext", "a_ext"], **common),
            FileEntry(stable_id="file:a.py", path="a.py", language="python", imports=["m_ext"], **common),
        ]
        
        files_b = [
            FileEntry(stable_id="file:a.py", path="a.py", language="python", imports=["m_ext"], **common),
            FileEntry(stable_id="file:b.py", path="b.py", language="python", imports=["a_ext", "z_ext"], **common),
        ]
        
        graph_a = self.builder.build(files_a)
        graph_b = self.builder.build(files_b)
        
        self.assertEqual(graph_a, graph_b)
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
        self.assertEqual(graph.cycles[0], ["file:a.py", "file:b.py"])

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
        self.assertFalse(graph.has_cycles)

if __name__ == "__main__":
    unittest.main()