from collections import defaultdict
from typing import Dict, List


class StructureBuilder:
    def build(self, repo_id: str, files: List[Dict]) -> Dict:
        modules = defaultdict(list)

        for file_entry in files:
            module_path = file_entry["module_path"]
            modules[module_path].append(file_entry["stable_id"])

        sorted_modules = sorted(modules.keys())

        module_entries = []
        for module in sorted_modules:
            module_entries.append({
                "stable_id": f"module:{module}",
                "path": module,
                "files": sorted(modules[module])
            })

        return {
            "schema_version": "1.0",
            "repo": {
                "stable_id": repo_id,
                "root": ".",
                "modules": module_entries
            }
        }