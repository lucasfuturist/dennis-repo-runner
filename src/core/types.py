from typing import TypedDict, List, Optional, Any, Dict

class FileEntry(TypedDict):
    stable_id: str
    path: str
    module_path: str
    sha256: str
    size_bytes: int
    language: str
    imports: List[str]

class SnapshotTool(TypedDict):
    name: str
    version: str

class SnapshotInputs(TypedDict):
    repo_root: str
    roots: List[str]
    git: Dict[str, Any]

class SnapshotConfig(TypedDict):
    depth: int
    ignore_names: List[str]
    include_extensions: List[str]
    include_readme: bool
    tree_only: bool
    manual_override: bool

class SnapshotStats(TypedDict):
    file_count: int
    total_bytes: int
    external_dependencies: List[str]  # New field

class Manifest(TypedDict):
    schema_version: str
    tool: SnapshotTool
    inputs: SnapshotInputs
    config: SnapshotConfig
    stats: SnapshotStats
    files: List[FileEntry]
    snapshot: Dict[str, Any]

# --- Graph Types ---

class GraphNode(TypedDict):
    id: str  # stable_id
    type: str  # file | module | external

class GraphEdge(TypedDict):
    source: str  # stable_id
    target: str  # stable_id
    relation: str  # imports | defines

class GraphStructure(TypedDict):
    schema_version: str
    nodes: List[GraphNode]
    edges: List[GraphEdge]