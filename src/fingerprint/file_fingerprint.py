import hashlib
import os
from typing import Dict


class FileFingerprint:
    LANGUAGE_MAP = {
        ".ts": "typescript",
        ".tsx": "typescript",
        ".js": "javascript",
        ".jsx": "javascript",
        ".py": "python",
        ".rs": "rust",
        ".go": "go",
        ".java": "java",
        ".html": "html",
        ".css": "css",
        ".sql": "sql",
        ".toml": "toml",
        ".ps1": "powershell",
        ".md": "markdown",
        ".json": "json",
    }

    @staticmethod
    def fingerprint(path: str) -> Dict:
        """
        Computes the fingerprint of a file.
        Raises OSError if the file cannot be opened or read (e.g. locked, permissions).
        """
        sha = hashlib.sha256()
        
        # We allow OSError to propagate so the caller (Controller) can decide 
        # whether to skip the file or fail the run.
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha.update(chunk)

        try:
            size = os.path.getsize(path)
        except OSError:
            # Fallback if getsize fails but read succeeded (rare race condition)
            size = 0 

        ext = os.path.splitext(path)[1].lower()
        language = FileFingerprint.LANGUAGE_MAP.get(ext, "unknown")

        return {
            "sha256": sha.hexdigest(),
            "size_bytes": size,
            "language": language,
        }