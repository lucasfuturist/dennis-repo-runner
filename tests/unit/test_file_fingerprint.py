import unittest
import tempfile
import shutil
import os
import hashlib
from src.fingerprint.file_fingerprint import FileFingerprint

class TestFingerprintHardening(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_valid_file(self):
        path = os.path.join(self.test_dir, "test.txt")
        content = b"hello world"
        with open(path, "wb") as f:
            f.write(content)
            
        fp = FileFingerprint.fingerprint(path)
        
        expected_sha = hashlib.sha256(content).hexdigest()
        self.assertEqual(fp["sha256"], expected_sha)
        self.assertEqual(fp["size_bytes"], len(content))
        self.assertEqual(fp["language"], "unknown") # .txt is unknown in current map

    def test_empty_file(self):
        path = os.path.join(self.test_dir, "empty.py")
        with open(path, "wb") as f:
            pass
            
        fp = FileFingerprint.fingerprint(path)
        self.assertEqual(fp["size_bytes"], 0)
        self.assertEqual(fp["language"], "python")

    def test_locked_or_missing_file(self):
        # Test missing file raises OSError
        path = os.path.join(self.test_dir, "ghost.txt")
        
        with self.assertRaises(OSError):
            FileFingerprint.fingerprint(path)

if __name__ == "__main__":
    unittest.main()