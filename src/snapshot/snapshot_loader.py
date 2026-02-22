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