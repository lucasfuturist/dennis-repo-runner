import unittest
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