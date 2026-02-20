import os
from typing import List, Dict, Set, Optional
from src.core.types import FileEntry, GraphStructure, GraphNode, GraphEdge

class GraphBuilder:
    def build(self, files: List[FileEntry]) -> GraphStructure:
        """
        Constructs a dependency graph from a list of FileEntries.
        Resolves raw import strings to stable_ids where possible.
        """
        
        # 1. Build Lookup Maps
        # path -> stable_id (e.g., "src/utils/logger.py" -> "file:src/utils/logger.py")
        # Ensure keys are lowercased for case-insensitive lookup, matching normalizer behavior.
        path_map: Dict[str, str] = {f["path"].lower(): f["stable_id"] for f in files}
        
        nodes: List[GraphNode] = []
        edges: List[GraphEdge] = []
        external_ids: Set[str] = set()
        
        # Add all file nodes
        for f in files:
            nodes.append({
                "id": f["stable_id"],
                "type": "file"
            })

        # 2. Iterate and Resolve Imports
        for f in files:
            source_id = f["stable_id"]
            source_path = f["path"]
            source_dir = os.path.dirname(source_path)
            lang = f["language"]

            for raw_import in f["imports"]:
                # Try internal resolution first
                target_id = self._resolve_import(raw_import, source_dir, lang, path_map)
                
                if target_id:
                    edges.append({
                        "source": source_id,
                        "target": target_id,
                        "relation": "imports"
                    })
                else:
                    # Try external resolution
                    pkg_name = self._resolve_external(raw_import, lang)
                    if pkg_name:
                        ext_id = f"external:{pkg_name}"
                        
                        # Add external node if new
                        if ext_id not in external_ids:
                            external_ids.add(ext_id)
                            nodes.append({
                                "id": ext_id,
                                "type": "external"
                            })
                        
                        # Add edge
                        edges.append({
                            "source": source_id,
                            "target": ext_id,
                            "relation": "imports"
                        })

        # 3. Enforce Determinism 
        # Lists must be explicitly sorted. The JSON writer only sorts dictionary keys.
        nodes.sort(key=lambda n: n["id"])
        edges.sort(key=lambda e: (e["source"], e["target"], e["relation"]))

        return {
            "schema_version": "1.0",
            "nodes": nodes,
            "edges": edges
        }

    def _resolve_import(
        self, 
        import_str: str, 
        source_dir: str, 
        language: str, 
        path_map: Dict[str, str]
    ) -> Optional[str]:
        """
        Heuristic resolution logic for internal files.
        """
        if language == "python":
            return self._resolve_python(import_str, source_dir, path_map)
        elif language in ("javascript", "typescript"):
            return self._resolve_js(import_str, source_dir, path_map)
        return None

    def _resolve_external(self, import_str: str, language: str) -> Optional[str]:
        """
        Determines if an import string represents an external package and returns
        the canonical package name.
        """
        if language == "python":
            # Python Logic
            # 1. Ignore relative imports (starting with .)
            if import_str.startswith("."):
                return None
            
            # 2. Extract top-level package
            # e.g., "pandas.core.frame" -> "pandas"
            # e.g., "os" -> "os"
            return import_str.split(".")[0]

        elif language in ("javascript", "typescript"):
            # JS/TS Logic
            # 1. Ignore relative paths
            if import_str.startswith(".") or import_str.startswith("/"):
                return None
            
            # 2. Handle scoped packages (@org/pkg/sub -> @org/pkg)
            if import_str.startswith("@"):
                parts = import_str.split("/")
                if len(parts) >= 2:
                    return f"{parts[0]}/{parts[1]}"
                return import_str # Fallback (weird case)
            
            # 3. Handle standard packages (lodash/fp -> lodash)
            return import_str.split("/")[0]

        return None

    def _resolve_python(
        self, 
        import_str: str, 
        source_dir: str, 
        path_map: Dict[str, str]
    ) -> Optional[str]:
        # Convert dots to slashes: "utils.logger" -> "utils/logger"
        base_path = import_str.replace(".", "/")
        
        # Candidates to check
        candidates = []

        # 1. Repo-relative match (absolute import from root)
        # e.g. "utils/logger" -> "utils/logger.py"
        candidates.append(f"{base_path}.py")
        candidates.append(f"{base_path}/__init__.py")

        # 2. Source-relative match (sibling or sub-package import)
        # e.g. source="src", import="utils.logger" -> "src/utils/logger.py"
        # We use os.path.join but must force forward slashes
        rel_base = os.path.join(source_dir, base_path).replace("\\", "/")
        candidates.append(f"{rel_base}.py")
        candidates.append(f"{rel_base}/__init__.py")

        for c in candidates:
            c_lower = c.lower()
            if c_lower in path_map:
                return path_map[c_lower]

        return None

    def _resolve_js(
        self, 
        import_str: str, 
        source_dir: str, 
        path_map: Dict[str, str]
    ) -> Optional[str]:
        
        # 1. External packages (lodash, react) -> Skip internal check if not relative
        # Note: We check relative logic in _resolve_external, but for internal resolution
        # we strictly only look at relative paths or paths that might be aliased.
        # For v0.1/0.2, we assume internal imports start with "." to be safe, 
        # or we might catch absolute imports if they match a file exactly.
        
        # 2. Relative resolution
        try:
            joined = os.path.join(source_dir, import_str)
            normalized = os.path.normpath(joined).replace("\\", "/")
        except ValueError:
            return None

        # 3. Extensions probing
        extensions = ["", ".ts", ".tsx", ".js", ".jsx", ".d.ts", ".json"]
        
        for ext in extensions:
            candidate = f"{normalized}{ext}"
            candidate_lower = candidate.lower()
            if candidate_lower in path_map:
                return path_map[candidate_lower]
                
        # 4. Index probing
        index_extensions = [".ts", ".tsx", ".js", ".jsx"]
        for ext in index_extensions:
            candidate = f"{normalized}/index{ext}"
            candidate_lower = candidate.lower()
            if candidate_lower in path_map:
                return path_map[candidate_lower]
                
        return None