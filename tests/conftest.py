import pytest
import os
import shutil
import tempfile
from pathlib import Path
from typing import Generator, List, Dict

@pytest.fixture
def temp_repo_root() -> Generator[str, None, None]:
    """
    Creates a temporary directory to act as a repository root.
    Cleans up after the test completes.
    """
    # Create a unique temp directory
    tmp_dir = tempfile.mkdtemp(prefix="repo_runner_test_")
    
    # Normalize path immediately to avoid Windows/Linux mismatches in tests
    tmp_path = os.path.normpath(tmp_dir).replace("\\", "/")
    
    yield tmp_path
    
    # Teardown
    if os.path.exists(tmp_dir):
        try:
            shutil.rmtree(tmp_dir)
        except PermissionError:
            # Common on Windows if a file handle is still open
            pass

@pytest.fixture
def create_file(temp_repo_root):
    """
    Factory fixture to create files within the temp repo.
    Usage: create_file("src/main.py", "print('hello')")
    """
    def _create(rel_path: str, content: str = ""):
        full_path = os.path.join(temp_repo_root, rel_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        return full_path
    return _create

@pytest.fixture
def simple_repo(temp_repo_root, create_file):
    """
    Populates the temp repo with a minimal Python structure.
    """
    create_file("src/main.py", "import os\nprint('hello')")
    create_file("src/utils.py", "def add(a, b): return a + b")
    create_file("README.md", "# Test Repo")
    return temp_repo_root

@pytest.fixture
def complex_repo(temp_repo_root, create_file):
    """
    Populates the temp repo with a mixed-language, nested structure
    including ignored directories.
    """
    # Python
    create_file("src/backend/api.py", "from . import utils")
    create_file("src/backend/utils.py", "SECRET = 'xyz'")
    
    # Typescript/React
    create_file("src/frontend/App.tsx", "import React from 'react';\nimport { Button } from './components/Button';")
    create_file("src/frontend/components/Button.tsx", "export const Button = () => <button />")
    
    # Ignored folders
    create_file("node_modules/react/index.js", "module.exports = {}")
    create_file(".git/config", "[core]\nrepositoryformatversion = 0")
    create_file("dist/bundle.js", "var a = 1;")
    
    # Configs
    create_file("package.json", "{}")
    create_file("requirements.txt", "flask")
    
    return temp_repo_root