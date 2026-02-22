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
                    pkg_name = self._resolve_external(raw_import, lang)
                    if pkg_name:
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
        if language == "python":
            if import_str.startswith("."): return None
            return import_str.split(".")[0]
        elif language in ("javascript", "typescript"):
            if import_str.startswith(".") or import_str.startswith("/"): return None
            if import_str.startswith("@"):
                parts = import_str.split("/")
                if len(parts) >= 2: return f"{parts[0]}/{parts[1]}"
                return import_str 
            return import_str.split("/")[0]
        return None

    def _resolve_python(self, import_str: str, source_dir: str, path_map: Dict[str, str]) -> Optional[str]:
        base_path = import_str.replace(".", "/")
        candidates = []
        candidates.append(f"{base_path}.py")
        candidates.append(f"{base_path}/__init__.py")
        rel_base = os.path.join(source_dir, base_path).replace("\\", "/")
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