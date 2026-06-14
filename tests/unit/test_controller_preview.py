import os
import pytest
from src.core.controller import get_file_preview_data

def test_get_file_preview_data_valid(temp_repo_root, create_file):
    file_path = create_file("src/test_file.py", "import os\n\nCONST_VAL = 10\n")
    data = get_file_preview_data(file_path, repo_root=temp_repo_root)
    
    assert data["language"] == "python"
    assert "os" in data["imports"]
    assert "CONST_VAL" in data["symbols"]
    assert data["stable_id"] == "file:src/test_file.py"

def test_get_file_preview_data_missing():
    with pytest.raises(FileNotFoundError):
        get_file_preview_data("non_existent_file.py")