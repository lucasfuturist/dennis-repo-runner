
## Context Telemetry
- **Focus:** `symbol:ContextSlicer`
- **Radius:** 1
- **Usage:** 1314 tokens
- **Cycles Included:** 0


# Context Slice: symbol:ContextSlicer

- repo_root: `C:\projects\repo-runner\src`
- snapshot_id: `2026-02-22T19-30-36Z`
- file_count: `1`
- tree_only: `False`
## Tree

```
└── analysis
    └── context_slicer.py
```

## File Contents

### `analysis/context_slicer.py`

```
from typing import Dict, Any, Union, Set, List, Optional
from collections import defaultdict
import logging
from src.observability.token_telemetry import TokenTelemetry

# Configure a module-level logger
logger = logging.getLogger(__name__)

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
            focus_id: The stable_id of the file (or a `symbol:{name}`) to center the slice on
            radius: Distance in hops to include
            max_tokens: Soft limit on context size. If exceeded, expansion stops.
                        The focus file is always included even if it exceeds the limit.
        """
        # 1. Normalize inputs
        graph_dict = graph.model_dump() if hasattr(graph, 'model_dump') else graph
        manifest_dict = manifest.model_dump() if hasattr(manifest, 'model_dump') else manifest

        files_map = {f["stable_id"]: f for f in manifest_dict.get("files", [])}
        
        # 1.5 Semantic Resolution: Resolve symbol to file
        resolved_focus_id = focus_id
        if focus_id.startswith("symbol:"):
            symbol_name = focus_id.split(":", 1)[1]
            found_file = None
            for file_entry in manifest_dict.get("files", []):
                if symbol_name in file_entry.get("symbols", []):
                    found_file = file_entry["stable_id"]
                    break
            
            if found_file:
                logger.info(f"Resolved {focus_id} to {found_file}")
                resolved_focus_id = found_file
            else:
                logger.warning(f"Symbol not found in manifest: {focus_id}")
                # If symbol isn't found, we can't slice. Return empty.
                sliced_manifest = manifest_dict.copy()
                sliced_manifest["files"] = []
                sliced_manifest["stats"] = sliced_manifest.get("stats", {}).copy()
                sliced_manifest["stats"]["file_count"] = 0
                sliced_manifest["stats"]["estimated_tokens"] = 0
                sliced_manifest["stats"]["cycles_included"] = 0
                return sliced_manifest
        
        # Ensure focus file exists in manifest, otherwise we can't slice
        if resolved_focus_id not in files_map:
            pass

        # 2. Build Adjacency List (Bidirectional)
        adj = defaultdict(list)
        for edge in graph_dict.get("edges", []):
            src = edge["source"]
            tgt = edge["target"]
            adj[src].append(tgt)
            adj[tgt].append(src)

        # 3. BFS with Token Budgeting
        visited: Set[str] = set()
        queue = [(resolved_focus_id, 0)]
        current_tokens = 0

        while queue:
            node_id, dist = queue.pop(0)
            
            if node_id in visited:
                continue

            # Calculate cost
            file_entry = files_map.get(node_id)
            if not file_entry:
                # Node might be external or missing; skip token counting for it
                visited.add(node_id)
                if dist < radius:
                    for neighbor in adj[node_id]:
                        if neighbor not in visited:
                            queue.append((neighbor, dist + 1))
                continue

            node_cost = TokenTelemetry.estimate_tokens(file_entry.get("size_bytes", 0))

            # Budget Check
            # Always include the resolved_focus_id regardless of size
            if max_tokens is not None:
                if current_tokens + node_cost > max_tokens and node_id != resolved_focus_id:
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
        included_ids = set(f["stable_id"] for f in filtered_files)
        cycles_in_slice = 0
        
        all_cycles = graph_dict.get("cycles", [])
        for cycle in all_cycles:
            if any(node_id in included_ids for node_id in cycle):
                cycles_in_slice += 1

        # 6. Construct Pruned Manifest
        sliced_manifest = manifest_dict.copy()
        sliced_manifest["files"] = filtered_files
        
        sliced_manifest["stats"] = sliced_manifest.get("stats", {}).copy()
        sliced_manifest["stats"]["file_count"] = len(filtered_files)
        sliced_manifest["stats"]["estimated_tokens"] = current_tokens
        sliced_manifest["stats"]["cycles_included"] = cycles_in_slice
        
        sliced_manifest["telemetry"] = {
            "focus_id": focus_id, # Original requested focus
            "resolved_id": resolved_focus_id, # What we actually centered on
            "radius": radius,
            "max_tokens": max_tokens,
            "budget_used_pct": (current_tokens / max_tokens * 100) if max_tokens else 0
        }

        return sliced_manifest
```

---
## Context Stats
- **Total Characters:** 6,290
- **Estimated Tokens:** ~1,572 (assuming ~4 chars/token)
- **Model Fit:** GPT-4 (8k)
