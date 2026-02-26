import unittest
from unittest.mock import MagicMock, patch
import os
import pytest
from src.core.controller import run_snapshot

class TestCollisionLogic(unittest.TestCase):
    """
    Verifies that the system strictly enforces ID uniqueness, 
    preventing data loss on case-sensitive filesystems where 
    'File.txt' and 'file.txt' might coexist.
    """
    
    @patch("src.core.controller.FileSystemScanner")
    @patch("src.core.controller.ConfigLoader")
    def test_detects_case_collision(self, mock_config_loader, mock_scanner_cls):
        # 1. Setup Mocks
        # Mock Config not strictly needed if we pass explicit args, but safer
        mock_config = MagicMock()
        mock_config_loader.load_config.return_value = mock_config
        
        # Mock Scanner to return colliding paths
        # In a real scenario, these would come from os.walk on Linux
        mock_instance = mock_scanner_cls.return_value
        mock_instance.scan.return_value = [
            "/repo/src/Utils.py", 
            "/repo/src/utils.py"
        ]
        
        # 2. Execution & Assertion
        # We expect a ValueError because both Normalize to 'file:src/utils.py'
        # We need to mock os.path.exists and isdir to bypass checks on fake paths
        with patch("os.path.exists", return_value=True), \
             patch("os.path.isdir", return_value=True), \
             patch("os.path.abspath", side_effect=lambda x: x): # pass through
             
            with self.assertRaises(ValueError) as context:
                run_snapshot(
                    repo_root="/repo",
                    output_root="/tmp/out",
                    depth=5,
                    ignore=[],
                    include_extensions=[],
                    include_readme=False,
                    write_current_pointer=False
                )
            
        # 3. Verify Error Message
        msg = str(context.exception)
        self.assertIn("ID Collision Detected", msg)
        self.assertIn("src/Utils.py", msg)
        self.assertIn("src/utils.py", msg)

    @patch("src.core.controller.FileSystemScanner")
    @patch("src.core.controller.ConfigLoader")
    def test_no_collision_on_distinct_files(self, mock_config_loader, mock_scanner_cls):
        mock_instance = mock_scanner_cls.return_value
        mock_instance.scan.return_value = [
            "/repo/src/a.py", 
            "/repo/src/b.py"
        ]
        
        # Should NOT raise
        try:
            with patch("os.path.exists", return_value=True), \
                 patch("os.path.isdir", return_value=True), \
                 patch("os.path.abspath", side_effect=lambda x: x), \
                 patch("src.core.controller.FileFingerprint.fingerprint") as mock_fp, \
                 patch("src.core.controller.SnapshotWriter"):
                
                # Return dummy fingerprint
                mock_fp.return_value = {
                    "sha256": "000", 
                    "size_bytes": 10, 
                    "language": "python"
                }
                
                run_snapshot(
                    repo_root="/repo",
                    output_root="/tmp/out",
                    depth=5,
                    ignore=[],
                    include_extensions=[],
                    include_readme=False,
                    write_current_pointer=False
                )
        except ValueError:
            self.fail("run_snapshot raised ValueError unexpectedly on distinct files")

if __name__ == "__main__":
    unittest.main()