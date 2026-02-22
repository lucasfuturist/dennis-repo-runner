from typing import Dict, Tuple, Set, Optional
from src.core.types import Manifest, GraphStructure, SnapshotDiffReport, FileDiff, EdgeDiff

class SnapshotComparator:
    """
    Deterministic Diff Engine.
    Compares two repository snapshots to identify structural drift, 
    file modifications (via SHA256), and dependency edge changes.
    """

    @staticmethod
    def compare(
        manifest_a: Manifest, 
        manifest_b: Manifest, 
        graph_a: Optional[GraphStructure] = None, 
        graph_b: Optional[GraphStructure] = None
    ) -> SnapshotDiffReport:
        
        base_id = manifest_a.snapshot.get("snapshot_id", "unknown_base")
        target_id = manifest_b.snapshot.get("snapshot_id", "unknown_target")

        report = SnapshotDiffReport(
            base_snapshot_id=base_id,
            target_snapshot_id=target_id
        )

        # 1. Compare Files (Using stable_id and sha256)
        files_a: Dict[str, str] = {f.stable_id: f.sha256 for f in manifest_a.files}
        files_b: Dict[str, str] = {f.stable_id: f.sha256 for f in manifest_b.files}

        set_a = set(files_a.keys())
        set_b = set(files_b.keys())

        # Added Files
        for added_id in (set_b - set_a):
            report.file_diffs.append(FileDiff(
                stable_id=added_id, 
                status="added", 
                new_sha256=files_b[added_id]
            ))
            report.files_added += 1

        # Removed Files
        for removed_id in (set_a - set_b):
            report.file_diffs.append(FileDiff(
                stable_id=removed_id, 
                status="removed", 
                old_sha256=files_a[removed_id]
            ))
            report.files_removed += 1

        # Modified Files (Intersection with different hashes)
        for common_id in (set_a & set_b):
            if files_a[common_id] != files_b[common_id]:
                report.file_diffs.append(FileDiff(
                    stable_id=common_id, 
                    status="modified", 
                    old_sha256=files_a[common_id],
                    new_sha256=files_b[common_id]
                ))
                report.files_modified += 1

        # Sort file diffs deterministically
        report.file_diffs.sort(key=lambda x: (x.status, x.stable_id))

        # 2. Compare Graphs (If both exist)
        if graph_a and graph_b:
            # Create comparable tuples from edges: (source, target, relation)
            edges_a: Set[Tuple[str, str, str]] = {
                (e.source, e.target, e.relation) for e in graph_a.edges
            }
            edges_b: Set[Tuple[str, str, str]] = {
                (e.source, e.target, e.relation) for e in graph_b.edges
            }

            # Added Edges
            for edge in (edges_b - edges_a):
                report.edge_diffs.append(EdgeDiff(
                    source=edge[0], target=edge[1], relation=edge[2], status="added"
                ))
                report.edges_added += 1

            # Removed Edges
            for edge in (edges_a - edges_b):
                report.edge_diffs.append(EdgeDiff(
                    source=edge[0], target=edge[1], relation=edge[2], status="removed"
                ))
                report.edges_removed += 1

            # Sort edge diffs deterministically
            report.edge_diffs.sort(key=lambda x: (x.status, x.source, x.target))

        return report