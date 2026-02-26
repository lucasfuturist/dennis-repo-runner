import unittest
from src.analysis.graph_builder import GraphBuilder
from src.core.types import FileEntry

class TestGraphBuilderUnresolved(unittest.TestCase):
    
    def test_captures_unresolved_references(self):
        """
        Verifies that imports which are NOT files and NOT valid externals
        (e.g. broken relative paths) are captured in unresolved_references.
        """
        # Mock file entries
        files = [
            FileEntry(
                path="src/main.ts",
                stable_id="file:src/main.ts",
                module_path="src",
                sha256="abc",
                size_bytes=10,
                language="typescript",
                imports=[
                    "./utils",         # Valid (exists below)
                    "./missing_file",  # Broken relative
                    "react",           # Valid external
                    "/absolute/bad"    # Broken absolute (not allowed in external logic)
                ]
            ),
            FileEntry(
                path="src/utils.ts",
                stable_id="file:src/utils.ts",
                module_path="src",
                sha256="def",
                size_bytes=10,
                language="typescript",
                imports=[]
            )
        ]
        
        builder = GraphBuilder()
        graph = builder.build(files)
        
        # 1. Verify Nodes
        node_ids = {n.id for n in graph.nodes}
        self.assertIn("file:src/main.ts", node_ids)
        self.assertIn("file:src/utils.ts", node_ids)
        self.assertIn("external:react", node_ids)
        
        # 2. Verify Unresolved
        # "./missing_file" starts with ".", so _resolve_external returns None.
        # It's not in files list, so _resolve_import returns None.
        # Should be unresolved.
        unresolved_map = {u.import_ref: u.source for u in graph.unresolved_references}
        
        self.assertIn("./missing_file", unresolved_map)
        self.assertEqual(unresolved_map["./missing_file"], "file:src/main.ts")
        
        self.assertIn("/absolute/bad", unresolved_map)
        
        # "react" should NOT be unresolved
        self.assertNotIn("react", unresolved_map)
        
        # "./utils" should NOT be unresolved
        self.assertNotIn("./utils", unresolved_map)

    def test_python_unresolved(self):
        files = [
            FileEntry(
                path="src/app.py",
                stable_id="file:src/app.py",
                module_path="src",
                sha256="123",
                size_bytes=10,
                language="python",
                imports=[
                    ".missing_submodule", # Broken relative
                    "requests"            # Valid external
                ]
            )
        ]
        
        builder = GraphBuilder()
        graph = builder.build(files)
        
        unresolved_map = {u.import_ref for u in graph.unresolved_references}
        
        self.assertIn(".missing_submodule", unresolved_map)
        self.assertNotIn("requests", unresolved_map)

if __name__ == "__main__":
    unittest.main()