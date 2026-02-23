
## Context Telemetry
- **Focus:** `symbol:GraphBuilder`
- **Radius:** 1
- **Usage:** 3040/4000 (76.0%)
- **Cycles Included:** 0


# Context Slice: symbol:GraphBuilder

- repo_root: `C:\projects\repo-runner`
- snapshot_id: `2026-02-23T22-44-29Z`
- file_count: `2`
- tree_only: `False`
## Tree

```
└── src
    ├── analysis
    │   └── graph_builder.py
    └── core
        └── types.py
```

## File Contents

### `src/analysis/graph_builder.py`

```
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
        Reference: ID_SPEC.md (External ID Normalization)
        """
        if language == "python":
            # Rule: Truncate at first dot
            if import_str.startswith("."): return None
            return import_str.split(".")[0]
            
        elif language in ("javascript", "typescript"):
            # Rules:
            # 1. Ignore relatives / absolutes
            if import_str.startswith(".") or import_str.startswith("/"): return None
            
            # 2. Scoped Packages (@scope/pkg/sub -> @scope/pkg)
            if import_str.startswith("@"):
                parts = import_str.split("/")
                if len(parts) >= 2: 
                    return f"{parts[0]}/{parts[1]}"
                return import_str 
            
            # 3. Standard Packages (pkg/sub -> pkg)
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
```

### `src/core/types.py`

```
from typing import List, Optional, Set, Any, Dict
from pydantic import BaseModel, Field, field_validator

class RepoRunnerConfig(BaseModel):
    """
    Schema for repo-runner.json configuration files.
    Defines system-wide defaults for snapshot runs.
    """
    output_root: Optional[str] = None
    depth: int = 25
    ignore: List[str] = [".git", "node_modules", "__pycache__", "dist", "build", ".next", ".expo", ".venv"]
    include_extensions: List[str] = Field(default_factory=list)
    include_readme: bool = True
    skip_graph: bool = False
    export_flatten: bool = False

class FileEntry(BaseModel):
    """
    Represents a single file in the snapshot.
    Enforces path normalization strategies at the model level.
    """
    path: str
    stable_id: str
    module_path: str
    sha256: str
    size_bytes: int
    language: str = "unknown"
    imports: List[str] = Field(default_factory=list)
    symbols: List[str] = Field(default_factory=list) 

    @field_validator('path', 'module_path')
    @classmethod
    def validate_path_normalization(cls, v: str) -> str:
        """
        Enforces that all paths stored in the system are:
        1. Forward-slash separated
        2. Lowercase (for case-insensitive consistency)
        """
        if not v:
            return v
        return v.replace('\\', '/').lower()

    @field_validator('stable_id')
    @classmethod
    def validate_stable_id(cls, v: str) -> str:
        if not v.startswith(('file:', 'module:', 'repo:', 'external:')):
             raise ValueError(f"Invalid stable_id format: {v}")
        return v.lower()


class GraphNode(BaseModel):
    id: str
    type: str  # 'file' | 'module' | 'external'
    
    # Optional metadata for specific node types
    metadata: Optional[Any] = None

class GraphEdge(BaseModel):
    source: str
    target: str
    relation: str = "imports"

class GraphStructure(BaseModel):
    schema_version: str = "1.0"
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    # List of cycles, where each cycle is a list of node IDs in traversal order
    cycles: List[List[str]] = Field(default_factory=list)
    # Formalized flag for O(1) downstream checks (e.g., DAG validation)
    has_cycles: bool = False

class ManifestStats(BaseModel):
    file_count: int
    total_bytes: int
    external_dependencies: List[str] = Field(default_factory=list)

class GitMetadata(BaseModel):
    is_repo: bool
    commit: Optional[str] = None

class ManifestInputs(BaseModel):
    repo_root: str
    roots: List[str]
    git: GitMetadata

class ManifestConfig(BaseModel):
    depth: int
    ignore_names: List[str]
    include_extensions: List[str]
    include_readme: bool
    tree_only: bool
    skip_graph: bool
    manual_override: bool

class Manifest(BaseModel):
    schema_version: str = "1.0"
    tool: dict
    snapshot: dict
    inputs: ManifestInputs
    config: ManifestConfig
    stats: ManifestStats
    files: List[FileEntry]

# --- Structural Diff Models ---

class FileDiff(BaseModel):
    stable_id: str
    status: str # 'added', 'removed', 'modified'
    old_sha256: Optional[str] = None
    new_sha256: Optional[str] = None

class EdgeDiff(BaseModel):
    source: str
    target: str
    relation: str
    status: str # 'added', 'removed'

class SnapshotDiffReport(BaseModel):
    base_snapshot_id: str
    target_snapshot_id: str
    files_added: int = 0
    files_removed: int = 0
    files_modified: int = 0
    edges_added: int = 0
    edges_removed: int = 0
    file_diffs: List[FileDiff] = Field(default_factory=list)
    edge_diffs: List[EdgeDiff] = Field(default_factory=list)
```

---
## Context Stats
- **Total Characters:** 12,180
- **Estimated Tokens:** ~3,045 (assuming ~4 chars/token)
- **Model Fit:** GPT-4 (8k)
