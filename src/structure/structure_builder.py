from typing import List, Dict, Any
from src.core.types import FileEntry

class StructureBuilder:
    def build(self, repo_id: str, files: List[FileEntry]) -> Dict[str, Any]:
        """
        Organizes files into a hierarchical structure.
        Accepts Pydantic Models for FileEntry.
        """
        
        # Root Structure
        structure = {
            "schema_version": "1.0",
            "repo": {
                "stable_id": repo_id,
                "root": ".",
                "modules": []
            }
        }
        
        modules_map = {}
        
        for f in files:
            # Attribute access
            mod_path = f.module_path
            
            if mod_path not in modules_map:
                modules_map[mod_path] = {
                    "stable_id": f"module:{mod_path}",
                    "path": mod_path,
                    "files": []
                }
            
            modules_map[mod_path]["files"].append(f.stable_id)
            
        # Convert map to sorted list
        sorted_keys = sorted(modules_map.keys())
        for k in sorted_keys:
            structure["repo"]["modules"].append(modules_map[k])
            
        return structure