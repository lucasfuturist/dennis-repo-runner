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
        sha = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha.update(chunk)

        size = os.path.getsize(path)
        ext = os.path.splitext(path)[1].lower()
        language = FileFingerprint.LANGUAGE_MAP.get(ext, "unknown")

        return {
            "sha256": sha.hexdigest(),
            "size_bytes": size,
            "language": language,
        }