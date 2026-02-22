import re
import ast
from typing import List, Set, Dict

class ImportScanner:
    # --- JavaScript / TypeScript Patterns (Regex) ---
    
    # Imports 
    # CHANGED: Uses [^;]+? instead of [\s\S]+? to stop matching at the first semicolon.
    # This prevents catastrophic backtracking on side-effect imports (import 'foo';)
    # where the engine would otherwise scan the entire file looking for 'from'.
    _JS_IMPORT_FROM = re.compile(r'import\s+(?:type\s+)?([^;]+?)\s+from\s+[\'"]([^\'"]+)[\'"]')
    _JS_EXPORT_FROM = re.compile(r'export\s+(?:type\s+)?([^;]+?)\s+from\s+[\'"]([^\'"]+)[\'"]')
    
    # Strictly matches `import 'side-effect'` without snagging structured imports
    _JS_IMPORT_SIDE_EFFECT = re.compile(r'import\s+[\'"]([^\'"]+)[\'"]')
    
    _JS_REQUIRE = re.compile(r'require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)')
    _JS_DYNAMIC_IMPORT = re.compile(r'import\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)')

    # Symbols (Classes & Functions)
    _JS_CLASS_DEF = re.compile(r'(?:export\s+)?(?:default\s+)?(?:abstract\s+)?class\s+([a-zA-Z0-9_$]+)')
    # FIXED: Allows `function* name`, `function * name`, or standard `function name`
    _JS_FUNC_DEF = re.compile(r'(?:export\s+)?(?:default\s+)?(?:async\s+)?function(?:\s+|\s*\*\s*)([a-zA-Z0-9_$]+)')
    _JS_CONST_FUNC_DEF = re.compile(r'(?:export\s+)?const\s+([a-zA-Z0-9_$]+)\s*=\s*(?:async\s+)?(?:\([^)]*\)|[a-zA-Z0-9_$]+)\s*=>')

    # Comment Stripping
    _JS_BLOCK_COMMENT = re.compile(r'/\*[\s\S]*?\*/')
    _JS_LINE_COMMENT = re.compile(r'//.*')

    @staticmethod
    def scan(path: str, language: str) -> Dict[str, List[str]]:
        """
        Scans a file for import statements and defined symbols based on language.
        Returns a dictionary with 'imports' and 'symbols' lists.
        """
        result = {"imports": [], "symbols": []}
        
        if language not in ("python", "javascript", "typescript"):
            return result

        try:
            with open(path, 'r', encoding='utf-8-sig', errors='ignore') as f:
                # Limit read to 250KB to prevent OOM on massive bundles
                content = f.read(250_000)
        except OSError:
            return result

        imports: Set[str] = set()
        symbols: Set[str] = set()

        try:
            if language == "python":
                ImportScanner._scan_python(content, imports, symbols)
            elif language in ("javascript", "typescript"):
                ImportScanner._scan_js(content, imports, symbols)
        except Exception:
            # Fail gracefully for syntax errors
            pass

        result["imports"] = sorted(list(imports))
        result["symbols"] = sorted(list(symbols))
        return result

    @staticmethod
    def _scan_python(content: str, imports: Set[str], symbols: Set[str]):
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return

        for node in ast.walk(tree):
            # Imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            
            elif isinstance(node, ast.ImportFrom):
                module_name = node.module or ""
                if node.level > 0:
                    prefix = "." * node.level
                    if not module_name:
                        for alias in node.names:
                            imports.add(prefix + alias.name)
                        continue
                    module_name = prefix + module_name
                
                if module_name:
                    imports.add(module_name)
                    
            # Symbols
            elif isinstance(node, ast.ClassDef):
                symbols.add(node.name)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                symbols.add(node.name)

    @staticmethod
    def _scan_js(content: str, imports: Set[str], symbols: Set[str]):
        # Strip comments first to avoid matching code inside them
        clean_content = ImportScanner._JS_BLOCK_COMMENT.sub('', content)
        clean_content = ImportScanner._JS_LINE_COMMENT.sub('', clean_content)

        # Imports
        # Group 1 is the capture group for the 'from' path in the new regex
        # Note: In the previous regex it was group 2, but we removed (?:type\s+)? from capture?
        # Wait, the regex is:
        # r'import\s+(?:type\s+)?([^;]+?)\s+from\s+[\'"]([^\'"]+)[\'"]'
        # Group 1: ([^;]+?) -> The symbols
        # Group 2: ([^\'"]+) -> The path
        for match in ImportScanner._JS_IMPORT_FROM.finditer(clean_content):
            imports.add(match.group(2)) 
            
        for match in ImportScanner._JS_IMPORT_SIDE_EFFECT.finditer(clean_content):
            imports.add(match.group(1))

        for match in ImportScanner._JS_REQUIRE.finditer(clean_content):
            imports.add(match.group(1))

        for match in ImportScanner._JS_EXPORT_FROM.finditer(clean_content):
            imports.add(match.group(2))

        for match in ImportScanner._JS_DYNAMIC_IMPORT.finditer(clean_content):
            imports.add(match.group(1))
            
        # Symbols
        for match in ImportScanner._JS_CLASS_DEF.finditer(clean_content):
            symbols.add(match.group(1))
            
        for match in ImportScanner._JS_FUNC_DEF.finditer(clean_content):
            symbols.add(match.group(1))
            
        for match in ImportScanner._JS_CONST_FUNC_DEF.finditer(clean_content):
            symbols.add(match.group(1))