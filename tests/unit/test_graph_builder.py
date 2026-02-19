import unittest
from src.analysis.graph_builder import GraphBuilder
from src.core.types import FileEntry

class TestGraphBuilder(unittest.TestCase):
    def setUp(self):
        self.files = [
            {
                "stable_id": "file:src/main.py",
                "path": "src/main.py",
                "language": "python",
                "imports": ["utils.logger", "os", "pandas.core.frame"], 
                "module_path": "src",
                "sha256": "abc", "size_bytes": 100
            },
            {
                "stable_id": "file:src/utils/logger.py",
                "path": "src/utils/logger.py", 
                "language": "python",
                "imports": [],
                "module_path": "src/utils",
                "sha256": "def", "size_bytes": 200
            },
            {
                "stable_id": "file:src/app.tsx",
                "path": "src/app.tsx",
                "language": "typescript",
                "imports": ["react", "react-dom/client", "@angular/core", "./components/button"],
                "module_path": "src",
                "sha256": "ghi", "size_bytes": 300
            }
        ]
        self.builder = GraphBuilder()

    def test_node_generation(self):
        graph = self.builder.build(self.files)
        
        node_ids = set(n["id"] for n in graph["nodes"])
        
        # Internal files
        self.assertIn("file:src/main.py", node_ids)
        self.assertIn("file:src/utils/logger.py", node_ids)
        
        # External nodes (Python)
        self.assertIn("external:os", node_ids)
        self.assertIn("external:pandas", node_ids) # Should collapse pandas.core.frame
        
        # External nodes (JS/TS)
        self.assertIn("external:react", node_ids)
        self.assertIn("external:react-dom", node_ids) # Should collapse react-dom/client
        self.assertIn("external:@angular/core", node_ids) # Scoped package

    def test_edge_resolution_python(self):
        graph = self.builder.build(self.files)
        edges = graph["edges"]
        
        # 1. Internal Edge: main.py -> logger.py
        internal_edge = next((e for e in edges if 
            e["source"] == "file:src/main.py" and 
            e["target"] == "file:src/utils/logger.py"), None)
        self.assertIsNotNone(internal_edge)
        
        # 2. External Edge: main.py -> os
        external_edge = next((e for e in edges if 
            e["source"] == "file:src/main.py" and 
            e["target"] == "external:os"), None)
        self.assertIsNotNone(external_edge)

    def test_edge_resolution_js(self):
        graph = self.builder.build(self.files)
        edges = graph["edges"]
        
        # 1. External Edge: app.tsx -> react
        react_edge = next((e for e in edges if 
            e["source"] == "file:src/app.tsx" and 
            e["target"] == "external:react"), None)
        self.assertIsNotNone(react_edge)
        
        # 2. External Edge: app.tsx -> @angular/core
        angular_edge = next((e for e in edges if 
            e["source"] == "file:src/app.tsx" and 
            e["target"] == "external:@angular/core"), None)
        self.assertIsNotNone(angular_edge)

    def test_broken_relative_imports_ignored(self):
        # If a relative import doesn't resolve to a file, it should NOT become an external node
        files = [{
            "stable_id": "file:broken.py",
            "path": "broken.py",
            "language": "python",
            "imports": [".non_existent"], 
            "module_path": ".",
            "sha256": "123", "size_bytes": 10
        }]
        
        graph = self.builder.build(files)
        node_ids = [n["id"] for n in graph["nodes"]]
        
        self.assertNotIn("external:.non_existent", node_ids)
        self.assertNotIn("external:non_existent", node_ids)

if __name__ == "__main__":
    unittest.main()