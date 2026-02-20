import re
import ast
import os
from typing import List, Set

class ImportScanner:
    # --- JavaScript / TypeScript Patterns (Regex) ---
    
    # 1. import ... from 'x' (Supports multi-line via [\s\S]*?)
    _JS_IMPORT_FROM = re.compile(r'import\s+[\s\S]*?from\s+[\'"]([^\'"]+)[\'"]')
    
    # 2. import 'x' (Side effect)
    _JS_IMPORT_SIDE_EFFECT = re.compile(r'import\s+[\'"]([^\'"]+)[\'"]')
    
    # 3. require('x')
    _JS_REQUIRE = re.compile(r'require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)')

    # 4. export ... from 'x' (Re-exports)
    _JS_EXPORT_FROM = re.compile(r'export\s+[\s\S]*?from\s+[\'"]([^\'"]+)[\'"]')

    # 5. import('x') (Dynamic imports)
    _JS_DYNAMIC_IMPORT = re.compile(r'import\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)')

    # Comment Stripping
    _JS_BLOCK_COMMENT = re.compile(r'/\*[\s\S]*?\*/')
    _JS_LINE_COMMENT = re.compile(r'//.*')

    @staticmethod
    def scan(path: str, language: str) -> List[str]:
        """
        Scans a file for import statements based on its language.
        Returns a sorted list of unique import targets.
        """
        if language not in ("python", "javascript", "typescript"):
            return []

        try:
            # Limit read size to 1MB
            # Use 'utf-8-sig' to automatically consume BOM on Windows files
            with open(path, 'r', encoding='utf-8-sig', errors='ignore') as f:
                content = f.read(1_000_000)
        except OSError:
            return []

        imports: Set[str] = set()

        if language == "python":
            ImportScanner._scan_python(content, imports)
        elif language in ("javascript", "typescript"):
            ImportScanner._scan_js(content, imports)

        return sorted(list(imports))

    @staticmethod
    def _scan_python(content: str, imports: Set[str]):
        """
        Uses Python's native AST to extract imports reliably.
        """
        try:
            tree = ast.parse(content)
        except SyntaxError:
            # If the file is invalid Python, we simply skip scanning imports
            # rather than crashing the tool.
            return

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            
            elif isinstance(node, ast.ImportFrom):
                # Handle 'from x import y' -> module='x'
                # Handle 'from . import y' -> module=None, level=1
                
                module_name = node.module or ""
                
                # Reconstruct relative imports
                # level 1 = ., level 2 = .., etc.
                if node.level > 0:
                    prefix = "." * node.level
                    
                    # Special Case: 'from . import sibling'
                    # If module is empty but we have a level, the 'names' are likely submodules.
                    if not module_name:
                        for alias in node.names:
                            imports.add(prefix + alias.name)
                        continue
                    
                    module_name = prefix + module_name
                
                if module_name:
                    imports.add(module_name)

    @staticmethod
    def _scan_js(content: str, imports: Set[str]):
        """
        Uses Regex heuristics to extract JS/TS imports.
        """
        # 1. Strip Comments to avoid false positives
        clean_content = ImportScanner._JS_BLOCK_COMMENT.sub('', content)
        clean_content = ImportScanner._JS_LINE_COMMENT.sub('', clean_content)

        # 2. Run Regex on the full cleaned content
        
        # import ... from '...'
        for match in ImportScanner._JS_IMPORT_FROM.finditer(clean_content):
            imports.add(match.group(1))
            
        # import '...' (side effect)
        for match in ImportScanner._JS_IMPORT_SIDE_EFFECT.finditer(clean_content):
            full_match = match.group(0)
            # Heuristic: avoid capturing the "import" part of a "from" statement
            if "from" not in full_match: 
                imports.add(match.group(1))

        # require('...')
        for match in ImportScanner._JS_REQUIRE.finditer(clean_content):
            imports.add(match.group(1))

        # export ... from '...'
        for match in ImportScanner._JS_EXPORT_FROM.finditer(clean_content):
            imports.add(match.group(1))

        # import('...')
        for match in ImportScanner._JS_DYNAMIC_IMPORT.finditer(clean_content):
            imports.add(match.group(1))