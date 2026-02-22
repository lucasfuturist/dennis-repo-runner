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