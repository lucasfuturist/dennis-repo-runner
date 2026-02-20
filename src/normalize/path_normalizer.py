import os


class PathNormalizer:
    def __init__(self, repo_root: str):
        self.repo_root = os.path.abspath(repo_root)

    def normalize(self, absolute_path: str) -> str:
        """
        Converts an absolute path to a repo-relative, lowercased, forward-slash normalized string.
        Raises ValueError if the path escapes the repo root.
        """
        # 1. Compute relative path
        try:
            relative = os.path.relpath(absolute_path, self.repo_root)
        except ValueError:
            # On Windows, relpath fails if drives differ (C: vs D:)
            raise ValueError(f"Path {absolute_path} is on a different drive than repo root {self.repo_root}")

        # 2. Normalize separators immediately to handle cross-OS logic safely
        normalized = relative.replace("\\", "/")

        # 3. Security: Check for Root Escape
        # We check for ".." segments at the start.
        if normalized.startswith("../") or normalized == "..":
            raise ValueError(f"Path escapes repository root: {normalized} (from {absolute_path})")

        # 4. Strip purely decorative prefixes
        if normalized.startswith("./"):
            normalized = normalized[2:]

        # 5. Defensive: Strip leading slashes (shouldn't happen with relpath but be safe)
        while normalized.startswith("/"):
            normalized = normalized[1:]

        # 6. Enforce Lowercase (v0.2 Spec)
        return normalized.lower()

    def module_path(self, normalized_file_path: str) -> str:
        """
        Derives the module (directory) path from a normalized file path.
        Returns '.' if the file is at the repo root.
        """
        directory = os.path.dirname(normalized_file_path)
        
        # Standardize empty directory (root) to "."
        if not directory or directory == "":
            return "."
            
        return directory.replace("\\", "/")

    @staticmethod
    def file_id(normalized_path: str) -> str:
        return f"file:{normalized_path}"

    @staticmethod
    def module_id(module_path: str) -> str:
        # If the module is root, we map it to repo:root logically, 
        # but if we need a distinct ID for the directory node:
        if module_path == ".":
            return "module:." 
        return f"module:{module_path}"

    @staticmethod
    def repo_id() -> str:
        return "repo:root"