import os
from typing import List, Dict, Set, Optional
from src.core.types import FileEntry, GraphStructure, GraphNode, GraphEdge

class GraphBuilder:
    def build(self, files: List[FileEntry]) -> GraphStructure:
        """
        Constructs a dependency graph from a list of FileEntries.
        Accepts Pydantic Models.
        """
        
        # 1. Build Lookup Maps
        # Uses attribute access f.path and f.stable_id
        path_map: Dict[str, str] = {f.path.lower(): f.stable_id for f in files}
        
        nodes: List[GraphNode] = []
        edges: List[GraphEdge] = []
        external_ids: Set[str] = set()
        
        # Add all file nodes
        for f in files:
            nodes.append(GraphNode(id=f.stable_id, type="file"))

        # 2. Iterate and Resolve Imports
        for f in files:
            source_id = f.stable_id
            source_path = f.path
            source_dir = os.path.dirname(source_path)
            lang = f.language

            for raw_import in f.imports:
                target_id = self._resolve_import(raw_import, source_dir, lang, path_map)
                
                if target_id:
                    edges.append(GraphEdge(
                        source=source_id,
                        target=target_id,
                        relation="imports"
                    ))
                else:
                    # Fallback to External Resolution
                    pkg_name = self._resolve_external(raw_import, lang)
                    if pkg_name:
                        # Enforce stable ID format: external:package_name (lowercase)
                        ext_id = f"external:{pkg_name}"
                        
                        if ext_id not in external_ids:
                            external_ids.add(ext_id)
                            nodes.append(GraphNode(id=ext_id, type="external"))
                        
                        edges.append(GraphEdge(
                            source=source_id,
                            target=ext_id,
                            relation="imports"
                        ))

        # 3. Enforce Determinism 
        # Sort nodes and edges before graph analysis to ensure stable cycle detection
        nodes.sort(key=lambda n: n.id)
        edges.sort(key=lambda e: (e.source, e.target, e.relation))

        # 4. Cycle Detection
        adjacency = self._build_adjacency(nodes, edges)
        cycles = self._detect_cycles(adjacency, nodes)
        has_cycles = len(cycles) > 0

        return GraphStructure(
            nodes=nodes, 
            edges=edges, 
            cycles=cycles, 
            has_cycles=has_cycles
        )

    def _build_adjacency(self, nodes: List[GraphNode], edges: List[GraphEdge]) -> Dict[str, List[str]]:
        adj: Dict[str, List[str]] = {n.id: [] for n in nodes}
        for edge in edges:
            if edge.source in adj:
                adj[edge.source].append(edge.target)
        
        # Sort neighbors for deterministic traversal
        for node_id in adj:
            adj[node_id].sort()
            
        return adj

    def _detect_cycles(self, adj: Dict[str, List[str]], nodes: List[GraphNode]) -> List[List[str]]:
        """
        Detects elementary cycles using DFS.
        Returns a list of cycles, where each cycle is a list of node IDs.
        """
        visited: Set[str] = set()
        visiting: Set[str] = set()
        stack: List[str] = []
        cycles: List[List[str]] = []

        def dfs(node_id: str):
            visited.add(node_id)
            visiting.add(node_id)
            stack.append(node_id)

            if node_id in adj:
                for neighbor in adj[node_id]:
                    if neighbor in visiting:
                        # Cycle found!
                        # Extract the cycle portion from the current stack
                        try:
                            start_index = stack.index(neighbor)
                            cycle_path = stack[start_index:]
                            cycles.append(cycle_path)
                        except ValueError:
                            pass # Should not happen given logic
                    elif neighbor not in visited:
                        dfs(neighbor)
            
            stack.pop()
            visiting.remove(node_id)

        # Iterate through nodes in deterministic order (already sorted in build)
        for node in nodes:
            if node.id not in visited:
                dfs(node.id)

        # Post-process cycles for deterministic output
        # 1. Normalize rotation (smallest element first)
        # 2. Sort the list of cycles
        normalized_cycles = []
        for cycle in cycles:
            # Rotate cycle so the smallest string is first
            min_idx = cycle.index(min(cycle))
            rotated = cycle[min_idx:] + cycle[:min_idx]
            normalized_cycles.append(rotated)
        
        # Remove duplicates (possible if reachable from multiple paths)
        unique_cycles = []
        seen_cycles = set()
        for c in normalized_cycles:
            c_tuple = tuple(c)
            if c_tuple not in seen_cycles:
                seen_cycles.add(c_tuple)
                unique_cycles.append(c)

        # Sort lexicographically
        unique_cycles.sort()

        return unique_cycles

    def _resolve_import(
        self, 
        import_str: str, 
        source_dir: str, 
        language: str, 
        path_map: Dict[str, str]
    ) -> Optional[str]:
        if language == "python":
            return self._resolve_python(import_str, source_dir, path_map)
        elif language in ("javascript", "typescript"):
            return self._resolve_js(import_str, source_dir, path_map)
        return None

    def _resolve_external(self, import_str: str, language: str) -> Optional[str]:
        """
        Strictly normalizes external dependencies to their root package name.
        Enforces LOWERCASE to prevent ID duplication (e.g. React vs react).
        Reference: ID_SPEC.md (External ID Normalization)
        """
        if language == "python":
            # Rule: Truncate at first dot
            if import_str.startswith("."): return None
            pkg = import_str.split(".")[0]
            return pkg.lower()
            
        elif language in ("javascript", "typescript"):
            # Rules:
            # 1. Ignore relatives / absolutes
            if import_str.startswith(".") or import_str.startswith("/"): return None
            
            # 2. Scoped Packages (@scope/pkg/sub -> @scope/pkg)
            if import_str.startswith("@"):
                parts = import_str.split("/")
                if len(parts) >= 2: 
                    # join then lower
                    return f"{parts[0]}/{parts[1]}".lower()
                return import_str.lower()
            
            # 3. Standard Packages (pkg/sub -> pkg)
            pkg = import_str.split("/")[0]
            return pkg.lower()
            
        return None

    def _resolve_python(self, import_str: str, source_dir: str, path_map: Dict[str, str]) -> Optional[str]:
        # FIXED: Handle relative imports logic carefully
        
        if import_str.startswith("."):
            # It's a relative import (e.g. .utils or ..core)
            # We must NOT replace the leading dots with slashes blindly, 
            # as that creates paths like "/utils" which os.path.join treats as absolute root.
            
            # 1. Strip leading dots to get the name
            name_part = import_str.lstrip(".")
            dot_count = len(import_str) - len(name_part)
            
            # 2. Walk up directory tree based on dot count
            # . -> current dir (dot_count 1)
            # .. -> parent (dot_count 2)
            
            # Start at source_dir
            current_base = source_dir
            
            # Go up (dot_count - 1) times
            # E.g. .utils -> 0 times up (stay in source_dir)
            # ..utils -> 1 time up (parent)
            for _ in range(dot_count - 1):
                current_base = os.path.dirname(current_base)
            
            base_path = name_part.replace(".", "/")
            rel_base = os.path.join(current_base, base_path).replace("\\", "/")
            
        else:
            # Absolute import (e.g. src.utils)
            base_path = import_str.replace(".", "/")
            # Here we treat absolute imports as relative to repo root (handled by path_map lookup)
            rel_base = base_path
        
        candidates = []
        candidates.append(f"{rel_base}.py")
        candidates.append(f"{rel_base}/__init__.py")
        
        for c in candidates:
            c_lower = c.lower()
            if c_lower in path_map:
                return path_map[c_lower]
        return None

    def _resolve_js(self, import_str: str, source_dir: str, path_map: Dict[str, str]) -> Optional[str]:
        try:
            joined = os.path.join(source_dir, import_str)
            normalized = os.path.normpath(joined).replace("\\", "/")
        except ValueError:
            return None

        extensions = ["", ".ts", ".tsx", ".js", ".jsx", ".d.ts", ".json"]
        for ext in extensions:
            candidate = f"{normalized}{ext}"
            if candidate.lower() in path_map:
                return path_map[candidate.lower()]
                
        index_extensions = [".ts", ".tsx", ".js", ".jsx"]
        for ext in index_extensions:
            candidate = f"{normalized}/index{ext}"
            if candidate.lower() in path_map:
                return path_map[candidate.lower()]
        return None