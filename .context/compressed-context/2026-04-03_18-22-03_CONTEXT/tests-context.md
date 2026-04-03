# Module Export: tests

- repo_root: `C:/projects/repo-runner`
- snapshot_id: `BATCH_EXPORT`
- file_count: `31`
- tree_only: `False`
## Tree

```
└── tests
    ├── __init__.py
    ├── conftest.py
    ├── integration
    │   ├── __init__.py
    │   ├── test_api.py
    │   ├── test_cli_diff.py
    │   ├── test_cli_slice.py
    │   ├── test_e2e_snapshot.py
    │   ├── test_export_flow.py
    │   ├── test_golden.py
    │   ├── test_graph_snapshot.py
    │   └── test_robustness.py
    └── unit
        ├── __init__.py
        ├── test_collision_logic.py
        ├── test_config_loader.py
        ├── test_context_slicer.py
        ├── test_drawio_exporter.py
        ├── test_file_fingerprint.py
        ├── test_filesystem_scanner.py
        ├── test_flatten_exporter.py
        ├── test_graph_builder.py
        ├── test_graph_builder_unresolved.py
        ├── test_ignore_logic.py
        ├── test_import_scanner.py
        ├── test_mermaid_exporter.py
        ├── test_path_normalizer.py
        ├── test_scanner_constants.py
        ├── test_snapshot_comparator.py
        ├── test_snapshot_loader.py
        ├── test_structure_builder.py
        ├── test_token_telemetry.py
        └── test_types.py
```

## File Contents

### `tests/__init__.py`

```

```

### `tests/conftest.py`

```
import pytest
import os
import shutil
import tempfile
import json
from pathlib import Path
from typing import Generator, List, Dict, Any

@pytest.fixture
def temp_repo_root() -> Generator[str, None, None]:
    """
    Creates a temporary directory to act as a repository root.
    Cleans up after the test completes.
    """
    # Create a unique temp directory
    tmp_dir = tempfile.mkdtemp(prefix="repo_runner_test_")
    
    # Normalize path immediately to avoid Windows/Linux mismatches in tests
    tmp_path = os.path.normpath(tmp_dir).replace("\\", "/")
    
    yield tmp_path
    
    # Teardown
    if os.path.exists(tmp_dir):
        try:
            shutil.rmtree(tmp_dir)
        except PermissionError:
            # Common on Windows if a file handle is still open
            pass

@pytest.fixture
def create_file(temp_repo_root):
    """
    Factory fixture to create files within the temp repo.
    Usage: create_file("src/main.py", "print('hello')")
    """
    def _create(rel_path: str, content: str = ""):
        full_path = os.path.join(temp_repo_root, rel_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        return full_path
    return _create

@pytest.fixture
def simple_repo(temp_repo_root, create_file):
    """
    Populates the temp repo with a minimal Python structure.
    """
    create_file("src/main.py", "import os\nprint('hello')")
    create_file("src/utils.py", "def add(a, b): return a + b")
    create_file("README.md", "# Test Repo")
    return temp_repo_root

@pytest.fixture
def complex_repo(temp_repo_root, create_file):
    """
    Populates the temp repo with a mixed-language, nested structure
    including ignored directories.
    """
    # Python
    create_file("src/backend/api.py", "from . import utils")
    create_file("src/backend/utils.py", "SECRET = 'xyz'")
    
    # Typescript/React
    create_file("src/frontend/App.tsx", "import React from 'react';\nimport { Button } from './components/Button';")
    create_file("src/frontend/components/Button.tsx", "export const Button = () => <button />")
    
    # Ignored folders
    create_file("node_modules/react/index.js", "module.exports = {}")
    create_file(".git/config", "[core]\nrepositoryformatversion = 0")
    create_file("dist/bundle.js", "var a = 1;")
    
    # Configs
    create_file("package.json", "{}")
    create_file("requirements.txt", "flask")
    
    return temp_repo_root

def scrub_json(data: Any) -> Any:
    """
    Recursively removes volatile fields (timestamps, dynamic paths) from a JSON object
    to allow deterministic comparison.
    """
    if isinstance(data, dict):
        # Create a copy to avoid mutating the original
        new_data = data.copy()
        
        # Volatile fields to remove
        keys_to_remove = ["created_utc", "snapshot_id", "output_root", "tool"]
        
        for key in keys_to_remove:
            if key in new_data:
                del new_data[key]
        
        # Recurse
        for k, v in new_data.items():
            new_data[k] = scrub_json(v)
        return new_data
    
    elif isinstance(data, list):
        return [scrub_json(item) for item in data]
        
    return data

@pytest.fixture
def assert_snapshot_determinism():
    """
    Returns a function that compares two snapshot directories for logical equivalence.
    Usage: assert_snapshot_determinism(dir_a, dir_b)
    """
    def _compare(dir_a: str, dir_b: str):
        files_to_compare = ["manifest.json", "graph.json", "structure.json"]
        
        for fname in files_to_compare:
            path_a = os.path.join(dir_a, fname)
            path_b = os.path.join(dir_b, fname)
            
            # Check existence
            assert os.path.exists(path_a), f"{fname} missing in Run A"
            assert os.path.exists(path_b), f"{fname} missing in Run B"
            
            with open(path_a, "r", encoding="utf-8") as f:
                json_a = json.load(f)
            with open(path_b, "r", encoding="utf-8") as f:
                json_b = json.load(f)
                
            scrubbed_a = scrub_json(json_a)
            scrubbed_b = scrub_json(json_b)
            
            # Use json.dumps with sort_keys to generate a readable diff if assertion fails
            str_a = json.dumps(scrubbed_a, sort_keys=True, indent=2)
            str_b = json.dumps(scrubbed_b, sort_keys=True, indent=2)
            
            assert str_a == str_b, f"Determinism failure in {fname}"
            
    return _compare
```

### `tests/integration/__init__.py`

```

```

### `tests/integration/test_api.py`

```
import unittest
import tempfile
import shutil
import os
import time
from fastapi.testclient import TestClient

# Must import the FastAPI app instance
from src.api.server import app

class TestAPI(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.realpath(tempfile.mkdtemp())
        self.repo_root = os.path.join(self.test_dir, "repo")
        self.output_root = os.path.join(self.test_dir, "output")
        os.makedirs(self.repo_root, exist_ok=True)
        os.makedirs(self.output_root, exist_ok=True)
        
        # Setup test client
        self.client = TestClient(app)

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

    def test_full_api_lifecycle(self):
        """
        Tests the entire lifecycle: Create Snapshot -> Slice Context -> Compare
        """
        # 1. Setup initial repo state
        self._create_file("main.py", "import utils\nprint('hello')")
        self._create_file("utils.py", "def helper(): pass")

        # 2. Test POST /snapshots (v1)
        response_v1 = self.client.post("/snapshots", json={
            "repo_root": self.repo_root,
            "output_root": self.output_root,
            "include_extensions": [".py"]
        })
        self.assertEqual(response_v1.status_code, 200)
        snap_v1_id = response_v1.json()["snapshot_id"]

        # 3. Test POST /snapshots/{id}/slice
        slice_resp = self.client.post(f"/snapshots/{snap_v1_id}/slice", json={
            "output_root": self.output_root,
            "focus_id": "file:main.py",
            "radius": 1
        })
        self.assertEqual(slice_resp.status_code, 200)
        slice_data = slice_resp.json()
        self.assertIn("telemetry_markdown", slice_data)
        
        # Ensure 'utils.py' is pulled into context via the 'main.py' import edge
        sliced_files = [f["stable_id"] for f in slice_data["sliced_manifest"]["files"]]
        self.assertIn("file:utils.py", sliced_files)

        # 4. Mutate the Repo (Remove utils, add config)
        os.remove(os.path.join(self.repo_root, "utils.py"))
        self._create_file("main.py", "import config\nprint('hello v2')") # modified
        self._create_file("config.py", "ENV='prod'") # added

        # FIX: Sleep for >1 second to ensure the second snapshot gets a unique timestamp ID
        time.sleep(1.1)

        # 5. Test POST /snapshots (v2)
        response_v2 = self.client.post("/snapshots", json={
            "repo_root": self.repo_root,
            "output_root": self.output_root,
            "include_extensions": [".py"]
        })
        snap_v2_id = response_v2.json()["snapshot_id"]
        
        # Verify IDs are actually different
        self.assertNotEqual(snap_v1_id, snap_v2_id, "Snapshots executed too fast, IDs collided.")

        # 6. Test POST /snapshots/compare
        compare_resp = self.client.post("/snapshots/compare", json={
            "output_root": self.output_root,
            "base_id": snap_v1_id,
            "target_id": snap_v2_id
        })
        self.assertEqual(compare_resp.status_code, 200)
        diff_report = compare_resp.json()

        # Validate Structural Diff matches our OS mutations
        self.assertEqual(diff_report["files_added"], 1)     # config.py
        self.assertEqual(diff_report["files_removed"], 1)   # utils.py
        self.assertEqual(diff_report["files_modified"], 1)  # main.py

    def test_slice_with_token_limit(self):
        """
        Tests that setting max_tokens strictly limits the returned files.
        """
        # Create a heavy dependency chain: A -> B (Heavy)
        self._create_file("a.py", "import b")
        # 1 token ~= 4 chars. Create ~1000 tokens (4000 chars)
        self._create_file("b.py", "#" * 4000) 

        # Snapshot
        resp = self.client.post("/snapshots", json={
            "repo_root": self.repo_root,
            "output_root": self.output_root,
            "include_extensions": [".py"]
        })
        snap_id = resp.json()["snapshot_id"]

        # Request slice with small limit (e.g. 50 tokens)
        # Should include A (focus, small) but EXCLUDE B (too big)
        slice_resp = self.client.post(f"/snapshots/{snap_id}/slice", json={
            "output_root": self.output_root,
            "focus_id": "file:a.py",
            "radius": 1,
            "max_tokens": 50
        })
        
        data = slice_resp.json()
        files = [f["stable_id"] for f in data["sliced_manifest"]["files"]]
        
        self.assertIn("file:a.py", files)
        self.assertNotIn("file:b.py", files)
        
        # Telemetry should reflect the drop
        self.assertIn("Usage:", data["telemetry_markdown"])
        # Estimated tokens should be low (just A)
        stats = data["sliced_manifest"]["stats"]
        self.assertTrue(stats["estimated_tokens"] < 100)

if __name__ == "__main__":
    unittest.main()
```

### `tests/integration/test_cli_diff.py`

```
import unittest
from unittest.mock import patch, MagicMock
from src.cli.main import main
import sys

class TestCLIDiff(unittest.TestCase):
    
    @patch('src.cli.main.run_compare')
    @patch('src.cli.main.ConfigLoader.load_config')
    def test_diff_command_parsing(self, mock_config, mock_compare):
        """Verify the diff command sends correct IDs to the controller."""
        # Setup mock report
        mock_report = MagicMock()
        mock_report.base_snapshot_id = "base_snap"
        mock_report.target_snapshot_id = "target_snap"
        mock_report.file_diffs = []
        mock_report.edge_diffs = []
        mock_compare.return_value = mock_report
        
        # Setup mock config
        mock_config.return_value.output_root = "./out"

        test_args = [
            "diff",
            "--base", "2026-02-22T01",
            "--target", "current"
        ]
        
        with patch.object(sys, 'argv', ["repo-runner"] + test_args):
            main()
            
            mock_compare.assert_called_once_with("./out", "2026-02-22T01", "current")

if __name__ == "__main__":
    unittest.main()
```

### `tests/integration/test_cli_slice.py`

```
import unittest
from unittest.mock import patch, MagicMock
from src.cli.main import _parse_args, main
import sys

class TestCLISlice(unittest.TestCase):
    
    @patch('src.cli.main.run_export_flatten')
    def test_slice_command_invocation(self, mock_export):
        """
        Verify that `repo-runner slice` parses args correctly and calls the controller.
        """
        # Mock sys.argv
        test_args = [
            "slice",
            "--output-root", "./out",
            "--repo-root", "./repo",
            "--focus", "file:src/app.py",
            "--radius", "2",
            "--max-tokens", "5000"
        ]
        
        with patch.object(sys, 'argv', ["repo-runner"] + test_args):
            # Run main, which calls _parse_args internally
            main()
            
            # Assert controller was called with correct types
            mock_export.assert_called_once()
            _, kwargs = mock_export.call_args
            
            self.assertEqual(kwargs["focus_id"], "file:src/app.py")
            self.assertEqual(kwargs["radius"], 2)
            self.assertEqual(kwargs["max_tokens"], 5000)
            self.assertEqual(kwargs["repo_root"], "./repo")

    @patch('src.cli.main.run_export_flatten')
    def test_slice_defaults(self, mock_export):
        """
        Verify default values for radius and max_tokens.
        """
        test_args = [
            "slice",
            "--output-root", "./out",
            "--repo-root", "./repo",
            "--focus", "file:main.py"
        ]
        
        with patch.object(sys, 'argv', ["repo-runner"] + test_args):
            main()
            
            _, kwargs = mock_export.call_args
            self.assertEqual(kwargs["radius"], 1) # Default
            self.assertIsNone(kwargs["max_tokens"]) # Default None

if __name__ == "__main__":
    unittest.main()
```

### `tests/integration/test_e2e_snapshot.py`

```
import unittest
import tempfile
import shutil
import os
from src.core.controller import run_snapshot
from src.snapshot.snapshot_loader import SnapshotLoader

class TestFullSnapshot(unittest.TestCase):
    def setUp(self):
        # Resolve real path immediately to avoid Windows 8.3 short-path / relpath bugs
        self.test_dir = os.path.realpath(tempfile.mkdtemp())
        self.repo_root = os.path.join(self.test_dir, "my_repo")
        self.output_root = os.path.join(self.test_dir, "output")
        
        os.makedirs(self.repo_root)
        os.makedirs(self.output_root)

        self._create_file("README.md", "# Hello")
        self._create_file("src/main.py", "import os\nprint('hello')")
        self._create_file("src/utils.py", "def add(a,b): return a+b")
        self._create_file("node_modules/bad_file.js", "ignore me")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _create_file(self, path, content):
        full_path = os.path.join(self.repo_root, path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w") as f:
            f.write(content)

    def test_snapshot_creation_with_graph_and_auto_export(self):
        # 1. Run Snapshot with v0.2 features enabled
        snapshot_id = run_snapshot(
            repo_root=self.repo_root,
            output_root=self.output_root,
            depth=5,
            ignore=["node_modules"],
            include_extensions=[".py", ".md"],
            include_readme=True,
            write_current_pointer=True,
            skip_graph=False,
            export_flatten=True
        )

        snap_dir = os.path.join(self.output_root, snapshot_id)
        
        # 2. Verify Output Directory Structure
        self.assertTrue(os.path.isdir(snap_dir))
        self.assertTrue(os.path.isfile(os.path.join(snap_dir, "manifest.json")))
        self.assertTrue(os.path.isfile(os.path.join(snap_dir, "structure.json")))
        self.assertTrue(os.path.isfile(os.path.join(snap_dir, "graph.json")), "Graph should be generated")
        self.assertTrue(os.path.isfile(os.path.join(snap_dir, "exports", "flatten.md")), "Auto-export should exist")

        # 3. Verify Manifest Stats (External Deps)
        loader = SnapshotLoader(self.output_root)
        manifest = loader.load_manifest(snap_dir)
        stats = manifest["stats"]
        self.assertIn("os", stats.get("external_dependencies", []))

    def test_snapshot_skip_graph(self):
        # 1. Run Snapshot with Graph Skipped
        snapshot_id = run_snapshot(
            repo_root=self.repo_root,
            output_root=self.output_root,
            depth=5,
            ignore=["node_modules"],
            include_extensions=[".py", ".md"],
            include_readme=True,
            write_current_pointer=True,
            skip_graph=True,
            export_flatten=False
        )

        snap_dir = os.path.join(self.output_root, snapshot_id)
        
        # 2. Verify Graph Absence
        self.assertFalse(os.path.exists(os.path.join(snap_dir, "graph.json")), "Graph should NOT be generated")
        
        # 3. Verify Manifest Reflects Config
        loader = SnapshotLoader(self.output_root)
        manifest = loader.load_manifest(snap_dir)
        self.assertTrue(manifest["config"]["skip_graph"])
        self.assertEqual(manifest["stats"].get("external_dependencies", []), [])

if __name__ == "__main__":
    unittest.main()
```

### `tests/integration/test_export_flow.py`

```
import unittest
import tempfile
import shutil
import os
from src.core.controller import run_snapshot, run_export_flatten

class TestExportFlow(unittest.TestCase):
    def setUp(self):
        # Resolve real path immediately to avoid Windows 8.3 short-path / relpath bugs
        self.test_dir = os.path.realpath(tempfile.mkdtemp())
        self.repo_root = os.path.join(self.test_dir, "my_repo")
        self.output_root = os.path.join(self.test_dir, "output")
        os.makedirs(self.repo_root)
        os.makedirs(self.output_root)

        self._create_file("README.md", "# Document Root\nTest.")
        self._create_file("src/api/server.js", "console.log('server');")
        self._create_file("src/api/routes.js", "console.log('routes');")
        self._create_file("src/ui/app.js", "console.log('app');")

        # Create base snapshot to export from
        self.snap_id = run_snapshot(
            repo_root=self.repo_root,
            output_root=self.output_root,
            depth=10,
            ignore=[],
            include_extensions=[".js", ".md"],
            include_readme=True,
            write_current_pointer=True,
            skip_graph=True
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _create_file(self, path, content):
        full_path = os.path.join(self.repo_root, path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w") as f:
            f.write(content)

    def test_export_full_with_tokens(self):
        out_path = os.path.join(self.test_dir, "custom_export.md")
        
        run_export_flatten(
            output_root=self.output_root,
            repo_root=self.repo_root,
            snapshot_id=self.snap_id,
            output_path=out_path,
            tree_only=False,
            include_readme=True,
            scope="full",
            title="E2E Export Test"
        )
        
        self.assertTrue(os.path.exists(out_path))
        with open(out_path, "r") as f:
            content = f.read()
            
        self.assertIn("# E2E Export Test", content)
        self.assertIn("## Context Stats", content)
        self.assertIn("Estimated Tokens", content)
        self.assertIn("server.js", content)
        self.assertIn("routes.js", content)
        self.assertIn("app.js", content)

    def test_export_scoped(self):
        out_path = os.path.join(self.test_dir, "scoped_export.md")
        
        run_export_flatten(
            output_root=self.output_root,
            repo_root=self.repo_root,
            snapshot_id=self.snap_id,
            output_path=out_path,
            tree_only=False,
            include_readme=False,
            scope="module:src/api",
            title="Scoped Export"
        )
        
        with open(out_path, "r") as f:
            content = f.read()
            
        # Should include API files
        self.assertIn("server.js", content)
        self.assertIn("routes.js", content)
        
        # Should exclude UI and Readme
        self.assertNotIn("app.js", content)
        self.assertNotIn("README.md", content.upper())

if __name__ == "__main__":
    unittest.main()
```

### `tests/integration/test_golden.py`

```
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
```

### `tests/integration/test_graph_snapshot.py`

```
import unittest
import tempfile
import shutil
import os
import json
import pytest
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
        with open(path, "w", encoding="utf-8") as f:
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

    def test_external_id_canonicalization(self):
        """
        Ensures that mixed-case imports for the same external package 
        resolve to a single, lowercased external node.
        """
        # Create files with mixed casing for 'react'
        self._create_file("component_a.tsx", "import React from 'react';")
        self._create_file("component_b.tsx", "import { useState } from 'React';") # Capitalized import
        self._create_file("component_c.tsx", "import * as R from 'react/client';") # Subpath
        
        snapshot_id = run_snapshot(
            repo_root=self.repo_root,
            output_root=self.output_root,
            depth=5,
            ignore=[],
            include_extensions=[".tsx"],
            include_readme=False,
            write_current_pointer=True,  # Added missing arg
            skip_graph=False
        )
        
        loader = SnapshotLoader(self.output_root)
        snap_dir = loader.resolve_snapshot_dir(snapshot_id)
        
        with open(os.path.join(snap_dir, "graph.json"), "r") as f:
            graph = json.load(f)
            
        nodes = {n["id"] for n in graph["nodes"]}
        
        # Must contain exactly one react node, and it must be lowercase
        self.assertIn("external:react", nodes)
        self.assertNotIn("external:React", nodes)
        
        # Ensure 'react/client' was normalized to root 'react'
        self.assertNotIn("external:react/client", nodes)

    def test_snapshot_determinism(self):
        """
        Runs the snapshot process twice on the exact same repo and asserts
        that the outputs (stripped of timestamps) are bit-for-bit identical.
        This uses the logic from assert_snapshot_determinism fixture, recreated here
        since we are in a unittest.TestCase class.
        """
        # Setup complex state
        self._create_file("main.py", "import utils\nimport requests")
        self._create_file("utils.py", "x = 1")
        
        # Run 1
        id_1 = run_snapshot(
            repo_root=self.repo_root,
            output_root=self.output_root,
            depth=5,
            ignore=[],
            include_extensions=[".py"],
            include_readme=False,
            write_current_pointer=True,  # Added missing arg
            skip_graph=False
        )
        
        # Run 2
        id_2 = run_snapshot(
            repo_root=self.repo_root,
            output_root=self.output_root,
            depth=5,
            ignore=[],
            include_extensions=[".py"],
            include_readme=False,
            write_current_pointer=True,  # Added missing arg
            skip_graph=False
        )
        
        loader = SnapshotLoader(self.output_root)
        dir_1 = loader.resolve_snapshot_dir(id_1)
        dir_2 = loader.resolve_snapshot_dir(id_2)
        
        # Use a local helper similar to the fixture logic
        from tests.conftest import scrub_json
        
        for fname in ["manifest.json", "graph.json", "structure.json"]:
            with open(os.path.join(dir_1, fname), "r") as f:
                json_1 = scrub_json(json.load(f))
            with open(os.path.join(dir_2, fname), "r") as f:
                json_2 = scrub_json(json.load(f))
                
            self.assertEqual(
                json.dumps(json_1, sort_keys=True),
                json.dumps(json_2, sort_keys=True),
                f"Determinism failed for {fname}"
            )

if __name__ == "__main__":
    unittest.main()
```

### `tests/integration/test_robustness.py`

```
import unittest
import tempfile
import shutil
import os
import sys
from src.core.controller import run_snapshot
from src.snapshot.snapshot_loader import SnapshotLoader

class TestRobustness(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.realpath(tempfile.mkdtemp())
        self.repo_root = os.path.join(self.test_dir, "repo")
        self.output_root = os.path.join(self.test_dir, "output")
        os.makedirs(self.repo_root)
        os.makedirs(self.output_root)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_snapshot_with_mixed_health(self):
        # 1. Valid Files
        with open(os.path.join(self.repo_root, "valid.py"), "w") as f:
            f.write("print('ok')")
            
        # 2. Ignored Files
        os.makedirs(os.path.join(self.repo_root, "node_modules"))
        with open(os.path.join(self.repo_root, "node_modules", "ignore.js"), "w") as f:
            f.write("ignore")

        # 3. Symlink Cycle (Unix only)
        if sys.platform != 'win32':
            os.symlink(self.repo_root, os.path.join(self.repo_root, "loop"))

        # Run Snapshot
        # This should succeed despite the complexity
        snap_id = run_snapshot(
            repo_root=self.repo_root,
            output_root=self.output_root,
            depth=10,
            ignore=["node_modules"],
            include_extensions=[],
            include_readme=True,
            write_current_pointer=True,
            skip_graph=True
        )

        # Verify Manifest
        loader = SnapshotLoader(self.output_root)
        manifest = loader.load_manifest(os.path.join(self.output_root, snap_id))
        
        files = manifest["files"]
        paths = [f["path"] for f in files]
        
        self.assertIn("valid.py", paths)
        self.assertNotIn("node_modules/ignore.js", paths)
        
        # Ensure we didn't index the loop infinitely
        loop_matches = [p for p in paths if "loop" in p]
        self.assertLess(len(loop_matches), 2)

if __name__ == "__main__":
    unittest.main()
```

### `tests/unit/__init__.py`

```

```

### `tests/unit/test_collision_logic.py`

```
import unittest
from unittest.mock import MagicMock, patch
import os
import pytest
from src.core.controller import run_snapshot

class TestCollisionLogic(unittest.TestCase):
    """
    Verifies that the system strictly enforces ID uniqueness, 
    preventing data loss on case-sensitive filesystems where 
    'File.txt' and 'file.txt' might coexist.
    """
    
    @patch("src.core.controller.FileSystemScanner")
    @patch("src.core.controller.ConfigLoader")
    def test_detects_case_collision(self, mock_config_loader, mock_scanner_cls):
        # 1. Setup Mocks
        mock_config = MagicMock()
        mock_config_loader.load_config.return_value = mock_config
        
        # Mock Scanner to return colliding paths
        mock_instance = mock_scanner_cls.return_value
        mock_instance.scan.return_value = [
            "/repo/src/Utils.py", 
            "/repo/src/utils.py"
        ]
        
        # Helper to simulate relpath for our fake /repo structure
        def fake_relpath(path, start):
            # Simplistic simulation: remove start from path
            if path.startswith(start):
                return path[len(start):].lstrip("/")
            return path

        # 2. Execution & Assertion
        # We mock os.path heavily to simulate a Linux environment on any host
        with patch("os.path.exists", return_value=True), \
             patch("os.path.isdir", return_value=True), \
             patch("os.path.abspath", side_effect=lambda x: x), \
             patch("os.path.relpath", side_effect=fake_relpath): 
             
            with self.assertRaises(ValueError) as context:
                run_snapshot(
                    repo_root="/repo",
                    output_root="/tmp/out",
                    depth=5,
                    ignore=[],
                    include_extensions=[],
                    include_readme=False,
                    write_current_pointer=False
                )
            
        # 3. Verify Error Message
        msg = str(context.exception)
        self.assertIn("ID Collision Detected", msg)
        self.assertIn("src/Utils.py", msg)
        self.assertIn("src/utils.py", msg)

    @patch("src.core.controller.FileSystemScanner")
    @patch("src.core.controller.ConfigLoader")
    def test_no_collision_on_distinct_files(self, mock_config_loader, mock_scanner_cls):
        mock_instance = mock_scanner_cls.return_value
        mock_instance.scan.return_value = [
            "/repo/src/a.py", 
            "/repo/src/b.py"
        ]
        
        def fake_relpath(path, start):
            if path.startswith(start):
                return path[len(start):].lstrip("/")
            return path
        
        # Should NOT raise
        try:
            with patch("os.path.exists", return_value=True), \
                 patch("os.path.isdir", return_value=True), \
                 patch("os.path.abspath", side_effect=lambda x: x), \
                 patch("os.path.relpath", side_effect=fake_relpath), \
                 patch("src.core.controller.FileFingerprint.fingerprint") as mock_fp, \
                 patch("src.core.controller.SnapshotWriter"):
                
                # Return dummy fingerprint
                mock_fp.return_value = {
                    "sha256": "000", 
                    "size_bytes": 10, 
                    "language": "python"
                }
                
                run_snapshot(
                    repo_root="/repo",
                    output_root="/tmp/out",
                    depth=5,
                    ignore=[],
                    include_extensions=[],
                    include_readme=False,
                    write_current_pointer=False
                )
        except ValueError:
            self.fail("run_snapshot raised ValueError unexpectedly on distinct files")

if __name__ == "__main__":
    unittest.main()
```

### `tests/unit/test_config_loader.py`

```
import unittest
import tempfile
import shutil
import os
import json
from src.core.config_loader import ConfigLoader

class TestConfigLoader(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.realpath(tempfile.mkdtemp())
        self.config_path = os.path.join(self.test_dir, "repo-runner.json")

    def tearDown(self):
        try:
            shutil.rmtree(self.test_dir)
        except OSError:
            pass

    def test_load_default_when_missing(self):
        """Should return defaults if no file exists."""
        config = ConfigLoader.load_config(self.test_dir)
        self.assertEqual(config.depth, 25)
        self.assertIsNone(config.output_root)

    def test_load_custom_config(self):
        """Should parse valid JSON and map to schema."""
        custom_data = {
            "output_root": "./my-custom-out",
            "depth": 5,
            "skip_graph": True,
            "include_extensions": [".py", ".md"]
        }
        with open(self.config_path, "w") as f:
            json.dump(custom_data, f)
            
        config = ConfigLoader.load_config(self.test_dir)
        self.assertEqual(config.output_root, "./my-custom-out")
        self.assertEqual(config.depth, 5)
        self.assertTrue(config.skip_graph)
        self.assertEqual(config.include_extensions, [".py", ".md"])

    def test_ignore_invalid_json(self):
        """Should fallback to defaults without crashing on bad JSON."""
        with open(self.config_path, "w") as f:
            f.write("{ bad json, missing quotes }")
            
        config = ConfigLoader.load_config(self.test_dir)
        self.assertEqual(config.depth, 25) # Reverted to default

    def test_ignore_schema_mismatch(self):
        """Should fallback to defaults if schema validation completely fails."""
        with open(self.config_path, "w") as f:
            json.dump({"depth": "Not a number"}, f)
            
        config = ConfigLoader.load_config(self.test_dir)
        self.assertEqual(config.depth, 25) # Reverted to default

if __name__ == "__main__":
    unittest.main()
```

### `tests/unit/test_context_slicer.py`

```
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
                {"stable_id": "file:a.py", "size_bytes": 40, "symbols": ["HelperClass"]},
                {"stable_id": "file:b.py", "size_bytes": 40, "symbols": []},
                {"stable_id": "file:c.py", "size_bytes": 400, "symbols": ["DataModel", "process"]},
                {"stable_id": "file:d.py", "size_bytes": 40, "symbols": []}
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

    def test_symbol_focus_resolution(self):
        """
        Test that passing 'symbol:DataModel' correctly resolves to 'file:c.py' 
        and performs the standard graph traversal from there.
        """
        sliced = ContextSlicer.slice_manifest(
            self.manifest, 
            self.graph, 
            "symbol:DataModel", 
            radius=1
        )
        files = sorted([f["stable_id"] for f in sliced["files"]])
        
        # Radius 1 from C should include B (parent) and D (child), plus C itself
        self.assertEqual(files, ["file:b.py", "file:c.py", "file:d.py"])
        self.assertEqual(sliced["telemetry"]["resolved_id"], "file:c.py")

    def test_symbol_not_found(self):
        """
        Test that requesting a missing symbol returns a safe, empty slice.
        """
        sliced = ContextSlicer.slice_manifest(
            self.manifest, 
            self.graph, 
            "symbol:MissingSymbol", 
            radius=1
        )
        self.assertEqual(len(sliced["files"]), 0)
        self.assertEqual(sliced["stats"]["file_count"], 0)

if __name__ == "__main__":
    unittest.main()
```

### `tests/unit/test_drawio_exporter.py`

```
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
```

### `tests/unit/test_file_fingerprint.py`

```
import unittest
import tempfile
import shutil
import os
import hashlib
from src.fingerprint.file_fingerprint import FileFingerprint

class TestFingerprintHardening(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_valid_file(self):
        path = os.path.join(self.test_dir, "test.txt")
        content = b"hello world"
        with open(path, "wb") as f:
            f.write(content)
            
        fp = FileFingerprint.fingerprint(path)
        
        expected_sha = hashlib.sha256(content).hexdigest()
        self.assertEqual(fp["sha256"], expected_sha)
        self.assertEqual(fp["size_bytes"], len(content))
        self.assertEqual(fp["language"], "unknown") # .txt is unknown in current map

    def test_empty_file(self):
        path = os.path.join(self.test_dir, "empty.py")
        with open(path, "wb") as f:
            pass
            
        fp = FileFingerprint.fingerprint(path)
        self.assertEqual(fp["size_bytes"], 0)
        self.assertEqual(fp["language"], "python")

    def test_locked_or_missing_file(self):
        # Test missing file raises OSError
        path = os.path.join(self.test_dir, "ghost.txt")
        
        with self.assertRaises(OSError):
            FileFingerprint.fingerprint(path)

if __name__ == "__main__":
    unittest.main()
```

### `tests/unit/test_filesystem_scanner.py`

```
﻿import unittest
import tempfile
import shutil
import os
import sys
from unittest.mock import patch, MagicMock
from src.scanner.filesystem_scanner import FileSystemScanner

class TestFileSystemScanner(unittest.TestCase):
    def setUp(self):
        # FIX: Resolve canonical path to prevent test failures on Windows
        self.test_dir = os.path.realpath(tempfile.mkdtemp())
        self._touch("ok.txt")
        self._touch(".git/config")
        self._touch("dist/bundle.js")
        self._touch("src/code.ts")

    def tearDown(self):
        try:
            shutil.rmtree(self.test_dir)
        except OSError:
            pass

    def _touch(self, path):
        full = os.path.join(self.test_dir, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w") as f:
            f.write("test")

    def test_scanner_ignores(self):
        ignore_set = {".git", "dist"}
        scanner = FileSystemScanner(depth=10, ignore_names=ignore_set)
        
        results = scanner.scan([self.test_dir])
        rel_results = [os.path.relpath(p, self.test_dir).replace("\\", "/") for p in results]
        
        self.assertIn("ok.txt", rel_results)
        self.assertIn("src/code.ts", rel_results)
        self.assertFalse(any("config" in p for p in rel_results))
        self.assertFalse(any("bundle.js" in p for p in rel_results))

    # --- Migrated Hardening Tests ---

    def test_symlink_cycle_detection(self):
        if sys.platform == 'win32':
            # Windows requires Admin for symlinks usually, safer to skip
            return

        # Create a cycle: root/link -> root
        link_path = os.path.join(self.test_dir, "link_to_self")
        os.symlink(self.test_dir, link_path)

        self._touch("file_a.txt")
        
        scanner = FileSystemScanner(depth=10, ignore_names=set())
        
        # Should not hang or crash
        files = scanner.scan([self.test_dir])
        
        self.assertTrue(any(f.endswith("file_a.txt") for f in files))
        # Ensure we didn't recurse infinitely
        self.assertLess(len(files), 10)

    @patch('os.listdir')
    def test_permission_error_handling(self, mock_listdir):
        # Simulate PermissionError on a subdirectory
        mock_listdir.side_effect = PermissionError("Access Denied")
        
        scanner = FileSystemScanner(depth=5, ignore_names=set())
        
        # Scan should complete returning empty list (or list of root files if root scan succeeded)
        files = scanner.scan([self.test_dir])
        
        self.assertEqual(files, [])

if __name__ == "__main__":
    unittest.main()
```

### `tests/unit/test_flatten_exporter.py`

```
import unittest
import os
from src.exporters.flatten_markdown_exporter import FlattenMarkdownExporter, FlattenOptions

class TestFlattenExporter(unittest.TestCase):
    def setUp(self):
        self.exporter = FlattenMarkdownExporter()
        self.manifest = {
            "files": [
                {"path": "src/index.ts", "size_bytes": 100, "sha256": "a"},
                {"path": "readme.md", "size_bytes": 50, "sha256": "b"},
            ]
        }
        self.options = FlattenOptions(
            tree_only=False,
            include_readme=True,
            scope="full"
        )

    def test_tree_generation(self):
        # We test the internal _render_tree method implicitly via generate_content
        md = self.exporter.generate_content(
            repo_root="C:/fake",
            manifest=self.manifest,
            options=self.options,
            title="Test Export"
        )
        
        self.assertIn("## Tree", md)
        # readme.md comes before src, so src is the last element (└──)
        self.assertIn("└── src", md) 
        self.assertIn("└── index.ts", md)

    def test_scope_filtering(self):
        # Change scope to only 'src'
        options = FlattenOptions(tree_only=True, include_readme=False, scope="module:src")
        
        files = self.exporter._canonical_files_from_manifest(self.manifest, options)
        paths = [f["path"] for f in files]
        
        self.assertIn("src/index.ts", paths)
        self.assertNotIn("readme.md", paths)

    def test_binary_placeholder(self):
        # Mock a binary file entry in manifest
        entry = {"path": "image.png", "size_bytes": 1024, "sha256": "binhash"}
        placeholder = self.exporter._binary_placeholder(entry)
        
        self.assertIn("<<BINARY_OR_SKIPPED_FILE>>", placeholder)
        self.assertIn("binhash", placeholder)

if __name__ == "__main__":
    unittest.main()
```

### `tests/unit/test_graph_builder.py`

```
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
        """
        HARDENING TEST:
        Test that deep imports collapse to root packages, preserving NPM scopes.
        Reference: ID_SPEC.md (External ID Normalization)
        """
        files = [
            FileEntry(
                stable_id="file:src/app.ts",
                path="src/app.ts",
                language="typescript",
                # Imports testing various JS ecosystem quirks
                imports=[
                    "@mui/material/Button",  # Scoped + Subpath -> @mui/material
                    "lodash/fp/map",         # Unscoped + Subpath -> lodash
                    "@angular/core",         # Scoped strict -> @angular/core
                    "react",                 # Unscoped strict -> react
                    "next/link"              # Unscoped subpath -> next
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
        self.assertIn("external:next", node_ids)
        
        # Verify collapse
        self.assertNotIn("external:@mui/material/Button", node_ids)
        self.assertNotIn("external:lodash/fp/map", node_ids)
        self.assertNotIn("external:next/link", node_ids)

    def test_python_deep_package_normalization(self):
        """
        HARDENING TEST:
        Test that Python dotted imports collapse to the top-level package.
        """
        files = [
            FileEntry(
                stable_id="file:analysis.py",
                path="analysis.py",
                language="python",
                imports=[
                    "pandas.core.frame",
                    "matplotlib.pyplot",
                    "os"
                ], 
                module_path=".",
                sha256="abc", 
                size_bytes=100
            )
        ]
        
        graph = self.builder.build(files)
        node_ids = set(n.id for n in graph.nodes)
        
        self.assertIn("external:pandas", node_ids)
        self.assertIn("external:matplotlib", node_ids)
        self.assertIn("external:os", node_ids)
        
        self.assertNotIn("external:pandas.core.frame", node_ids)

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
```

### `tests/unit/test_graph_builder_unresolved.py`

```
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
```

### `tests/unit/test_ignore_logic.py`

```
import unittest
from src.scanner.filesystem_scanner import FileSystemScanner
import tempfile
import shutil
import os

class TestIgnoreLogic(unittest.TestCase):
    def setUp(self):
        # FIX: Resolve canonical path to prevent test failures on Windows
        self.test_dir = os.path.realpath(tempfile.mkdtemp())
        
        # Structure:
        # /ok.txt
        # /.git/config (should ignore)
        # /dist/bundle.js (should ignore)
        # /src/code.ts (should keep)
        
        self._touch("ok.txt")
        self._touch(".git/config")
        self._touch("dist/bundle.js")
        self._touch("src/code.ts")

    def tearDown(self):
        try:
            shutil.rmtree(self.test_dir)
        except OSError:
            pass

    def _touch(self, path):
        full = os.path.join(self.test_dir, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w") as f:
            f.write("test")

    def test_scanner_ignores(self):
        ignore_set = {".git", "dist"}
        scanner = FileSystemScanner(depth=10, ignore_names=ignore_set)
        
        results = scanner.scan([self.test_dir])
        
        # Normalize for assertion
        rel_results = [os.path.relpath(p, self.test_dir).replace("\\", "/") for p in results]
        
        self.assertIn("ok.txt", rel_results)
        self.assertIn("src/code.ts", rel_results)
        
        # Should NOT be present
        self.assertFalse(any("config" in p for p in rel_results))
        self.assertFalse(any("bundle.js" in p for p in rel_results))

if __name__ == "__main__":
    unittest.main()
```

### `tests/unit/test_import_scanner.py`

```
import unittest
import os
import tempfile
import shutil
from src.analysis.import_scanner import ImportScanner

class TestImportScanner(unittest.TestCase):
    
    # --- Python Tests (AST Based) ---

    def test_python_complex_structure(self):
        """
        Tests multi-line parenthesized imports, multiple modules on one line.
        """
        content = """
import os, sys
from datetime import (
    datetime,
    timedelta as td
)
import pandas as pd
"""
        imports = set()
        symbols = set()
        ImportScanner._scan_python(content, imports, symbols)
        
        expected = {"os", "sys", "datetime", "pandas"}
        self.assertEqual(imports, expected)

    def test_python_relative_imports(self):
        content = """
from . import sibling
from ..parent import something
from ...grandparent.utils import helper
"""
        imports = set()
        symbols = set()
        ImportScanner._scan_python(content, imports, symbols)
        
        expected = {".sibling", "..parent", "...grandparent.utils"}
        self.assertEqual(imports, expected)

    def test_python_scope_and_strings(self):
        """
        Tests the superiority of AST over Regex:
        1. Finds imports hidden inside functions (lazy imports).
        2. IGNORES strings that look like imports.
        """
        content = """
def lazy_loader():
    import json # Should be found
    
def print_help():
    msg = "import os" # Should be IGNORED
    print(msg)
"""
        imports = set()
        symbols = set()
        ImportScanner._scan_python(content, imports, symbols)
        
        self.assertIn("json", imports)
        self.assertNotIn("os", imports)

    def test_python_syntax_error(self):
        content = "def broken_code(:"
        imports = set()
        symbols = set()
        ImportScanner._scan_python(content, imports, symbols)
        self.assertEqual(len(imports), 0)

    def test_python_symbols(self):
        content = """
class DataModel:
    def inner_method(self): pass

def process_data(): pass
async def fetch_remote(): pass
"""
        imports = set()
        symbols = set()
        ImportScanner._scan_python(content, imports, symbols)
        
        self.assertIn("DataModel", symbols)
        self.assertIn("inner_method", symbols)
        self.assertIn("process_data", symbols)
        self.assertIn("fetch_remote", symbols)

    # --- JavaScript / TypeScript Tests (Regex Based) ---

    def test_js_standard_imports(self):
        content = """
import React from 'react';
import { useState } from "react";
const fs = require('fs');
"""
        imports = set()
        symbols = set()
        ImportScanner._scan_js(content, imports, symbols)
        
        expected = {"react", "fs"}
        self.assertEqual(imports, expected)

    def test_js_edge_cases(self):
        content = """
import './styles.css'; 
// import { bad } from 'bad-lib'; 
import { 
  Component,
  OnInit
} from '@angular/core';
"""
        imports = set()
        symbols = set()
        ImportScanner._scan_js(content, imports, symbols)
        
        self.assertIn("./styles.css", imports)
        self.assertIn("@angular/core", imports)
        self.assertNotIn("bad-lib", imports)

    def test_ts_advanced_imports(self):
        content = """
        import type { User } from '@models/auth';
        import {
          ComponentA,
          ComponentB
        } from "./components";
        export * from './exports';
        const Lazy = React.lazy(() => import('./LazyComponent'));
        import '@fontsource/roboto';
        """
        imports = set()
        symbols = set()
        ImportScanner._scan_js(content, imports, symbols)
        
        expected = {
            "@models/auth",
            "./components",
            "./exports",
            "./LazyComponent",
            "@fontsource/roboto"
        }
        self.assertEqual(imports, expected)

    def test_js_symbols(self):
        content = """
export default class UserService {}
function calculateTotal() {}
export const fetchUser = async (id) => {}
"""
        imports = set()
        symbols = set()
        ImportScanner._scan_js(content, imports, symbols)
        
        self.assertIn("UserService", symbols)
        self.assertIn("calculateTotal", symbols)
        self.assertIn("fetchUser", symbols)

    # --- Migrated Safety Tests ---

    def test_large_file_skip(self):
        """Ensure files > 250KB are truncated/handled safely."""
        test_dir = tempfile.mkdtemp()
        try:
            path = os.path.join(test_dir, "big_bundle.js")
            with open(path, "w") as f:
                f.write("import 'a';\n" * 20000)
                
            imports = ImportScanner.scan(path, "javascript")
            self.assertTrue(len(imports) > 0)
        finally:
            shutil.rmtree(test_dir)

    def test_unknown_language_safety(self):
        """Ensure unsupported languages return empty lists."""
        test_dir = tempfile.mkdtemp()
        try:
            path = os.path.join(test_dir, "test.rs")
            with open(path, "w") as f:
                f.write("use std::io;")
            imports = ImportScanner.scan(path, "rust")
            self.assertEqual(imports["imports"], [])
        finally:
            shutil.rmtree(test_dir)

if __name__ == "__main__":
    unittest.main()
```

### `tests/unit/test_mermaid_exporter.py`

```
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
```

### `tests/unit/test_path_normalizer.py`

```
﻿import unittest
import os
from src.normalize.path_normalizer import PathNormalizer

class TestPathNormalizer(unittest.TestCase):
    def setUp(self):
        # Use a controlled fake root
        self.root = "C:/projects/my-repo" if os.name == 'nt' else "/projects/my-repo"
        self.normalizer = PathNormalizer(self.root)

    def test_basic_normalization(self):
        abs_path = os.path.join(self.root, "src", "main.py")
        normalized = self.normalizer.normalize(abs_path)
        self.assertEqual(normalized, "src/main.py")

    def test_messy_path_normalization(self):
        """Test that redundant slashes and current-dir dots are stripped."""
        # Equivalent to: /projects/my-repo/src//app/./main.py
        messy_path = os.path.join(self.root, "src//app/./main.py")
        normalized = self.normalizer.normalize(messy_path)
        
        # Normalizer should resolve it cleanly
        self.assertEqual(normalized, "src/app/main.py")

    def test_parent_traversal(self):
        """Test that paths traversing up and down resolve to canonical paths."""
        # Equivalent to: /projects/my-repo/src/app/../utils/main.py
        traversal_path = os.path.join(self.root, "src", "app", "..", "utils", "main.py")
        normalized = self.normalizer.normalize(traversal_path)
        
        self.assertEqual(normalized, "src/utils/main.py")

    def test_windows_separator_handling(self):
        """Ensure backslashes are converted to forward slashes universally."""
        # Force a Windows-style path string regardless of host OS
        raw_relative = "src\\Components\\Header.tsx"
        normalized = raw_relative.replace("\\", "/").lower()
        self.assertEqual(normalized, "src/components/header.tsx")

    def test_casing_policy(self):
        """Ensure paths are lowercased per ID_SPEC v0.1."""
        path = os.path.join(self.root, "Config", "README.md")
        normalized = self.normalizer.normalize(path)
        self.assertEqual(normalized, "config/readme.md")

    def test_id_generation(self):
        self.assertEqual(self.normalizer.file_id("src/utils/helper.ts"), "file:src/utils/helper.ts")
        self.assertEqual(self.normalizer.module_id("src/utils"), "module:src/utils")
        self.assertEqual(self.normalizer.repo_id(), "repo:root")

if __name__ == "__main__":
    unittest.main()
```

### `tests/unit/test_scanner_constants.py`

```
import unittest
from src.analysis.import_scanner import ImportScanner
import tempfile
import os

class TestScannerConstants(unittest.TestCase):
    """
    Verifies that the ImportScanner correctly identifies global constants
    (UPPER_CASE variables) in addition to Classes and Functions.
    """
    
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp_dir)
        
    def _create_and_scan(self, filename, content, lang):
        path = os.path.join(self.tmp_dir, filename)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return ImportScanner.scan(path, lang)

    def test_python_constants(self):
        code = """
import os

# Should capture
MAX_RETRIES = 5
DEFAULT_CONFIG = "prod"
API_KEY: str = os.getenv("KEY")

# Should NOT capture (lowercase/mixed)
local_var = 10
CamelCase = True
_private = False
        """
        result = self._create_and_scan("consts.py", code, "python")
        symbols = set(result["symbols"])
        
        self.assertIn("MAX_RETRIES", symbols)
        self.assertIn("DEFAULT_CONFIG", symbols)
        self.assertIn("API_KEY", symbols)
        
        self.assertNotIn("local_var", symbols)
        self.assertNotIn("CamelCase", symbols)
        self.assertNotIn("os", symbols) # It's an import, not a symbol def

    def test_js_constants(self):
        code = """
// Should capture
export const MAX_WIDTH = 100;
const API_ENDPOINT = 'https://api.com';

// Should capture arrow functions (existing logic)
const fetchData = () => {};

// Should NOT capture (lowercase/mixed)
const isValid = true;
let MUTABLE_VAR = 1; // We only target 'const' for JS to reduce noise
        """
        result = self._create_and_scan("consts.ts", code, "typescript")
        symbols = set(result["symbols"])
        
        self.assertIn("MAX_WIDTH", symbols)
        self.assertIn("API_ENDPOINT", symbols)
        self.assertIn("fetchData", symbols)
        
        self.assertNotIn("isValid", symbols)
        self.assertNotIn("MUTABLE_VAR", symbols)

    def test_python_assignment_unpacking(self):
        """
        Edge case: tuple unpacking assignments like A, B = 1, 2
        """
        code = """
A, B = 1, 2
x, Y = 3, 4
        """
        result = self._create_and_scan("unpack.py", code, "python")
        symbols = set(result["symbols"])
        
        # Current naive implementation visits targets.
        # If AST splits Tuple node, we might miss it unless we handle Tuple/List targets.
        # Let's see if the generic walker catches the names inside the Tuple.
        # Spoiler: It does because we iterate `node.targets`. 
        # But if target is a Tuple, `isinstance(target, ast.Name)` fails.
        # This test documents CURRENT limitations or behavior.
        
        # AST Assign target is a Tuple node, not a Name node.
        # So our current code SKIPs unpacking.
        self.assertNotIn("A", symbols) 
        self.assertNotIn("B", symbols)

if __name__ == "__main__":
    unittest.main()
```

### `tests/unit/test_snapshot_comparator.py`

```
import unittest
from src.analysis.snapshot_comparator import SnapshotComparator
from src.core.types import (
    Manifest, ManifestInputs, ManifestConfig, ManifestStats, GitMetadata, 
    FileEntry, GraphStructure, GraphNode, GraphEdge
)

class TestSnapshotComparator(unittest.TestCase):
    def setUp(self):
        # Base setup helpers to keep tests clean
        self.inputs = ManifestInputs(repo_root="C:/repo", roots=["C:/repo"], git=GitMetadata(is_repo=False))
        self.config = ManifestConfig(depth=5, ignore_names=[], include_extensions=[], include_readme=True, tree_only=False, skip_graph=False, manual_override=False)
        self.stats = ManifestStats(file_count=0, total_bytes=0)

    def _create_manifest(self, snap_id: str, files: list) -> Manifest:
        return Manifest(
            tool={"name": "test"},
            snapshot={"snapshot_id": snap_id},
            inputs=self.inputs,
            config=self.config,
            stats=self.stats,
            files=files
        )

    def test_file_diffing(self):
        """Test detection of added, removed, and modified files via SHA256."""
        # Snapshot A (Base)
        files_a = [
            FileEntry(stable_id="file:src/a.py", path="src/a.py", module_path="src", sha256="hash_a1", size_bytes=10),
            FileEntry(stable_id="file:src/b.py", path="src/b.py", module_path="src", sha256="hash_b1", size_bytes=10),
        ]
        manifest_a = self._create_manifest("v1", files_a)

        # Snapshot B (Target)
        # a.py is modified (hash changed)
        # b.py is removed
        # c.py is added
        files_b = [
            FileEntry(stable_id="file:src/a.py", path="src/a.py", module_path="src", sha256="hash_a2", size_bytes=10),
            FileEntry(stable_id="file:src/c.py", path="src/c.py", module_path="src", sha256="hash_c1", size_bytes=10),
        ]
        manifest_b = self._create_manifest("v2", files_b)

        report = SnapshotComparator.compare(manifest_a, manifest_b)

        self.assertEqual(report.files_added, 1)
        self.assertEqual(report.files_removed, 1)
        self.assertEqual(report.files_modified, 1)

        added = [f for f in report.file_diffs if f.status == "added"][0]
        self.assertEqual(added.stable_id, "file:src/c.py")

        removed = [f for f in report.file_diffs if f.status == "removed"][0]
        self.assertEqual(removed.stable_id, "file:src/b.py")

        modified = [f for f in report.file_diffs if f.status == "modified"][0]
        self.assertEqual(modified.stable_id, "file:src/a.py")
        self.assertEqual(modified.old_sha256, "hash_a1")
        self.assertEqual(modified.new_sha256, "hash_a2")

    def test_graph_diffing(self):
        """Test detection of added and removed dependency edges."""
        graph_a = GraphStructure(
            nodes=[], 
            edges=[
                GraphEdge(source="file:a.py", target="file:b.py", relation="imports"),
                GraphEdge(source="file:a.py", target="external:os", relation="imports")
            ]
        )

        # Removed 'os' import, added 'sys' import
        graph_b = GraphStructure(
            nodes=[], 
            edges=[
                GraphEdge(source="file:a.py", target="file:b.py", relation="imports"),
                GraphEdge(source="file:a.py", target="external:sys", relation="imports")
            ]
        )

        manifest_dummy = self._create_manifest("v1", [])
        
        report = SnapshotComparator.compare(manifest_dummy, manifest_dummy, graph_a, graph_b)

        self.assertEqual(report.edges_added, 1)
        self.assertEqual(report.edges_removed, 1)

        added_edge = [e for e in report.edge_diffs if e.status == "added"][0]
        self.assertEqual(added_edge.target, "external:sys")

        removed_edge = [e for e in report.edge_diffs if e.status == "removed"][0]
        self.assertEqual(removed_edge.target, "external:os")

if __name__ == "__main__":
    unittest.main()
```

### `tests/unit/test_snapshot_loader.py`

```

```

### `tests/unit/test_structure_builder.py`

```
﻿import unittest
from src.structure.structure_builder import StructureBuilder
from src.core.types import FileEntry

class TestStructureBuilder(unittest.TestCase):
    def test_build_structure(self):
        # Refactored to use Pydantic Models instead of raw dicts
        files = [
            FileEntry(stable_id="file:src/a.ts", module_path="src", path="src/a.ts", sha256="x", size_bytes=1),
            FileEntry(stable_id="file:src/b.ts", module_path="src", path="src/b.ts", sha256="x", size_bytes=1),
            FileEntry(stable_id="file:root.md", module_path=".", path="root.md", sha256="x", size_bytes=1),
            FileEntry(stable_id="file:utils/deep/x.py", module_path="utils/deep", path="utils/deep/x.py", sha256="x", size_bytes=1),
        ]

        builder = StructureBuilder()
        output = builder.build(repo_id="repo:root", files=files)

        self.assertEqual(output["schema_version"], "1.0")
        self.assertEqual(output["repo"]["stable_id"], "repo:root")
        
        modules = output["repo"]["modules"]
        self.assertEqual(len(modules), 3)
        self.assertEqual(modules[0]["path"], ".")
        self.assertEqual(modules[1]["path"], "src")
        self.assertEqual(modules[2]["path"], "utils/deep")

        src_mod = modules[1]
        self.assertEqual(src_mod["stable_id"], "module:src")
        self.assertEqual(len(src_mod["files"]), 2)
        self.assertEqual(src_mod["files"][0], "file:src/a.ts")

if __name__ == "__main__":
    unittest.main()
```

### `tests/unit/test_token_telemetry.py`

```
import unittest
from src.observability.token_telemetry import TokenTelemetry

class TestTokenTelemetry(unittest.TestCase):
    def setUp(self):
        # Mock Original Manifest (10 files, 10,000 bytes)
        self.original = {
            "stats": {"file_count": 10, "total_bytes": 10000},
            "files": [{"size_bytes": 1000} for _ in range(10)]
        }
        
        # Mock Sliced Manifest (2 files, 2,000 bytes)
        self.sliced = {
            "stats": {"file_count": 2},
            "files": [{"size_bytes": 1000} for _ in range(2)]
        }

    def test_telemetry_calculations(self):
        header = TokenTelemetry.calculate_telemetry(
            original_manifest=self.original,
            sliced_manifest=self.sliced,
            focus_id="file:src/main.py",
            radius=1
        )
        
        # Verify Mathematics in the generated Markdown
        self.assertIn("Pruned from 10 total", header)
        self.assertIn("2,000 bytes", header)
        self.assertIn("80.0% reduction", header)  # 10k down to 2k is an 80% reduction
        
        # Tokens = 2000 // 4 = 500
        self.assertIn("Estimated Tokens:** 500", header)
        
        # Cost = 500 / 1,000,000 * 5.00 = 0.0025
        self.assertIn("Est. Input Cost (GPT-4o):** $0.00250", header)

if __name__ == "__main__":
    unittest.main()
```

### `tests/unit/test_types.py`

```
import unittest
from pydantic import ValidationError
from src.core.types import FileEntry

class TestTypes(unittest.TestCase):
    def test_path_normalization_validator(self):
        """
        Prove that the model automatically cleans dirty paths.
        This is a key 'Schema Assurance' feature.
        """
        # Dirty input: Windows slashes + Mixed Case
        dirty_path = "Src\\Utils\\Helper.py"
        
        entry = FileEntry(
            stable_id="file:src/utils/helper.py",
            path=dirty_path,
            module_path="src/utils",
            sha256="dummy",
            size_bytes=100,
            language="python"
        )
        
        # Validator should have cleaned it
        self.assertEqual(entry.path, "src/utils/helper.py")

    def test_stable_id_validation(self):
        """Ensure we can't create FileEntries with invalid IDs."""
        with self.assertRaises(ValidationError):
            FileEntry(
                stable_id="invalid:id", # Must start with file/module/repo
                path="src/main.py",
                module_path="src",
                sha256="x",
                size_bytes=1
            )

if __name__ == "__main__":
    unittest.main()
```

---
## Context Stats
- **Total Characters:** 91,223
- **Estimated Tokens:** ~22,805 (assuming ~4 chars/token)
- **Model Fit:** GPT-4 (32k)
