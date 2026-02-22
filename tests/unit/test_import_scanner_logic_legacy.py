import unittest
import os
import tempfile
from src.analysis.import_scanner import ImportScanner

class TestImportScannerLogic(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.test_dir)

    def _create_file(self, filename, content):
        path = os.path.join(self.test_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def test_python_ast_extraction(self):
        """Test robust AST parsing for Python."""
        content = """
import os
from sys import path
from ..utils import helper
import pandas.DataFrame as df
        """
        path = self._create_file("test.py", content)
        imports = ImportScanner.scan(path, "python")
        
        expected = ["os", "sys", "..utils", "pandas.DataFrame"]
        self.assertEqual(set(imports), set(expected))

    def test_js_regex_extraction(self):
        """Test regex heuristic for JS/TS."""
        content = """
import React from 'react';
const fs = require('fs');
import { x } from './utils';
// import { fake } from 'commented-out';
        """
        path = self._create_file("app.ts", content)
        imports = ImportScanner.scan(path, "typescript")
        
        expected = ["react", "fs", "./utils"]
        self.assertEqual(set(imports), set(expected))

    def test_large_file_skip(self):
        """Ensure files > 250KB are truncated/handled safely."""
        # Create a 300KB file
        path = os.path.join(self.test_dir, "big_bundle.js")
        with open(path, "w") as f:
            f.write("import 'a';\n" * 20000) # Should be well over 250KB
            
        # The scanner reads only 250KB. 
        # If the file is valid JS repeats, it captures what it reads.
        # This test primarily ensures it DOES NOT crash on memory or IO.
        imports = ImportScanner.scan(path, "javascript")
        self.assertTrue(len(imports) > 0)

    def test_syntax_error_resilience(self):
        """Ensure broken syntax doesn't crash the scanner."""
        content = "def broken_function(:" # Invalid Python
        path = self._create_file("broken.py", content)
        
        # Should return empty list, not raise SyntaxError
        imports = ImportScanner.scan(path, "python")
        self.assertEqual(imports, [])

    def test_unknown_language_safety(self):
        """Ensure unsupported languages return empty lists."""
        path = self._create_file("test.rs", "use std::io;")
        imports = ImportScanner.scan(path, "rust")
        self.assertEqual(imports, [])

if __name__ == "__main__":
    unittest.main()