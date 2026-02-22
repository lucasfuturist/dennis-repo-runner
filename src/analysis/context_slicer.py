from typing import Dict, Any, Union, Set, List, Optional
from collections import defaultdict
from src.observability.token_telemetry import TokenTelemetry

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
        radius: int = 1,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Filters a manifest to only include files within `radius` edges of `focus_id`.
        
        Args:
            manifest: The full repository manifest (dict or Pydantic model)
            graph: The dependency graph (dict or Pydantic model)
            focus_id: The stable_id of the file to center the slice on
            radius: Distance in hops to include
            max_tokens: Soft limit on context size. If exceeded, expansion stops.
                        The focus file is always included even if it exceeds the limit.
        """
        # 1. Normalize inputs
        graph_dict = graph.model_dump() if hasattr(graph, 'model_dump') else graph
        manifest_dict = manifest.model_dump() if hasattr(manifest, 'model_dump') else manifest

        files_map = {f["stable_id"]: f for f in manifest_dict.get("files", [])}
        
        # 2. Build Adjacency List (Bidirectional)
        adj = defaultdict(list)
        for edge in graph_dict.get("edges", []):
            src = edge["source"]
            tgt = edge["target"]
            adj[src].append(tgt)
            adj[tgt].append(src)

        # 3. BFS with Token Budgeting
        visited: Set[str] = set()
        queue = [(focus_id, 0)]
        current_tokens = 0
        
        # Ensure focus file exists in manifest, otherwise we can't slice
        if focus_id not in files_map:
            # Fallback: Return empty or minimal structure
            # For now, let's just proceed; the loop will handle empty lookups
            pass

        while queue:
            node_id, dist = queue.pop(0)
            
            if node_id in visited:
                continue

            # Calculate cost
            file_entry = files_map.get(node_id)
            if not file_entry:
                # Node might be external or missing; skip token counting for it
                # but allow traversal if it's in the graph? 
                # Policy: Only include 'files' in the token budget and output
                visited.add(node_id)
                # Still expand neighbors if within radius
                if dist < radius:
                    for neighbor in adj[node_id]:
                        if neighbor not in visited:
                            queue.append((neighbor, dist + 1))
                continue

            node_cost = TokenTelemetry.estimate_tokens(file_entry.get("size_bytes", 0))

            # Budget Check
            # Always include the focus_id regardless of size
            if max_tokens is not None:
                if current_tokens + node_cost > max_tokens and node_id != focus_id:
                    # Budget exhausted, stop this branch
                    continue

            # Commit to slice
            visited.add(node_id)
            current_tokens += node_cost

            # Expand
            if dist < radius:
                # Sort neighbors for deterministic queueing
                neighbors = sorted(adj[node_id])
                for neighbor in neighbors:
                    if neighbor not in visited:
                        queue.append((neighbor, dist + 1))

        # 4. Filter Files
        filtered_files = [
            f for f in manifest_dict.get("files", []) 
            if f["stable_id"] in visited
        ]

        # 5. Cycle Detection Stats
        # Check if any included files participate in known cycles
        included_ids = set(f["stable_id"] for f in filtered_files)
        cycles_in_slice = 0
        
        all_cycles = graph_dict.get("cycles", [])
        for cycle in all_cycles:
            # If any node in the cycle is included, we count the cycle
            if any(node_id in included_ids for node_id in cycle):
                cycles_in_slice += 1

        # 6. Construct Pruned Manifest
        sliced_manifest = manifest_dict.copy()
        sliced_manifest["files"] = filtered_files
        
        # Update stats
        sliced_manifest["stats"] = sliced_manifest.get("stats", {}).copy()
        sliced_manifest["stats"]["file_count"] = len(filtered_files)
        sliced_manifest["stats"]["estimated_tokens"] = current_tokens
        sliced_manifest["stats"]["cycles_included"] = cycles_in_slice
        
        # Add telemetry metadata
        sliced_manifest["telemetry"] = {
            "focus_id": focus_id,
            "radius": radius,
            "max_tokens": max_tokens,
            "budget_used_pct": (current_tokens / max_tokens * 100) if max_tokens else 0
        }

        return sliced_manifest