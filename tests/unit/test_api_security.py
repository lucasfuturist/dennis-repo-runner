import os
import pytest
from fastapi import HTTPException
from src.api.server import verify_safe_path

def test_verify_safe_path_valid():
    path = "src/api"
    resolved = verify_safe_path(path)
    assert "src" in resolved.replace("\\", "/")

def test_verify_safe_path_empty():
    with pytest.raises(HTTPException) as exc_info:
        verify_safe_path("")
    assert exc_info.value.status_code == 400

def test_verify_safe_path_system_root():
    root = os.path.abspath(os.sep)
    with pytest.raises(HTTPException) as exc_info:
        verify_safe_path(root)
    assert exc_info.value.status_code == 403

def test_verify_safe_path_sensitive_folders():
    with pytest.raises(HTTPException) as exc_info:
        verify_safe_path("C:/Windows/System32")
    assert exc_info.value.status_code == 403

    with pytest.raises(HTTPException) as exc_info:
        verify_safe_path("/etc/passwd")
    assert exc_info.value.status_code == 403