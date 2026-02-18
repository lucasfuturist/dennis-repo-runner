import unittest
from src.scanner.filesystem_scanner import FileSystemScanner
import tempfile
import shutil
import os

class TestIgnoreLogic(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        
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
        shutil.rmtree(self.test_dir)

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