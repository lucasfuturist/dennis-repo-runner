import os
import sys
from unittest.mock import patch, MagicMock
import pytest
from src.cli.main import main

def test_cli_batch_compress_invocation(temp_repo_root, create_file):
    """
    Validates end-to-end integration mapping from CLI arguments
    to the run_batch_module_compression_stateless core service.
    """
    temp_repo_root = os.path.realpath(temp_repo_root)

    # 1. Setup mock directories & target codebase files
    create_file("src/analysis/a.py", "class A:\n    pass")
    create_file("repo-runner.json", '{"include_extensions": [".py"]}')

    export_dir = os.path.join(temp_repo_root, "exports")

    # Command parameters simulating typical terminal invocation
    cli_args = [
        "repo-runner", "export", "batch-compress",
        "--repo-root", temp_repo_root,
        "--modules", "src/analysis",
        "--output-dir", export_dir,
        "--delay", "0.0"
    ]

    with patch("sys.argv", cli_args), \
         patch("src.core.controller.run_batch_module_compression_stateless") as mock_run:
        
        mock_run.return_value = {"src/analysis": os.path.join(export_dir, "src-analysis-compressed.md")}

        # Run command line interface controller
        main()

        # 2. Assert core service was mapped and parameters were passed accurately
        mock_run.assert_called_once()
        call_kwargs = mock_run.call_args[1]

        assert call_kwargs["repo_root"] == temp_repo_root
        assert call_kwargs["export_dir"] == export_dir
        assert "src/analysis" in call_kwargs["selected_modules"]
        assert call_kwargs["delay"] == 0.0