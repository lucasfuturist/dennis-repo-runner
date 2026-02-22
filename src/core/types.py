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