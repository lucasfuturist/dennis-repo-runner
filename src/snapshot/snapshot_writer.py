import os
import json
import datetime
from typing import Optional, Dict, Union, List

from src.core.types import Manifest, GraphStructure

class SnapshotWriter:
    def __init__(self, output_root: str):
        self.output_root = output_root

    def write(
        self,
        manifest: Manifest,
        structure: Dict,
        graph: Optional[GraphStructure],
        symbols: Optional[Dict[str, List[str]]] = None,
        write_current_pointer: bool = True
    ) -> str:
        """
        Writes the snapshot to disk.
        Handles Pydantic serialization for manifest and graph.
        """
        
        # Generate ID (Timezone Aware to fix DeprecationWarning)
        timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
        snapshot_id = timestamp
        
        snapshot_dir = os.path.join(self.output_root, snapshot_id)
        os.makedirs(snapshot_dir, exist_ok=True)
        
        # Update Manifest with Snapshot Info
        manifest.snapshot = {
            "snapshot_id": snapshot_id,
            "created_utc": timestamp,
            "output_root": self.output_root.replace("\\", "/")
        }

        # Write Manifest (Pydantic Dump)
        with open(os.path.join(snapshot_dir, "manifest.json"), "w") as f:
            f.write(manifest.model_dump_json(indent=2))
            
        # Write Structure (Dict Dump)
        with open(os.path.join(snapshot_dir, "structure.json"), "w") as f:
            json.dump(structure, f, indent=2)
            
        # Write Graph (Pydantic Dump)
        if graph:
            with open(os.path.join(snapshot_dir, "graph.json"), "w") as f:
                f.write(graph.model_dump_json(indent=2))
                
        # Write Symbols Index
        if symbols is not None:
            with open(os.path.join(snapshot_dir, "symbols.json"), "w") as f:
                json.dump(symbols, f, indent=2)
                
        # Write Exports folder
        os.makedirs(os.path.join(snapshot_dir, "exports"), exist_ok=True)
        
        # Update Pointer
        if write_current_pointer:
            current_ptr = {
                "schema_version": "1.0",
                "current_snapshot_id": snapshot_id,
                "path": snapshot_id
            }
            with open(os.path.join(self.output_root, "current.json"), "w") as f:
                json.dump(current_ptr, f, indent=2)
                
        return snapshot_id