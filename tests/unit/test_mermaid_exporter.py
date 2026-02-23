import unittest
import os
import shutil
import tempfile
from src.exporters.mermaid_exporter import MermaidExporter
from src.core.types import GraphStructure, GraphNode, GraphEdge

class TestMermaidExporter(unittest.TestCase):
    def setUp(self):
        self.exporter = MermaidExporter()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_basic_export_syntax(self):
        """Ensure valid Mermaid syntax is generated for simple graph."""
        nodes = [
            GraphNode(id="file:src/main.py", type="file"),
            GraphNode(id="file:src/utils.py", type="file"),
            GraphNode(id="external:react", type="external")
        ]
        edges = [
            GraphEdge(source="file:src/main.py", target="file:src/utils.py"),
            GraphEdge(source="file:src/main.py", target="external:react")
        ]
        
        graph = GraphStructure(nodes=nodes, edges=edges)
        output_file = os.path.join(self.temp_dir, "test.mmd")
        
        self.exporter.export(self.temp_dir, graph, output_file)
        
        with open(output_file, "r") as f:
            content = f.read()
            
        self.assertIn("graph TD", content)
        # FIXED: Subgraph IDs use the 'subgraph_' prefix to avoid collisions
        self.assertIn("subgraph subgraph_src", content) 
        self.assertIn("file_src_main_py[main.py]", content)
        self.assertIn("external_react([react]):::external", content)
        self.assertIn("file_src_main_py --> file_src_utils_py", content)

    def test_cycle_highlighting(self):
        """Ensure edges involved in cycles are styled differently."""
        nodes = [
            GraphNode(id="file:a.py", type="file"),
            GraphNode(id="file:b.py", type="file")
        ]
        edges = [
            GraphEdge(source="file:a.py", target="file:b.py"),
            GraphEdge(source="file:b.py", target="file:a.py")
        ]
        # Simulate cycle detection result
        graph = GraphStructure(
            nodes=nodes, 
            edges=edges, 
            cycles=[["file:a.py", "file:b.py"]]
        )
        
        content = self.exporter._generate_content(graph, None)
        
        # Look for cycle styling
        self.assertIn("file_a_py[a.py]:::cycle", content)
        self.assertIn("file_b_py[b.py]:::cycle", content)
        # Note: Mermaid edge styles are just text in the arrow
        self.assertIn("file_a_py -.->|CYCLE| file_b_py", content)

    def test_id_escaping(self):
        """Ensure special characters in IDs don't break Mermaid syntax."""
        raw_id = "external:@scope/package-name"
        clean = self.exporter._escape_id(raw_id)
        
        self.assertEqual(clean, "external__scope_package_name")
        self.assertNotIn("/", clean)
        self.assertNotIn("@", clean)
        self.assertNotIn("-", clean)

if __name__ == "__main__":
    unittest.main()