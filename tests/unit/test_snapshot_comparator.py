import unittest
from src.analysis.snapshot_comparator import SnapshotComparator
from src.core.types import (
    Manifest, ManifestInputs, ManifestConfig, ManifestStats, GitMetadata, 
    FileEntry, GraphStructure, GraphNode, GraphEdge
)

class TestSnapshotComparator(unittest.TestCase):
    def setUp(self):
        # Base setup helpers to keep tests clean
        self.inputs = ManifestInputs(repo_root="C:/repo", roots=["C:/repo"], git=GitMetadata(is_repo=False))
        self.config = ManifestConfig(depth=5, ignore_names=[], include_extensions=[], include_readme=True, tree_only=False, skip_graph=False, manual_override=False)
        self.stats = ManifestStats(file_count=0, total_bytes=0)

    def _create_manifest(self, snap_id: str, files: list) -> Manifest:
        return Manifest(
            tool={"name": "test"},
            snapshot={"snapshot_id": snap_id},
            inputs=self.inputs,
            config=self.config,
            stats=self.stats,
            files=files
        )

    def test_file_diffing(self):
        """Test detection of added, removed, and modified files via SHA256."""
        # Snapshot A (Base)
        files_a = [
            FileEntry(stable_id="file:src/a.py", path="src/a.py", module_path="src", sha256="hash_a1", size_bytes=10),
            FileEntry(stable_id="file:src/b.py", path="src/b.py", module_path="src", sha256="hash_b1", size_bytes=10),
        ]
        manifest_a = self._create_manifest("v1", files_a)

        # Snapshot B (Target)
        # a.py is modified (hash changed)
        # b.py is removed
        # c.py is added
        files_b = [
            FileEntry(stable_id="file:src/a.py", path="src/a.py", module_path="src", sha256="hash_a2", size_bytes=10),
            FileEntry(stable_id="file:src/c.py", path="src/c.py", module_path="src", sha256="hash_c1", size_bytes=10),
        ]
        manifest_b = self._create_manifest("v2", files_b)

        report = SnapshotComparator.compare(manifest_a, manifest_b)

        self.assertEqual(report.files_added, 1)
        self.assertEqual(report.files_removed, 1)
        self.assertEqual(report.files_modified, 1)

        added = [f for f in report.file_diffs if f.status == "added"][0]
        self.assertEqual(added.stable_id, "file:src/c.py")

        removed = [f for f in report.file_diffs if f.status == "removed"][0]
        self.assertEqual(removed.stable_id, "file:src/b.py")

        modified = [f for f in report.file_diffs if f.status == "modified"][0]
        self.assertEqual(modified.stable_id, "file:src/a.py")
        self.assertEqual(modified.old_sha256, "hash_a1")
        self.assertEqual(modified.new_sha256, "hash_a2")

    def test_graph_diffing(self):
        """Test detection of added and removed dependency edges."""
        graph_a = GraphStructure(
            nodes=[], 
            edges=[
                GraphEdge(source="file:a.py", target="file:b.py", relation="imports"),
                GraphEdge(source="file:a.py", target="external:os", relation="imports")
            ]
        )

        # Removed 'os' import, added 'sys' import
        graph_b = GraphStructure(
            nodes=[], 
            edges=[
                GraphEdge(source="file:a.py", target="file:b.py", relation="imports"),
                GraphEdge(source="file:a.py", target="external:sys", relation="imports")
            ]
        )

        manifest_dummy = self._create_manifest("v1", [])
        
        report = SnapshotComparator.compare(manifest_dummy, manifest_dummy, graph_a, graph_b)

        self.assertEqual(report.edges_added, 1)
        self.assertEqual(report.edges_removed, 1)

        added_edge = [e for e in report.edge_diffs if e.status == "added"][0]
        self.assertEqual(added_edge.target, "external:sys")

        removed_edge = [e for e in report.edge_diffs if e.status == "removed"][0]
        self.assertEqual(removed_edge.target, "external:os")

if __name__ == "__main__":
    unittest.main()