import unittest
from unittest.mock import patch, MagicMock
from src.cli.main import main
import sys

class TestCLIDiff(unittest.TestCase):
    
    @patch('src.cli.main.run_compare')
    @patch('src.cli.main.ConfigLoader.load_config')
    def test_diff_command_parsing(self, mock_config, mock_compare):
        """Verify the diff command sends correct IDs to the controller."""
        # Setup mock report
        mock_report = MagicMock()
        mock_report.base_snapshot_id = "base_snap"
        mock_report.target_snapshot_id = "target_snap"
        mock_report.file_diffs = []
        mock_report.edge_diffs = []
        mock_compare.return_value = mock_report
        
        # Setup mock config
        mock_config.return_value.output_root = "./out"

        test_args = [
            "diff",
            "--base", "2026-02-22T01",
            "--target", "current"
        ]
        
        with patch.object(sys, 'argv', ["repo-runner"] + test_args):
            main()
            
            mock_compare.assert_called_once_with("./out", "2026-02-22T01", "current")

if __name__ == "__main__":
    unittest.main()