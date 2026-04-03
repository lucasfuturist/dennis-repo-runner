# Module Export: snapshot

- repo_root: `C:/projects/repo-runner`
- snapshot_id: `BATCH_EXPORT`
- file_count: `2`
- tree_only: `False`
## Tree

```
└── src
    └── snapshot
        ├── snapshot_loader.py
        └── snapshot_writer.py
```

## File Contents

### `src/snapshot/snapshot_loader.py`

```
import json
import os
from typing import Optional


class SnapshotLoader:
    """
    Utility for resolving and loading snapshot artifacts from the output directory.
    Supports 'current' alias resolution via current.json.
    """
    def __init__(self, output_root: str):
        self.output_root = output_root

    def resolve_snapshot_dir(self, snapshot_id: Optional[str]) -> str:
        """
        Locates a specific snapshot directory. 
        If snapshot_id is None or "current", resolves via current.json.
        """
        # Treat "current" string as an alias for the latest pointer
        is_current_alias = snapshot_id is not None and snapshot_id.lower() == "current"

        if snapshot_id and not is_current_alias:
            snapshot_dir = os.path.join(self.output_root, snapshot_id)
            if not os.path.isdir(snapshot_dir):
                raise FileNotFoundError(f"Snapshot not found: {snapshot_dir}")
            return snapshot_dir

        # Resolve via current.json
        current_path = os.path.join(self.output_root, "current.json")
        if not os.path.isfile(current_path):
            raise FileNotFoundError(
                f"current.json not found at output root: {current_path}. "
                "Run `repo-runner snapshot ...` first or pass a specific --snapshot-id."
            )

        with open(current_path, "r", encoding="utf-8") as f:
            current = json.load(f)

        resolved_id = current.get("current_snapshot_id")
        if not resolved_id:
            raise ValueError("current.json missing required field: current_snapshot_id")

        snapshot_dir = os.path.join(self.output_root, resolved_id)
        if not os.path.isdir(snapshot_dir):
            raise FileNotFoundError(f"Snapshot dir referenced by current.json not found: {snapshot_dir}")

        return snapshot_dir

    @staticmethod
    def load_manifest(snapshot_dir: str) -> dict:
        path = os.path.join(snapshot_dir, "manifest.json")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def load_structure(snapshot_dir: str) -> dict:
        path = os.path.join(snapshot_dir, "structure.json")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
```

### `src/snapshot/snapshot_writer.py`

```
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
```

---
## Context Stats
- **Total Characters:** 5,083
- **Estimated Tokens:** ~1,270 (assuming ~4 chars/token)
- **Model Fit:** GPT-4 (8k)
