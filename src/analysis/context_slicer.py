from typing import Dict, Any, Union, Set
from collections import defaultdict

class ContextSlicer:
    """
    Deterministically prunes repository manifests based on graph topology.
    Used to compress LLM context windows by isolating a target file and its
    N-degree upstream/downstream dependencies.
    """
    
    @staticmethod
    def slice_manifest(
        manifest: Union[Dict, Any], 
        graph: Union[Dict, Any], 
        focus_id: str, 
        radius: int = 1
    ) -> Dict[str, Any]:
        """
        Filters a manifest to only include files within `radius` edges of `focus_id`.
        Returns a raw dictionary compatible with legacy exporters.
        """
        # 1. Normalize inputs to dicts to support both Pydantic and raw JSON
        graph_dict = graph.model_dump() if hasattr(graph, 'model_dump') else graph
        manifest_dict = manifest.model_dump() if hasattr(manifest, 'model_dump') else manifest

        # 2. Build Adjacency List (Bidirectional)
        # We want bidirectional context. If A imports B, both A and B need to be in context
        # to understand the full interface usage and implementation.
        adj = defaultdict(list)
        for edge in graph_dict.get("edges", []):
            src = edge["source"]
            tgt = edge["target"]
            adj[src].append(tgt)
            adj[tgt].append(src)

        # 3. Breadth-First Search (BFS) for N-Degree Radius
        visited: Set[str] = {focus_id}
        queue = [(focus_id, 0)]

        while queue:
            current, dist = queue.pop(0)
            if dist < radius:
                for neighbor in adj[current]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append((neighbor, dist + 1))

        # 4. Filter the Manifest Files
        original_files = manifest_dict.get("files", [])
        filtered_files = [
            f for f in original_files 
            if f.get("stable_id") in visited
        ]

        # 5. Construct Pruned Manifest
        sliced_manifest = manifest_dict.copy()
        sliced_manifest["files"] = filtered_files
        
        # Update stats to reflect the new, smaller size
        sliced_manifest["stats"] = sliced_manifest.get("stats", {}).copy()
        sliced_manifest["stats"]["file_count"] = len(filtered_files)
        
        return sliced_manifest