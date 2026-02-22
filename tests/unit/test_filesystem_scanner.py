import unittest
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