import os
from typing import List, Set


class FileSystemScanner:
    def __init__(self, depth: int, ignore_names: Set[str]):
        self.depth = depth
        self.ignore_names = ignore_names

    def scan(self, root_paths: List[str]) -> List[str]:
        all_files = []
        visited_realpaths = set()

        for root in root_paths:
            # Handle explicit file inputs
            if os.path.isfile(root):
                all_files.append(os.path.abspath(root))
                continue

            # Handle directories
            abs_root = os.path.abspath(root)
            if os.path.isdir(abs_root):
                self._walk(abs_root, 0, all_files, visited_realpaths)

        return sorted(all_files)

    def _walk(self, directory: str, current_depth: int, results: List[str], visited: Set[str]):
        if self.depth >= 0 and current_depth > self.depth:
            return

        # 1. Symlink Cycle Detection
        try:
            real_path = os.path.realpath(directory)
            if real_path in visited:
                return
            visited.add(real_path)
        except OSError:
            # If we cannot resolve the path (permission/locked), we skip it safely.
            return

        # 2. List Directory
        try:
            entries = sorted(os.listdir(directory))
        except OSError:
            # Permission denied, not a directory, or vanished
            return

        for entry in entries:
            if entry in self.ignore_names:
                continue

            full_path = os.path.join(directory, entry)

            # 3. Classify and Recurse
            try:
                if os.path.isdir(full_path):
                    self._walk(full_path, current_depth + 1, results, visited)
                elif os.path.isfile(full_path):
                    results.append(os.path.abspath(full_path))
            except OSError:
                # Handle race conditions where file disappears between listdir and isfile
                continue