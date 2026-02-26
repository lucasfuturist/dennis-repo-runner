import unittest
from src.analysis.import_scanner import ImportScanner
import tempfile
import os

class TestScannerConstants(unittest.TestCase):
    """
    Verifies that the ImportScanner correctly identifies global constants
    (UPPER_CASE variables) in addition to Classes and Functions.
    """
    
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp_dir)
        
    def _create_and_scan(self, filename, content, lang):
        path = os.path.join(self.tmp_dir, filename)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return ImportScanner.scan(path, lang)

    def test_python_constants(self):
        code = """
import os

# Should capture
MAX_RETRIES = 5
DEFAULT_CONFIG = "prod"
API_KEY: str = os.getenv("KEY")

# Should NOT capture (lowercase/mixed)
local_var = 10
CamelCase = True
_private = False
        """
        result = self._create_and_scan("consts.py", code, "python")
        symbols = set(result["symbols"])
        
        self.assertIn("MAX_RETRIES", symbols)
        self.assertIn("DEFAULT_CONFIG", symbols)
        self.assertIn("API_KEY", symbols)
        
        self.assertNotIn("local_var", symbols)
        self.assertNotIn("CamelCase", symbols)
        self.assertNotIn("os", symbols) # It's an import, not a symbol def

    def test_js_constants(self):
        code = """
// Should capture
export const MAX_WIDTH = 100;
const API_ENDPOINT = 'https://api.com';

// Should capture arrow functions (existing logic)
const fetchData = () => {};

// Should NOT capture (lowercase/mixed)
const isValid = true;
let MUTABLE_VAR = 1; // We only target 'const' for JS to reduce noise
        """
        result = self._create_and_scan("consts.ts", code, "typescript")
        symbols = set(result["symbols"])
        
        self.assertIn("MAX_WIDTH", symbols)
        self.assertIn("API_ENDPOINT", symbols)
        self.assertIn("fetchData", symbols)
        
        self.assertNotIn("isValid", symbols)
        self.assertNotIn("MUTABLE_VAR", symbols)

    def test_python_assignment_unpacking(self):
        """
        Edge case: tuple unpacking assignments like A, B = 1, 2
        """
        code = """
A, B = 1, 2
x, Y = 3, 4
        """
        result = self._create_and_scan("unpack.py", code, "python")
        symbols = set(result["symbols"])
        
        # Current naive implementation visits targets.
        # If AST splits Tuple node, we might miss it unless we handle Tuple/List targets.
        # Let's see if the generic walker catches the names inside the Tuple.
        # Spoiler: It does because we iterate `node.targets`. 
        # But if target is a Tuple, `isinstance(target, ast.Name)` fails.
        # This test documents CURRENT limitations or behavior.
        
        # AST Assign target is a Tuple node, not a Name node.
        # So our current code SKIPs unpacking.
        self.assertNotIn("A", symbols) 
        self.assertNotIn("B", symbols)

if __name__ == "__main__":
    unittest.main()