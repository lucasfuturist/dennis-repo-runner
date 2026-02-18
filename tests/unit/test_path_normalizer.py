import unittest
import os
from src.normalize.path_normalizer import PathNormalizer

class TestPathNormalizer(unittest.TestCase):
    def setUp(self):
        self.root = "C:\\projects\\my-repo"
        self.normalizer = PathNormalizer(self.root)

    def test_basic_normalization(self):
        # Input: Absolute path
        abs_path = os.path.join(self.root, "src", "main.py")
        normalized = self.normalizer.normalize(abs_path)
        self.assertEqual(normalized, "src/main.py")

    def test_windows_separator_handling(self):
        # Force a windows-style relative path string
        raw_relative = "src\\Components\\Header.tsx"
        normalized = raw_relative.replace("\\", "/").lower()
        self.assertEqual(normalized, "src/components/header.tsx")

    def test_casing_policy(self):
        path = os.path.join(self.root, "README.md")
        normalized = self.normalizer.normalize(path)
        self.assertEqual(normalized, "readme.md")

    def test_id_generation(self):
        self.assertEqual(self.normalizer.file_id("src/utils/helper.ts"), "file:src/utils/helper.ts")
        self.assertEqual(self.normalizer.module_id("src/utils"), "module:src/utils")
        self.assertEqual(self.normalizer.repo_id(), "repo:root")

if __name__ == "__main__":
    unittest.main()
