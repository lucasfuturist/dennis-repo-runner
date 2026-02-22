import unittest
from src.analysis.import_scanner import ImportScanner

class TestImportScanner(unittest.TestCase):
    
    # --- Python Tests (AST Based) ---

    def test_python_complex_structure(self):
        """
        Tests:
        1. Multi-line parenthesized imports (common in big projects).
        2. Multiple modules on one line.
        3. Aliasing (should capture the *source*, not the alias).
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
        """
        Tests relative imports used in modular monoliths.
        .  = current directory
        .. = parent
        """
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
    
# import commented_out # Should be IGNORED
"""
        imports = set()
        symbols = set()
        ImportScanner._scan_python(content, imports, symbols)
        
        self.assertIn("json", imports)
        self.assertNotIn("os", imports)
        self.assertNotIn("commented_out", imports)

    def test_python_syntax_error(self):
        """
        Ensure the tool is robust against broken files (e.g., during a merge conflict).
        """
        content = "def broken_code(:"
        imports = set()
        symbols = set()
        
        # Should catch SyntaxError silently
        ImportScanner._scan_python(content, imports, symbols)
        self.assertEqual(len(imports), 0)

    def test_python_symbols(self):
        """
        Verify that Classes, Functions, and Async Functions are extracted.
        """
        content = """
class DataModel:
    def inner_method(self):
        pass

def process_data():
    pass

async def fetch_remote():
    pass
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
import { useState, useEffect } from "react";
const fs = require('fs');
"""
        imports = set()
        symbols = set()
        ImportScanner._scan_js(content, imports, symbols)
        
        expected = {"react", "fs"}
        self.assertEqual(imports, expected)

    def test_js_edge_cases(self):
        """
        Tests:
        1. Side-effect imports (import 'css').
        2. Multi-line imports (Angular/NestJS style).
        3. Comments (should not pick up commented imports).
        """
        content = """
import './styles.css'; // Side effect

// import { bad } from 'bad-lib'; 

import { 
  Component,
  OnInit
} from '@angular/core';

/* 
  import { ignore } from 'block-comment'; 
*/
"""
        imports = set()
        symbols = set()
        ImportScanner._scan_js(content, imports, symbols)
        
        self.assertIn("./styles.css", imports)
        self.assertIn("@angular/core", imports)
        
        # Verify comments are stripped
        self.assertNotIn("bad-lib", imports)
        self.assertNotIn("block-comment", imports)

    def test_ts_advanced_imports(self):
        """
        TypeScript 'import type', dynamic imports, and complex destructuring
        must register accurately without greedy regex bleed.
        """
        content = """
        import type { User, Session } from '@models/auth';
        import {
          ComponentA,
          ComponentB
        } from "./components";
        export * from './exports';
        export { default as Utils } from './utils';
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
            "./utils",
            "./LazyComponent",
            "@fontsource/roboto"
        }
        self.assertEqual(imports, expected)

    def test_js_symbols(self):
        """
        Verify that JS Classes, Functions, and Arrow Functions are extracted.
        """
        content = """
export default class UserService {}
function calculateTotal() {}
export const fetchUser = async (id) => {}
const ignoredVar = 42;
"""
        imports = set()
        symbols = set()
        ImportScanner._scan_js(content, imports, symbols)
        
        self.assertIn("UserService", symbols)
        self.assertIn("calculateTotal", symbols)
        self.assertIn("fetchUser", symbols)
        self.assertNotIn("ignoredVar", symbols)

    def test_js_advanced_symbols(self):
        """
        Verify abstract classes and generator functions are caught.
        """
        content = """
        export abstract class BaseService {}
        function* myGenerator() {}
        const process = async (data) => {}
        """
        imports = set()
        symbols = set()
        ImportScanner._scan_js(content, imports, symbols)
        
        self.assertIn("BaseService", symbols)
        self.assertIn("myGenerator", symbols)
        self.assertIn("process", symbols)

if __name__ == "__main__":
    unittest.main()