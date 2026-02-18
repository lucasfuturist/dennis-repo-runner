import unittest
from src.structure.structure_builder import StructureBuilder

class TestStructureBuilder(unittest.TestCase):
    def test_build_structure(self):
        files = [
            {"stable_id": "file:src/a.ts", "module_path": "src", "path": "src/a.ts"},
            {"stable_id": "file:src/b.ts", "module_path": "src", "path": "src/b.ts"},
            {"stable_id": "file:root.md", "module_path": ".", "path": "root.md"},
            {"stable_id": "file:utils/deep/x.py", "module_path": "utils/deep", "path": "utils/deep/x.py"},
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
