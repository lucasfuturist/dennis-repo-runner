import json
import os
from datetime import datetime, timezone
from typing import Dict, Optional

class SnapshotWriter:
    def __init__(self, output_root: str):
        self.output_root = output_root

    def write(
        self,
        manifest: Dict,
        structure: Dict,
        graph: Optional[Dict] = None,
        snapshot_id: Optional[str] = None,
        write_current_pointer: bool = True,
    ) -> str:
        os.makedirs(self.output_root, exist_ok=True)

        # Use timezone-aware UTC
        now_utc = datetime.now(timezone.utc)

        if snapshot_id is None:
            snapshot_id = now_utc.strftime("%Y-%m-%dT%H-%M-%SZ")

        snapshot_dir = os.path.join(self.output_root, snapshot_id)
        if os.path.exists(snapshot_dir):
            raise RuntimeError(f"Snapshot directory already exists: {snapshot_dir}")

        os.makedirs(snapshot_dir, exist_ok=False)
        os.makedirs(os.path.join(snapshot_dir, "exports"), exist_ok=True)

        manifest = dict(manifest)
        manifest.setdefault("snapshot", {})
        manifest["snapshot"] = dict(manifest["snapshot"])
        manifest["snapshot"].setdefault("snapshot_id", snapshot_id)
        # ISO 8601 format with Z
        manifest["snapshot"].setdefault("created_utc", now_utc.strftime("%Y-%m-%dT%H:%M:%SZ"))
        manifest["snapshot"].setdefault("output_root", self.output_root)

        # Write Manifest
        with open(os.path.join(snapshot_dir, "manifest.json"), "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, sort_keys=True)

        # Write Structure
        with open(os.path.join(snapshot_dir, "structure.json"), "w", encoding="utf-8") as f:
            json.dump(structure, f, indent=2, sort_keys=True)
            
        # Write Graph (if present)
        if graph:
            with open(os.path.join(snapshot_dir, "graph.json"), "w", encoding="utf-8") as f:
                json.dump(graph, f, indent=2, sort_keys=True)

        # Update Pointer
        if write_current_pointer:
            current_path = os.path.join(self.output_root, "current.json")
            with open(current_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "schema_version": "1.0",
                        "current_snapshot_id": snapshot_id,
                        "path": snapshot_id,
                    },
                    f,
                    indent=2,
                    sort_keys=True,
                )

        return snapshot_id