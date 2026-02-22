import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from src.core.controller import run_snapshot
from src.snapshot.snapshot_loader import SnapshotLoader
from src.analysis.context_slicer import ContextSlicer
from src.analysis.snapshot_comparator import SnapshotComparator
from src.observability.token_telemetry import TokenTelemetry
from src.core.types import Manifest, GraphStructure, SnapshotDiffReport

app = FastAPI(
    title="Repo-Runner AI Context API",
    description="Deterministic ingestion and context slicing engine for LLMs.",
    version="0.2.1"
)

# --- NEW: Root Redirect ---
@app.get("/", include_in_schema=False)
def root():
    """Redirects the root URL to the interactive API documentation."""
    return RedirectResponse(url="/docs")

# --- Request Models ---

class SnapshotRequest(BaseModel):
    repo_root: str
    output_root: str
    depth: int = 25
    ignore: List[str] = [".git", "node_modules", "__pycache__", "dist", "build"]
    include_extensions: List[str] = []
    include_readme: bool = True
    skip_graph: bool = False

class SliceRequest(BaseModel):
    output_root: str
    focus_id: str
    radius: int = 1
    max_tokens: Optional[int] = None  # NEW FIELD

class CompareRequest(BaseModel):
    output_root: str
    base_id: str
    target_id: str

# --- Routes ---

@app.post("/snapshots", summary="Trigger a new repository snapshot")
def create_snapshot(req: SnapshotRequest):
    """
    Scans the target repository, normalizes paths, fingerprints files, 
    and builds an AST-derived dependency graph.
    """
    try:
        snap_id = run_snapshot(
            repo_root=req.repo_root,
            output_root=req.output_root,
            depth=req.depth,
            ignore=req.ignore,
            include_extensions=req.include_extensions,
            include_readme=req.include_readme,
            write_current_pointer=True,
            skip_graph=req.skip_graph
        )
        return {"snapshot_id": snap_id, "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/snapshots/{snapshot_id}/slice", summary="Generate a tailored LLM context slice")
def slice_snapshot(snapshot_id: str, req: SliceRequest):
    """
    Performs a Bidirectional BFS on the dependency graph to isolate a target file 
    and its N-degree dependencies. Returns the compressed manifest and token telemetry.
    """
    loader = SnapshotLoader(req.output_root)
    try:
        snap_dir = loader.resolve_snapshot_dir(snapshot_id)
        manifest_dict = loader.load_manifest(snap_dir)
        
        graph_path = os.path.join(snap_dir, "graph.json")
        if not os.path.exists(graph_path):
            raise FileNotFoundError(f"graph.json missing in {snap_dir}")
            
        with open(graph_path, "r") as f:
            graph_data = json.load(f)
            
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Slice with new max_tokens parameter
    sliced_manifest = ContextSlicer.slice_manifest(
        manifest=manifest_dict, 
        graph=graph_data, 
        focus_id=req.focus_id, 
        radius=req.radius,
        max_tokens=req.max_tokens
    )
    
    # Generate human-readable telemetry
    # We use the sliced manifest's internal stats for telemetry generation
    estimated = sliced_manifest.get("stats", {}).get("estimated_tokens", 0)
    usage_str = TokenTelemetry.format_usage(estimated, req.max_tokens or 0)
    
    telemetry_md = f"""
## Context Telemetry
- **Focus:** `{req.focus_id}`
- **Radius:** {req.radius}
- **Usage:** {usage_str}
- **Cycles Included:** {sliced_manifest.get("stats", {}).get("cycles_included", 0)}
"""
    
    return {
        "focus_id": req.focus_id,
        "radius": req.radius,
        "telemetry_markdown": telemetry_md,
        "sliced_manifest": sliced_manifest
    }


@app.post("/snapshots/compare", response_model=SnapshotDiffReport, summary="Diff two structural snapshots")
def compare_snapshots(req: CompareRequest):
    """
    Deterministically diffs two snapshots. Identifies added/removed/modified files 
    via SHA256 hashes, and calculates the exact dependency edges that drifted.
    """
    loader = SnapshotLoader(req.output_root)
    try:
        dir_a = loader.resolve_snapshot_dir(req.base_id)
        dir_b = loader.resolve_snapshot_dir(req.target_id)
        
        manifest_a = Manifest.model_validate(loader.load_manifest(dir_a))
        manifest_b = Manifest.model_validate(loader.load_manifest(dir_b))
        
        ga_path = os.path.join(dir_a, "graph.json")
        gb_path = os.path.join(dir_b, "graph.json")
        
        g_a, g_b = None, None
        if os.path.exists(ga_path):
            with open(ga_path, "r") as f: g_a = GraphStructure.model_validate(json.load(f))
        if os.path.exists(gb_path):
            with open(gb_path, "r") as f: g_b = GraphStructure.model_validate(json.load(f))

        report = SnapshotComparator.compare(manifest_a, manifest_b, g_a, g_b)
        return report

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))