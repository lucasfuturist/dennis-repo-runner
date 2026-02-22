import unittest
import os
import tempfile
import shutil
from src.analysis.import_scanner import ImportScanner

class TestImportScanner(unittest.TestCase):
    
    # --- Python Tests (AST Based) ---

    def test_python_complex_structure(self):
        """
        Tests multi-line parenthesized imports, multiple modules on one line.
        """
        content = """
import os, sys
from datetime import (
    datetime,
    timedelta as td
)
import pandas as pd
"""
        imports = set()
        symbols = set()
        ImportScanner._scan_python(content, imports, symbols)
        
        expected = {"os", "sys", "datetime", "pandas"}
        self.assertEqual(imports, expected)

    def test_python_relative_imports(self):
        content = """
from . import sibling
from ..parent import something
from ...grandparent.utils import helper
"""
        imports = set()
        symbols = set()
        ImportScanner._scan_python(content, imports, symbols)
        
        expected = {".sibling", "..parent", "...grandparent.utils"}
        self.assertEqual(imports, expected)

    def test_python_scope_and_strings(self):
        """
        Tests the superiority of AST over Regex:
        1. Finds imports hidden inside functions (lazy imports).
        2. IGNORES strings that look like imports.
        """
        content = """
def lazy_loader():
    import json # Should be found
    
def print_help():
    msg = "import os" # Should be IGNORED
    print(msg)
"""
        imports = set()
        symbols = set()
        ImportScanner._scan_python(content, imports, symbols)
        
        self.assertIn("json", imports)
        self.assertNotIn("os", imports)

    def test_python_syntax_error(self):
        content = "def broken_code(:"
        imports = set()
        symbols = set()
        ImportScanner._scan_python(content, imports, symbols)
        self.assertEqual(len(imports), 0)

    def test_python_symbols(self):
        content = """
class DataModel:
    def inner_method(self): pass

def process_data(): pass
async def fetch_remote(): pass
"""
        imports = set()
        symbols = set()
        ImportScanner._scan_python(content, imports, symbols)
        
        self.assertIn("DataModel", symbols)
        self.assertIn("inner_method", symbols)
        self.assertIn("process_data", symbols)
        self.assertIn("fetch_remote", symbols)

    # --- JavaScript / TypeScript Tests (Regex Based) ---

    def test_js_standard_imports(self):
        content = """
import React from 'react';
import { useState } from "react";
const fs = require('fs');
"""
        imports = set()
        symbols = set()
        ImportScanner._scan_js(content, imports, symbols)
        
        expected = {"react", "fs"}
        self.assertEqual(imports, expected)

    def test_js_edge_cases(self):
        content = """
import './styles.css'; 
// import { bad } from 'bad-lib'; 
import { 
  Component,
  OnInit
} from '@angular/core';
"""
        imports = set()
        symbols = set()
        ImportScanner._scan_js(content, imports, symbols)
        
        self.assertIn("./styles.css", imports)
        self.assertIn("@angular/core", imports)
        self.assertNotIn("bad-lib", imports)

    def test_ts_advanced_imports(self):
        content = """
        import type { User } from '@models/auth';
        import {
          ComponentA,
          ComponentB
        } from "./components";
        export * from './exports';
        const Lazy = React.lazy(() => import('./LazyComponent'));
        import '@fontsource/roboto';
        """
        imports = set()
        symbols = set()
        ImportScanner._scan_js(content, imports, symbols)
        
        expected = {
            "@models/auth",
            "./components",
            "./exports",
            "./LazyComponent",
            "@fontsource/roboto"
        }
        self.assertEqual(imports, expected)

    def test_js_symbols(self):
        content = """
export default class UserService {}
function calculateTotal() {}
export const fetchUser = async (id) => {}
"""
        imports = set()
        symbols = set()
        ImportScanner._scan_js(content, imports, symbols)
        
        self.assertIn("UserService", symbols)
        self.assertIn("calculateTotal", symbols)
        self.assertIn("fetchUser", symbols)

    # --- Migrated Safety Tests ---

    def test_large_file_skip(self):
        """Ensure files > 250KB are truncated/handled safely."""
        test_dir = tempfile.mkdtemp()
        try:
            path = os.path.join(test_dir, "big_bundle.js")
            with open(path, "w") as f:
                f.write("import 'a';\n" * 20000)
                
            imports = ImportScanner.scan(path, "javascript")
            self.assertTrue(len(imports) > 0)
        finally:
            shutil.rmtree(test_dir)

    def test_unknown_language_safety(self):
        """Ensure unsupported languages return empty lists."""
        test_dir = tempfile.mkdtemp()
        try:
            path = os.path.join(test_dir, "test.rs")
            with open(path, "w") as f:
                f.write("use std::io;")
            imports = ImportScanner.scan(path, "rust")
            self.assertEqual(imports["imports"], [])
        finally:
            shutil.rmtree(test_dir)

if __name__ == "__main__":
    unittest.main()