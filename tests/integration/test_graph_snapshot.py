import unittest
import tempfile
import shutil
import os
import json
from src.core.controller import run_snapshot
from src.snapshot.snapshot_loader import SnapshotLoader

class TestGraphSnapshot(unittest.TestCase):
    def setUp(self):
        # FIX: os.path.realpath is mandatory on Windows to resolve 8.3 aliases 
        # and inconsistent drive casing returned by mkdtemp.
        self.test_dir = os.path.realpath(tempfile.mkdtemp())
        self.repo_root = os.path.join(self.test_dir, "repo")
        self.output_root = os.path.join(self.test_dir, "output")
        os.makedirs(self.repo_root)
        os.makedirs(self.output_root)

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

    def test_end_to_end_graph_generation(self):
        # 1. Setup a mini-repo with dependencies
        self._create_file("main.py", "import utils\nimport os")
        self._create_file("utils.py", "print('utils')")
        
        # 2. Run Snapshot
        snapshot_id = run_snapshot(
            repo_root=self.repo_root,
            output_root=self.output_root,
            depth=5,
            ignore=[],
            include_extensions=[".py"],
            include_readme=False,
            write_current_pointer=True,
            skip_graph=False
        )
        
        # 3. Load Results
        loader = SnapshotLoader(self.output_root)
        snap_dir = loader.resolve_snapshot_dir(snapshot_id)
        
        # Verify Manifest Stats
        manifest = loader.load_manifest(snap_dir)
        self.assertIn("os", manifest["stats"]["external_dependencies"])
        
        # Verify Graph JSON structure
        with open(os.path.join(snap_dir, "graph.json"), "r") as f:
            graph = json.load(f)
            
        nodes = {n["id"]: n for n in graph["nodes"]}
        edges = graph["edges"]
        
        # Check Nodes
        self.assertIn("file:main.py", nodes)
        self.assertIn("file:utils.py", nodes)
        self.assertIn("external:os", nodes)
        
        # Check Edges (main -> utils)
        found_internal = False
        for e in edges:
            if e["source"] == "file:main.py" and e["target"] == "file:utils.py":
                found_internal = True
                break
        self.assertTrue(found_internal, "Dependency edge main->utils not found")
        
        # Check Edges (main -> os)
        found_external = False
        for e in edges:
            if e["source"] == "file:main.py" and e["target"] == "external:os":
                found_external = True
                break
        self.assertTrue(found_external, "Dependency edge main->os not found")

if __name__ == "__main__":
    unittest.main()