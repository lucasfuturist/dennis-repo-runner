from typing import List, Optional, Set, Any
from pydantic import BaseModel, Field, field_validator

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
        if not v.startswith(('file:', 'module:', 'repo:')):
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

# --- Structural Diff Models (NEW) ---

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