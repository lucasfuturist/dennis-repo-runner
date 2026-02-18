import os


class PathNormalizer:
    def __init__(self, repo_root: str):
        self.repo_root = os.path.abspath(repo_root)

    def normalize(self, absolute_path: str) -> str:
        relative = os.path.relpath(absolute_path, self.repo_root)

        # Normalize separators first.
        normalized = relative.replace("\\", "/")

        # Only strip a literal "./" prefix (do NOT strip leading dots from names like ".context-docs").
        if normalized.startswith("./"):
            normalized = normalized[2:]

        # Normalize any accidental leading slashes (defensive; relpath shouldn't produce these).
        while normalized.startswith("/"):
            normalized = normalized[1:]

        return normalized.lower()

    def module_path(self, file_path: str) -> str:
        directory = os.path.dirname(file_path)
        return directory.replace("\\", "/")

    @staticmethod
    def file_id(normalized_path: str) -> str:
        return f"file:{normalized_path}"

    @staticmethod
    def module_id(module_path: str) -> str:
        return f"module:{module_path}"

    @staticmethod
    def repo_id() -> str:
        return "repo:root"