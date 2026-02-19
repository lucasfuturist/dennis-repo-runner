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