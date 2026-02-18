import os
from typing import List, Set


class FileSystemScanner:
    def __init__(self, depth: int, ignore_names: Set[str]):
        self.depth = depth
        self.ignore_names = ignore_names

    def scan(self, root_paths: List[str]) -> List[str]:
        all_files = []

        for root in root_paths:
            if os.path.isfile(root):
                all_files.append(os.path.abspath(root))
                continue

            root = os.path.abspath(root)
            all_files.extend(self._walk(root, current_depth=0))

        return sorted(all_files)

    def _walk(self, directory: str, current_depth: int) -> List[str]:
        if self.depth >= 0 and current_depth > self.depth:
            return []

        results = []

        try:
            entries = sorted(os.listdir(directory))
        except OSError:
            return []

        for entry in entries:
            if entry in self.ignore_names:
                continue

            full_path = os.path.join(directory, entry)

            if os.path.isdir(full_path):
                results.extend(self._walk(full_path, current_depth + 1))
            elif os.path.isfile(full_path):
                results.append(os.path.abspath(full_path))

        return results