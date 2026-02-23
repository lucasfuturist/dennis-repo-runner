import unittest
import os
import shutil
import tempfile
import csv
import io
from src.exporters.drawio_exporter import DrawioExporter
from src.core.types import GraphStructure, GraphNode, GraphEdge

class TestDrawioExporter(unittest.TestCase):
    def setUp(self):
        self.exporter = DrawioExporter()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_csv_generation(self):
        """Ensure valid Draw.io CSV layout formatting."""
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
        output_file = os.path.join(self.temp_dir, "test.drawio.csv")
        
        self.exporter.export(self.temp_dir, graph, output_file)
        
        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()
            
        # Check Headers
        self.assertIn("## Draw.io auto-layout CSV", content)
        self.assertIn("# layout: horizontalflow", content)
        self.assertIn("# connect: {\"from\": \"refs\"", content)
        
        # Parse the actual CSV data (skip the # comments)
        data_lines = [line for line in content.split("\n") if not line.startswith("#") and line.strip()]
        reader = csv.DictReader(data_lines)
        rows = list(reader)
        
        # Verify Modules were extracted
        module_row = next((r for r in rows if r["id"] == "module_src"), None)
        self.assertIsNotNone(module_row, "Container node 'module_src' should be generated")
        self.assertIn("shape=swimlane", module_row["style"])
        
        # Verify Files
        main_row = next((r for r in rows if r["id"] == "file:src/main.py"), None)
        self.assertIsNotNone(main_row)
        self.assertEqual(main_row["parent"], "module_src")
        # Ensure 'refs' contains both targets, comma-separated
        self.assertIn("file:src/utils.py", main_row["refs"])
        self.assertIn("external:react", main_row["refs"])
        
        # Verify Externals (no parent)
        ext_row = next((r for r in rows if r["id"] == "external:react"), None)
        self.assertIsNotNone(ext_row)
        self.assertEqual(ext_row["parent"], "")

if __name__ == "__main__":
    unittest.main()