import os
from typing import List, Set, Optional, Callable


class FileSystemScanner:
    def __init__(self, depth: int, ignore_names: Set[str]):
        self.depth = depth
        self.ignore_names = ignore_names

    def scan(self, root_paths: List[str], progress_callback: Optional[Callable[[int], None]] = None) -> List[str]:
        all_files = []
        visited_realpaths = set()
        count = 0

        for root in root_paths:
            # Hardening: Resolve user provided paths to realpaths immediately.
            try:
                abs_root = os.path.realpath(root)
            except OSError:
                continue

            # Handle explicit file inputs
            if os.path.isfile(abs_root):
                all_files.append(abs_root)
                count += 1
                if progress_callback and count % 100 == 0:
                     if not progress_callback(count): return all_files
                continue

            # Handle directories
            if os.path.isdir(abs_root):
                # We start the recursive walk
                if not self._walk(abs_root, 0, all_files, visited_realpaths, progress_callback):
                    # If _walk returns False, it means scan was cancelled
                    return sorted(all_files)

        return sorted(all_files)

    def _walk(self, directory: str, current_depth: int, results: List[str], visited: Set[str], 
              progress_callback: Optional[Callable[[int], bool]]) -> bool:
        """
        Returns True if walk should continue, False if cancelled.
        """
        if self.depth >= 0 and current_depth > self.depth:
            return True

        # 1. Symlink Cycle Detection & Canonicalization
        try:
            real_path = os.path.realpath(directory)
            if real_path in visited:
                return True
            visited.add(real_path)
        except OSError:
            return True

        # 2. List Directory (Robust)
        try:
            entries = sorted(os.listdir(directory))
        except (PermissionError, OSError):
            return True

        for entry in entries:
            if entry in self.ignore_names:
                continue

            full_path = os.path.join(directory, entry)

            # 3. Classify and Recurse
            try:
                if os.path.isdir(full_path):
                    if not self._walk(full_path, current_depth + 1, results, visited, progress_callback):
                        return False
                elif os.path.isfile(full_path):
                    results.append(os.path.abspath(full_path))
                    
                    # Report Progress every 50 files to avoid UI spam
                    if progress_callback and len(results) % 50 == 0:
                        should_continue = progress_callback(len(results))
                        if not should_continue:
                            return False
            except (PermissionError, OSError):
                continue
                
        return True