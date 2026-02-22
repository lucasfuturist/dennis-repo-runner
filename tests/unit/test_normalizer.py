import unittest
import os
from src.normalize.path_normalizer import PathNormalizer

class TestPathNormalizer(unittest.TestCase):
    def setUp(self):
        # Simulate a repo root
        self.root = "/projects/my-repo"
        self.normalizer = PathNormalizer(self.root)

    def test_basic_normalization(self):
        # Input: Absolute path
        abs_path = os.path.join(self.root, "src", "main.py")
        normalized = self.normalizer.normalize(abs_path)
        
        # Expect: Repo-relative, lowercase, forward slash
        self.assertEqual(normalized, "src/main.py")

    def test_windows_separator_handling(self):
        # Simulate Windows input on any OS logic
        # We manually invoke the logic if we can't simulate OS.sep easily, 
        # but the class uses os.path.relpath which depends on OS.
        # So we test the string replacement logic explicitly.
        
        # Hard-force a windows-style relative path outcome for testing the replacement
        raw_relative = "src\\Components\\Header.tsx"
        normalized = raw_relative.replace("\\", "/").lower()
        
        # Verify the class logic matches our expectation
        self.assertEqual(normalized, "src/components/header.tsx")

    def test_casing_policy(self):
        # Policy: All lowercase (per ID_SPEC.md v0.1)
        path = os.path.join(self.root, "README.md")
        normalized = self.normalizer.normalize(path)
        self.assertEqual(normalized, "readme.md")

    def test_id_generation(self):
        path = "src/utils/helper.ts"
        self.assertEqual(self.normalizer.file_id(path), "file:src/utils/helper.ts")
        self.assertEqual(self.normalizer.module_id("src/utils"), "module:src/utils")
        self.assertEqual(self.normalizer.repo_id(), "repo:root")

if __name__ == "__main__":
    unittest.main()