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