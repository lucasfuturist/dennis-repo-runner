import re
import ast
from typing import List, Set

class ImportScanner:
    # --- JavaScript / TypeScript Patterns (Regex) ---
    
    # 1. import ... from 'x' 
    # Hardened: limited wildcard to 1000 chars to prevent catastrophic backtracking (ReDoS)
    # if a file has 'import' but is missing the 'from' keyword.
    _JS_IMPORT_FROM = re.compile(r'import\s+[\s\S]{0,1000}?\s+from\s+[\'"]([^\'"]+)[\'"]')
    
    # 2. import 'x' (Side effect)
    _JS_IMPORT_SIDE_EFFECT = re.compile(r'import\s+[\'"]([^\'"]+)[\'"]')
    
    # 3. require('x')
    _JS_REQUIRE = re.compile(r'require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)')

    # 4. export ... from 'x' (Re-exports)
    # Hardened: limited wildcard to 1000 chars
    _JS_EXPORT_FROM = re.compile(r'export\s+[\s\S]{0,1000}?\s+from\s+[\'"]([^\'"]+)[\'"]')

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
            # Limit read size to 250KB for dependency scanning.
            # Files larger than this are almost always minified bundles, compiled outputs, 
            # or data dictionaries. Parsing them risks MemoryErrors and ReDoS hangs.
            with open(path, 'r', encoding='utf-8-sig', errors='ignore') as f:
                content = f.read(250_000)
        except OSError:
            return []

        imports: Set[str] = set()

        # Hardened Execution Boundary
        # We must never crash the SnapshotWriter just because a single file has 
        # malformed syntax, recursive AST loops, or regex blowups.
        try:
            if language == "python":
                ImportScanner._scan_python(content, imports)
            elif language in ("javascript", "typescript"):
                ImportScanner._scan_js(content, imports)
        except Exception:
            # Fail safely. A partial/missing import graph is better than a failed snapshot.
            pass

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
            return

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            
            elif isinstance(node, ast.ImportFrom):
                module_name = node.module or ""
                
                # Reconstruct relative imports
                if node.level > 0:
                    prefix = "." * node.level
                    
                    # Special Case: 'from . import sibling'
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
        for match in ImportScanner._JS_IMPORT_FROM.finditer(clean_content):
            imports.add(match.group(1))
            
        for match in ImportScanner._JS_IMPORT_SIDE_EFFECT.finditer(clean_content):
            full_match = match.group(0)
            if "from" not in full_match: 
                imports.add(match.group(1))

        for match in ImportScanner._JS_REQUIRE.finditer(clean_content):
            imports.add(match.group(1))

        for match in ImportScanner._JS_EXPORT_FROM.finditer(clean_content):
            imports.add(match.group(1))

        for match in ImportScanner._JS_DYNAMIC_IMPORT.finditer(clean_content):
            imports.add(match.group(1))