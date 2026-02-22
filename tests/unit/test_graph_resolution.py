import unittest
from src.analysis.graph_builder import GraphBuilder
from src.core.types import FileEntry

class TestGraphResolution(unittest.TestCase):
    def setUp(self):
        self.builder = GraphBuilder()

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

if __name__ == "__main__":
    unittest.main()