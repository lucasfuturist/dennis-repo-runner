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