import unittest
from unittest.mock import patch, MagicMock
from src.cli.main import _parse_args, main
import sys

class TestCLISlice(unittest.TestCase):
    
    @patch('src.cli.main.run_export_flatten')
    def test_slice_command_invocation(self, mock_export):
        """
        Verify that `repo-runner slice` parses args correctly and calls the controller.
        """
        # Mock sys.argv
        test_args = [
            "slice",
            "--output-root", "./out",
            "--repo-root", "./repo",
            "--focus", "file:src/app.py",
            "--radius", "2",
            "--max-tokens", "5000"
        ]
        
        with patch.object(sys, 'argv', ["repo-runner"] + test_args):
            # Run main, which calls _parse_args internally
            main()
            
            # Assert controller was called with correct types
            mock_export.assert_called_once()
            _, kwargs = mock_export.call_args
            
            self.assertEqual(kwargs["focus_id"], "file:src/app.py")
            self.assertEqual(kwargs["radius"], 2)
            self.assertEqual(kwargs["max_tokens"], 5000)
            self.assertEqual(kwargs["repo_root"], "./repo")

    @patch('src.cli.main.run_export_flatten')
    def test_slice_defaults(self, mock_export):
        """
        Verify default values for radius and max_tokens.
        """
        test_args = [
            "slice",
            "--output-root", "./out",
            "--repo-root", "./repo",
            "--focus", "file:main.py"
        ]
        
        with patch.object(sys, 'argv', ["repo-runner"] + test_args):
            main()
            
            _, kwargs = mock_export.call_args
            self.assertEqual(kwargs["radius"], 1) # Default
            self.assertIsNone(kwargs["max_tokens"]) # Default None

if __name__ == "__main__":
    unittest.main()