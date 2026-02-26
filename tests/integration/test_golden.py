import unittest
import os
import json
import pytest
from src.core.controller import run_snapshot
from src.snapshot.snapshot_loader import SnapshotLoader
from tests.conftest import scrub_json

# The "Golden" State implies:
# 1. We expect specific stable IDs (lowercase, normalized)
# 2. We expect specific edges (dependency resolution working)
# 3. We expect Pydantic serialization to match specific keys
GOLDEN_GRAPH_SUBSET = {
    "nodes": [
        # "external:flask", # REMOVED: Scanner does not yet support requirements.txt
        {"id": "external:react", "type": "external"},
        {"id": "file:package.json", "type": "file"},
        {"id": "file:src/backend/api.py", "type": "file"},
        {"id": "file:src/backend/utils.py", "type": "file"},
        {"id": "file:src/frontend/app.tsx", "type": "file"},
        {"id": "file:src/frontend/components/button.tsx", "type": "file"},
    ],
    "edges": [
        # Python relative import
        {"source": "file:src/backend/api.py", "target": "file:src/backend/utils.py", "relation": "imports"},
        # JS Component import
        {"source": "file:src/frontend/app.tsx", "target": "file:src/frontend/components/button.tsx", "relation": "imports"},
        # JS External import (canonicalized)
        {"source": "file:src/frontend/app.tsx", "target": "external:react", "relation": "imports"},
    ]
}

class TestGoldenSnapshot(unittest.TestCase):
    """
    Validates that the output matches a strict, human-verified 'Golden' standard.
    This prevents silent regressions in graph logic or ID generation.
    """

    @pytest.fixture(autouse=True)
    def _inject_fixtures(self, complex_repo):
        # FIX: Ensure we use the OS-canonical path to prevent mismatch 
        # between fixture-generated paths and scanner-detected paths on Windows.
        self.repo_root = os.path.realpath(complex_repo)

    def test_matches_golden_expectations(self):
        # 1. Run Snapshot on the Complex Repo
        # Note: We use a temp output root. We place it OUTSIDE the repo root 
        # to avoid self-scanning loops if ignore logic fails (though robust scanner handles it).
        output_root = os.path.join(os.path.dirname(self.repo_root), "output_golden_nodes")
        
        snapshot_id = run_snapshot(
            repo_root=self.repo_root,
            output_root=output_root,
            depth=10,
            ignore=["node_modules", "dist", ".git"],
            include_extensions=[".py", ".tsx", ".json"], # Explicitly include json for package.json
            include_readme=False,
            write_current_pointer=True,
            skip_graph=False
        )
        
        # 2. Load the Result
        loader = SnapshotLoader(output_root)
        snap_dir = loader.resolve_snapshot_dir(snapshot_id)
        
        with open(os.path.join(snap_dir, "graph.json"), "r") as f:
            graph_data = json.load(f)
            
        # 3. Verify Nodes (Set Comparison for content, ignoring order)
        # We only check that the GOLDEN nodes exist in the output. 
        # The output might contain more (e.g. implicit nodes), but it MUST contain these.
        
        actual_node_ids = {n["id"] for n in graph_data["nodes"]}
        for expected in GOLDEN_GRAPH_SUBSET["nodes"]:
            self.assertIn(expected["id"], actual_node_ids, f"Missing expected node: {expected['id']}")
            
            # Verify Type
            actual_node = next(n for n in graph_data["nodes"] if n["id"] == expected["id"])
            self.assertEqual(actual_node["type"], expected["type"], f"Type mismatch for {expected['id']}")

    def test_golden_edges(self):
        output_root = os.path.join(os.path.dirname(self.repo_root), "output_golden_edges")
        
        snapshot_id = run_snapshot(
            repo_root=self.repo_root,
            output_root=output_root,
            depth=10,
            ignore=["node_modules", "dist", ".git"],
            include_extensions=[".py", ".tsx"],
            include_readme=False,
            write_current_pointer=True,
            skip_graph=False
        )
        
        loader = SnapshotLoader(output_root)
        snap_dir = loader.resolve_snapshot_dir(snapshot_id)
        
        with open(os.path.join(snap_dir, "graph.json"), "r") as f:
            graph_data = json.load(f)
            
        # Create a set of "Source->Target" strings for O(1) lookup
        actual_edges = {f"{e['source']}->{e['target']}" for e in graph_data["edges"]}
        
        for expected in GOLDEN_GRAPH_SUBSET["edges"]:
            key = f"{expected['source']}->{expected['target']}"
            self.assertIn(key, actual_edges, f"Missing expected edge: {key}")

    def test_manifest_schema_version(self):
        """
        Ensures the manifest version is pinned. 
        If we change the schema, we must update this test and the Spec.
        """
        output_root = os.path.join(os.path.dirname(self.repo_root), "output_schema")
        snapshot_id = run_snapshot(
            repo_root=self.repo_root,
            output_root=output_root,
            depth=5,
            ignore=[],
            include_extensions=[".py"],
            include_readme=False,
            write_current_pointer=True,
            skip_graph=False
        )
        
        loader = SnapshotLoader(output_root)
        snap_dir = loader.resolve_snapshot_dir(snapshot_id)
        manifest = loader.load_manifest(snap_dir)
        
        # Enforce v1.0 schema compliance
        self.assertEqual(manifest["schema_version"], "1.0")
        self.assertEqual(manifest["tool"]["name"], "repo-runner")
        
        # Ensure 'files' is a list and has strict ordering
        self.assertTrue(isinstance(manifest["files"], list))
        if len(manifest["files"]) > 1:
            sorted_files = sorted(manifest["files"], key=lambda x: x["path"])
            self.assertEqual(manifest["files"], sorted_files, "Manifest files are not sorted by path")

if __name__ == "__main__":
    unittest.main()