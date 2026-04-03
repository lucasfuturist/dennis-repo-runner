# Module Export: src

- repo_root: `C:/projects/repo-runner`
- snapshot_id: `BATCH_EXPORT`
- file_count: `34`
- tree_only: `False`
## Tree

```
└── src
    ├── __init__.py
    ├── analysis
    │   ├── __init__.py
    │   ├── context_slicer.py
    │   ├── graph_builder.py
    │   ├── import_scanner.py
    │   └── snapshot_comparator.py
    ├── api
    │   ├── init.py
    │   └── server.py
    ├── cli
    │   ├── __init__.py
    │   └── main.py
    ├── core
    │   ├── __init__.py
    │   ├── config_loader.py
    │   ├── controller.py
    │   ├── repo-runner.code-workspace
    │   └── types.py
    ├── entry_point.py
    ├── exporters
    │   ├── drawio_exporter.py
    │   ├── flatten_markdown_exporter.py
    │   └── mermaid_exporter.py
    ├── fingerprint
    │   └── file_fingerprint.py
    ├── gui
    │   ├── __init__.py
    │   ├── app.py
    │   └── components
    │       ├── config_tabs.py
    │       ├── export_preview.py
    │       ├── preview_pane.py
    │       ├── progress_window.py
    │       └── tree_view.py
    ├── normalize
    │   └── path_normalizer.py
    ├── observability
    │   ├── init.py
    │   └── token_telemetry.py
    ├── scanner
    │   └── filesystem_scanner.py
    ├── snapshot
    │   ├── snapshot_loader.py
    │   └── snapshot_writer.py
    └── structure
        └── structure_builder.py
```

## File Contents

### `src/__init__.py`

```

```

### `src/analysis/__init__.py`

```
# src/analysis/__init__.py
```

### `src/analysis/context_slicer.py`

```
from typing import Dict, Any, Union, Set, List, Optional
from collections import defaultdict
import logging
from src.observability.token_telemetry import TokenTelemetry

# Configure a module-level logger
logger = logging.getLogger(__name__)

class ContextSlicer:
    """
    Deterministically prunes repository manifests based on graph topology.
    Used to compress LLM context windows by isolating a target file and its
    N-degree upstream/downstream dependencies.
    """
    
    @staticmethod
    def slice_manifest(
        manifest: Union[Dict, Any], 
        graph: Union[Dict, Any], 
        focus_id: str, 
        radius: int = 1,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Filters a manifest to only include files within `radius` edges of `focus_id`.
        
        Args:
            manifest: The full repository manifest (dict or Pydantic model)
            graph: The dependency graph (dict or Pydantic model)
            focus_id: The stable_id of the file (or a `symbol:{name}`) to center the slice on
            radius: Distance in hops to include
            max_tokens: Soft limit on context size. If exceeded, expansion stops.
                        The focus file is always included even if it exceeds the limit.
        """
        # 1. Normalize inputs
        graph_dict = graph.model_dump() if hasattr(graph, 'model_dump') else graph
        manifest_dict = manifest.model_dump() if hasattr(manifest, 'model_dump') else manifest

        files_map = {f["stable_id"]: f for f in manifest_dict.get("files", [])}
        
        # 1.5 Semantic Resolution: Resolve symbol to file
        resolved_focus_id = focus_id
        if focus_id.startswith("symbol:"):
            symbol_name = focus_id.split(":", 1)[1]
            found_file = None
            for file_entry in manifest_dict.get("files", []):
                if symbol_name in file_entry.get("symbols", []):
                    found_file = file_entry["stable_id"]
                    break
            
            if found_file:
                logger.info(f"Resolved {focus_id} to {found_file}")
                resolved_focus_id = found_file
            else:
                logger.warning(f"Symbol not found in manifest: {focus_id}")
                # If symbol isn't found, we can't slice. Return empty.
                sliced_manifest = manifest_dict.copy()
                sliced_manifest["files"] = []
                sliced_manifest["stats"] = sliced_manifest.get("stats", {}).copy()
                sliced_manifest["stats"]["file_count"] = 0
                sliced_manifest["stats"]["estimated_tokens"] = 0
                sliced_manifest["stats"]["cycles_included"] = 0
                return sliced_manifest
        
        # Ensure focus file exists in manifest, otherwise we can't slice
        if resolved_focus_id not in files_map:
            logger.warning(f"Focus ID not found in manifest graph: {resolved_focus_id}")
            sliced_manifest = manifest_dict.copy()
            sliced_manifest["files"] = []
            sliced_manifest["stats"] = sliced_manifest.get("stats", {}).copy()
            sliced_manifest["stats"]["file_count"] = 0
            sliced_manifest["stats"]["estimated_tokens"] = 0
            sliced_manifest["stats"]["cycles_included"] = 0
            return sliced_manifest

        # 2. Build Adjacency List (Bidirectional)
        adj = defaultdict(list)
        for edge in graph_dict.get("edges", []):
            src = edge["source"]
            tgt = edge["target"]
            adj[src].append(tgt)
            adj[tgt].append(src)

        # 3. BFS with Token Budgeting
        visited: Set[str] = set()
        queue = [(resolved_focus_id, 0)]
        current_tokens = 0

        while queue:
            node_id, dist = queue.pop(0)
            
            if node_id in visited:
                continue

            # Calculate cost
            file_entry = files_map.get(node_id)
            if not file_entry:
                # Node might be external or missing; skip token counting for it
                visited.add(node_id)
                if dist < radius:
                    for neighbor in adj[node_id]:
                        if neighbor not in visited:
                            queue.append((neighbor, dist + 1))
                continue

            # NEW: Language-aware token estimation
            node_cost = TokenTelemetry.estimate_tokens(
                file_entry.get("size_bytes", 0), 
                file_entry.get("language", "unknown")
            )

            # Budget Check
            # Always include the resolved_focus_id regardless of size
            if max_tokens is not None:
                if current_tokens + node_cost > max_tokens and node_id != resolved_focus_id:
                    # Budget exhausted, stop this branch
                    continue

            # Commit to slice
            visited.add(node_id)
            current_tokens += node_cost

            # Expand
            if dist < radius:
                # Sort neighbors for deterministic queueing
                neighbors = sorted(adj[node_id])
                for neighbor in neighbors:
                    if neighbor not in visited:
                        queue.append((neighbor, dist + 1))

        # 4. Filter Files
        filtered_files = [
            f for f in manifest_dict.get("files", []) 
            if f["stable_id"] in visited
        ]

        # 5. Cycle Detection Stats
        included_ids = set(f["stable_id"] for f in filtered_files)
        cycles_in_slice = 0
        
        all_cycles = graph_dict.get("cycles", [])
        for cycle in all_cycles:
            if any(node_id in included_ids for node_id in cycle):
                cycles_in_slice += 1

        # 6. Construct Pruned Manifest
        sliced_manifest = manifest_dict.copy()
        sliced_manifest["files"] = filtered_files
        
        sliced_manifest["stats"] = sliced_manifest.get("stats", {}).copy()
        sliced_manifest["stats"]["file_count"] = len(filtered_files)
        sliced_manifest["stats"]["estimated_tokens"] = current_tokens
        sliced_manifest["stats"]["cycles_included"] = cycles_in_slice
        
        sliced_manifest["telemetry"] = {
            "focus_id": focus_id, # Original requested focus
            "resolved_id": resolved_focus_id, # What we actually centered on
            "radius": radius,
            "max_tokens": max_tokens,
            "budget_used_pct": (current_tokens / max_tokens * 100) if max_tokens else 0
        }

        return sliced_manifest
```

### `src/analysis/graph_builder.py`

```
import os
from typing import List, Dict, Set, Optional
from src.core.types import FileEntry, GraphStructure, GraphNode, GraphEdge, UnresolvedReference

class GraphBuilder:
    def build(self, files: List[FileEntry]) -> GraphStructure:
        """
        Constructs a dependency graph from a list of FileEntries.
        Accepts Pydantic Models.
        """
        
        # 1. Build Lookup Maps
        # Uses attribute access f.path and f.stable_id
        path_map: Dict[str, str] = {f.path.lower(): f.stable_id for f in files}
        
        nodes: List[GraphNode] = []
        edges: List[GraphEdge] = []
        unresolved: List[UnresolvedReference] = []
        external_ids: Set[str] = set()
        
        # Add all file nodes
        for f in files:
            nodes.append(GraphNode(id=f.stable_id, type="file"))

        # 2. Iterate and Resolve Imports
        for f in files:
            source_id = f.stable_id
            source_path = f.path
            source_dir = os.path.dirname(source_path)
            lang = f.language

            for raw_import in f.imports:
                target_id = self._resolve_import(raw_import, source_dir, lang, path_map)
                
                if target_id:
                    edges.append(GraphEdge(
                        source=source_id,
                        target=target_id,
                        relation="imports"
                    ))
                else:
                    # Fallback to External Resolution
                    pkg_name = self._resolve_external(raw_import, lang)
                    if pkg_name:
                        # Enforce stable ID format: external:package_name (lowercase)
                        ext_id = f"external:{pkg_name}"
                        
                        if ext_id not in external_ids:
                            external_ids.add(ext_id)
                            nodes.append(GraphNode(id=ext_id, type="external"))
                        
                        edges.append(GraphEdge(
                            source=source_id,
                            target=ext_id,
                            relation="imports"
                        ))
                    else:
                        # Resolution Failed: It's neither a file nor a valid external.
                        # Likely a broken relative import or file excluded by ignore rules.
                        unresolved.append(UnresolvedReference(
                            source=source_id,
                            import_ref=raw_import
                        ))

        # 3. Enforce Determinism 
        # Sort nodes and edges before graph analysis to ensure stable cycle detection
        nodes.sort(key=lambda n: n.id)
        edges.sort(key=lambda e: (e.source, e.target, e.relation))
        unresolved.sort(key=lambda u: (u.source, u.import_ref))

        # 4. Cycle Detection
        adjacency = self._build_adjacency(nodes, edges)
        cycles = self._detect_cycles(adjacency, nodes)
        has_cycles = len(cycles) > 0

        return GraphStructure(
            nodes=nodes, 
            edges=edges, 
            cycles=cycles, 
            has_cycles=has_cycles,
            unresolved_references=unresolved
        )

    def _build_adjacency(self, nodes: List[GraphNode], edges: List[GraphEdge]) -> Dict[str, List[str]]:
        adj: Dict[str, List[str]] = {n.id:[] for n in nodes}
        for edge in edges:
            if edge.source in adj:
                adj[edge.source].append(edge.target)
        
        # Sort neighbors for deterministic traversal
        for node_id in adj:
            adj[node_id].sort()
            
        return adj

    def _detect_cycles(self, adj: Dict[str, List[str]], nodes: List[GraphNode]) -> List[List[str]]:
        """
        Detects elementary cycles using DFS.
        Returns a list of cycles, where each cycle is a list of node IDs.
        """
        visited: Set[str] = set()
        visiting: Set[str] = set()
        stack: List[str] = []
        cycles: List[List[str]] =[]

        def dfs(node_id: str):
            visited.add(node_id)
            visiting.add(node_id)
            stack.append(node_id)

            if node_id in adj:
                for neighbor in adj[node_id]:
                    if neighbor in visiting:
                        # Cycle found!
                        # Extract the cycle portion from the current stack
                        try:
                            start_index = stack.index(neighbor)
                            cycle_path = stack[start_index:]
                            cycles.append(cycle_path)
                        except ValueError:
                            pass # Should not happen given logic
                    elif neighbor not in visited:
                        dfs(neighbor)
            
            stack.pop()
            visiting.remove(node_id)

        # Iterate through nodes in deterministic order (already sorted in build)
        for node in nodes:
            if node.id not in visited:
                dfs(node.id)

        # Post-process cycles for deterministic output
        # 1. Normalize rotation (smallest element first)
        # 2. Sort the list of cycles
        normalized_cycles =[]
        for cycle in cycles:
            # Rotate cycle so the smallest string is first
            min_idx = cycle.index(min(cycle))
            rotated = cycle[min_idx:] + cycle[:min_idx]
            normalized_cycles.append(rotated)
        
        # Remove duplicates (possible if reachable from multiple paths)
        unique_cycles =[]
        seen_cycles = set()
        for c in normalized_cycles:
            c_tuple = tuple(c)
            if c_tuple not in seen_cycles:
                seen_cycles.add(c_tuple)
                unique_cycles.append(c)

        # Sort lexicographically
        unique_cycles.sort()

        return unique_cycles

    def _resolve_import(
        self, 
        import_str: str, 
        source_dir: str, 
        language: str, 
        path_map: Dict[str, str]
    ) -> Optional[str]:
        if language == "python":
            return self._resolve_python(import_str, source_dir, path_map)
        elif language in ("javascript", "typescript"):
            return self._resolve_js(import_str, source_dir, path_map)
        return None

    def _resolve_external(self, import_str: str, language: str) -> Optional[str]:
        """
        Strictly normalizes external dependencies to their root package name.
        Enforces LOWERCASE to prevent ID duplication (e.g. React vs react).
        Reference: ID_SPEC.md (External ID Normalization)
        """
        if language == "python":
            # Rule: Truncate at first dot
            if import_str.startswith("."): return None
            pkg = import_str.split(".")[0]
            return pkg.lower()
            
        elif language in ("javascript", "typescript"):
            # Rules:
            # 1. Ignore relatives / absolutes
            if import_str.startswith(".") or import_str.startswith("/"): return None
            
            # 2. Scoped Packages (@scope/pkg/sub -> @scope/pkg)
            if import_str.startswith("@"):
                parts = import_str.split("/")
                if len(parts) >= 2: 
                    # join then lower
                    return f"{parts[0]}/{parts[1]}".lower()
                return import_str.lower()
            
            # 3. Standard Packages (pkg/sub -> pkg)
            pkg = import_str.split("/")[0]
            return pkg.lower()
            
        return None

    def _resolve_python(self, import_str: str, source_dir: str, path_map: Dict[str, str]) -> Optional[str]:
        candidates =[]
        
        if import_str.startswith("."):
            # Explicit Relative import (e.g. .utils or ..core)
            name_part = import_str.lstrip(".")
            dot_count = len(import_str) - len(name_part)
            
            current_base = source_dir
            for _ in range(dot_count - 1):
                current_base = os.path.dirname(current_base)
            
            base_path = name_part.replace(".", "/")
            rel_base = os.path.join(current_base, base_path).replace("\\", "/")
            candidates.append(f"{rel_base}.py")
            candidates.append(f"{rel_base}/__init__.py")
            
        else:
            # Absolute import (e.g. utils.logger)
            base_path = import_str.replace(".", "/")
            
            # 1. Check if it's relative to the repo root (standard absolute project import)
            candidates.append(f"{base_path}.py")
            candidates.append(f"{base_path}/__init__.py")
            
            # 2. FIX: Fallback to treating it as relative to source_dir 
            # (Python 2 style or certain local import scenarios like `import logger` inside `utils/`)
            # This restores the original behavior that test_python_internal_resolution expects.
            rel_base = os.path.join(source_dir, base_path).replace("\\", "/")
            candidates.append(f"{rel_base}.py")
            candidates.append(f"{rel_base}/__init__.py")
        
        for c in candidates:
            c_lower = c.lower()
            if c_lower in path_map:
                return path_map[c_lower]
        return None

    def _resolve_js(self, import_str: str, source_dir: str, path_map: Dict[str, str]) -> Optional[str]:
        try:
            joined = os.path.join(source_dir, import_str)
            normalized = os.path.normpath(joined).replace("\\", "/")
        except ValueError:
            return None

        extensions =["", ".ts", ".tsx", ".js", ".jsx", ".d.ts", ".json"]
        for ext in extensions:
            candidate = f"{normalized}{ext}"
            if candidate.lower() in path_map:
                return path_map[candidate.lower()]
                
        index_extensions = [".ts", ".tsx", ".js", ".jsx"]
        for ext in index_extensions:
            candidate = f"{normalized}/index{ext}"
            if candidate.lower() in path_map:
                return path_map[candidate.lower()]
        return None
```

### `src/analysis/import_scanner.py`

```
import re
import ast
from typing import List, Set, Dict

class ImportScanner:
    # --- JavaScript / TypeScript Patterns (Regex) ---
    
    # Imports 
    # Uses [^;]+? to stop matching at the first semicolon (prevent catastrophic backtracking)
    _JS_IMPORT_FROM = re.compile(r'import\s+(?:type\s+)?([^;]+?)\s+from\s+[\'"]([^\'"]+)[\'"]')
    _JS_EXPORT_FROM = re.compile(r'export\s+(?:type\s+)?([^;]+?)\s+from\s+[\'"]([^\'"]+)[\'"]')
    
    # Strictly matches `import 'side-effect'` without snagging structured imports
    _JS_IMPORT_SIDE_EFFECT = re.compile(r'import\s+[\'"]([^\'"]+)[\'"]')
    
    _JS_REQUIRE = re.compile(r'require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)')
    _JS_DYNAMIC_IMPORT = re.compile(r'import\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)')

    # Symbols (Classes & Functions)
    _JS_CLASS_DEF = re.compile(r'(?:export\s+)?(?:default\s+)?(?:abstract\s+)?class\s+([a-zA-Z0-9_$]+)')
    # Allows `function* name`, `function * name`, or standard `function name`
    _JS_FUNC_DEF = re.compile(r'(?:export\s+)?(?:default\s+)?(?:async\s+)?function(?:\s+|\s*\*\s*)([a-zA-Z0-9_$]+)')
    
    # Arrow Functions: const foo = () => ...
    _JS_CONST_FUNC_DEF = re.compile(r'(?:export\s+)?const\s+([a-zA-Z0-9_$]+)\s*=\s*(?:async\s+)?(?:\([^)]*\)|[a-zA-Z0-9_$]+)\s*=>')

    # Constants (New in v0.2.1): export const SCREAMING_SNAKE = ...
    # We enforce UPPER_CASE to avoid indexing every single local variable.
    _JS_CONST_VAR_DEF = re.compile(r'(?:export\s+)?const\s+([A-Z0-9_]{2,})\s*=')

    # Comment Stripping
    _JS_BLOCK_COMMENT = re.compile(r'/\*[\s\S]*?\*/')
    _JS_LINE_COMMENT = re.compile(r'//.*')

    @staticmethod
    def scan(path: str, language: str) -> Dict[str, List[str]]:
        """
        Scans a file for import statements and defined symbols based on language.
        Returns a dictionary with 'imports' and 'symbols' lists.
        """
        result = {"imports": [], "symbols": []}
        
        if language not in ("python", "javascript", "typescript"):
            return result

        try:
            with open(path, 'r', encoding='utf-8-sig', errors='ignore') as f:
                # Limit read to 250KB to prevent OOM on massive bundles
                content = f.read(250_000)
        except OSError:
            return result

        imports: Set[str] = set()
        symbols: Set[str] = set()

        try:
            if language == "python":
                ImportScanner._scan_python(content, imports, symbols)
            elif language in ("javascript", "typescript"):
                ImportScanner._scan_js(content, imports, symbols)
        except Exception:
            # Fail gracefully for syntax errors
            pass

        result["imports"] = sorted(list(imports))
        result["symbols"] = sorted(list(symbols))
        return result

    @staticmethod
    def _scan_python(content: str, imports: Set[str], symbols: Set[str]):
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return

        for node in ast.walk(tree):
            # Imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            
            elif isinstance(node, ast.ImportFrom):
                module_name = node.module or ""
                if node.level > 0:
                    prefix = "." * node.level
                    if not module_name:
                        for alias in node.names:
                            imports.add(prefix + alias.name)
                        continue
                    module_name = prefix + module_name
                
                if module_name:
                    imports.add(module_name)
                    
            # Symbols
            elif isinstance(node, ast.ClassDef):
                symbols.add(node.name)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                symbols.add(node.name)
            
            # Global Constants (Assignments)
            # We look for UPPER_CASE variables at the top level (approx)
            # ast.walk visits all nodes, so we check if the assignment target is a Name
            elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                targets = []
                if isinstance(node, ast.Assign):
                    targets = node.targets
                else:
                    targets = [node.target]
                
                for target in targets:
                    if isinstance(target, ast.Name):
                        name = target.id
                        # Heuristic: Only capture UPPER_CASE constants (min 2 chars)
                        # to avoid indexing loop variables or locals.
                        if name.isupper() and len(name) >= 2:
                            symbols.add(name)

    @staticmethod
    def _scan_js(content: str, imports: Set[str], symbols: Set[str]):
        # Strip comments first to avoid matching code inside them
        clean_content = ImportScanner._JS_BLOCK_COMMENT.sub('', content)
        clean_content = ImportScanner._JS_LINE_COMMENT.sub('', clean_content)

        # Imports
        for match in ImportScanner._JS_IMPORT_FROM.finditer(clean_content):
            imports.add(match.group(2)) 
            
        for match in ImportScanner._JS_IMPORT_SIDE_EFFECT.finditer(clean_content):
            imports.add(match.group(1))

        for match in ImportScanner._JS_REQUIRE.finditer(clean_content):
            imports.add(match.group(1))

        for match in ImportScanner._JS_EXPORT_FROM.finditer(clean_content):
            imports.add(match.group(2))

        for match in ImportScanner._JS_DYNAMIC_IMPORT.finditer(clean_content):
            imports.add(match.group(1))
            
        # Symbols
        for match in ImportScanner._JS_CLASS_DEF.finditer(clean_content):
            symbols.add(match.group(1))
            
        for match in ImportScanner._JS_FUNC_DEF.finditer(clean_content):
            symbols.add(match.group(1))
            
        for match in ImportScanner._JS_CONST_FUNC_DEF.finditer(clean_content):
            symbols.add(match.group(1))
            
        # Constants
        for match in ImportScanner._JS_CONST_VAR_DEF.finditer(clean_content):
            symbols.add(match.group(1))
```

### `src/analysis/snapshot_comparator.py`

```
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
```

### `src/api/init.py`

```
# API Module
```

### `src/api/server.py`

```
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
```

### `src/cli/__init__.py`

```

```

### `src/cli/main.py`

```
﻿import argparse
import os
import sys
from src.core.controller import run_snapshot, run_export_flatten, run_compare, run_export_diagram
from src.core.config_loader import ConfigLoader

def _parse_args():
    parser = argparse.ArgumentParser(prog="repo-runner", description="repo-runner v0.2")
    sub = parser.add_subparsers(dest="command", required=True)

    # snapshot
    snap = sub.add_parser("snapshot", help="Create a deterministic structural snapshot")
    snap.add_argument("repo_root", help="Repository root path")
    snap.add_argument("--output-root", required=False, default=None, help="Output root directory")
    snap.add_argument("--depth", type=int, default=None)
    snap.add_argument("--ignore", nargs="*", default=None)
    snap.add_argument("--include-extensions", nargs="*", default=None)
    snap.add_argument("--include-readme", action="store_true", default=None)
    snap.add_argument("--no-include-readme", action="store_false", dest="include_readme")
    snap.add_argument("--write-current-pointer", action="store_true", default=None)
    snap.add_argument("--no-write-current-pointer", action="store_false", dest="write_current_pointer")
    snap.add_argument("--skip-graph", action="store_true", default=None)
    snap.add_argument("--no-skip-graph", action="store_false", dest="skip_graph")
    snap.add_argument("--export-flatten", action="store_true", default=None)
    snap.add_argument("--no-export-flatten", action="store_false", dest="export_flatten")

    # slice
    slice_cmd = sub.add_parser("slice", help="Generate a context slice (Markdown)")
    slice_cmd.add_argument("--repo-root", required=True)
    slice_cmd.add_argument("--output-root", required=False, default=None)
    slice_cmd.add_argument("--snapshot-id", required=False, default=None)
    slice_cmd.add_argument("--focus", required=True)
    slice_cmd.add_argument("--radius", type=int, default=1)
    slice_cmd.add_argument("--max-tokens", type=int, default=None)
    slice_cmd.add_argument("--output", required=False, default=None)

    # diff
    diff_cmd = sub.add_parser("diff", help="Compare two structural snapshots")
    diff_cmd.add_argument("--base", required=True, help="Base snapshot ID or 'current'")
    diff_cmd.add_argument("--target", required=True, help="Target snapshot ID or 'current'")
    diff_cmd.add_argument("--output-root", required=False, default=None)
    diff_cmd.add_argument("--repo-root", required=False, default=".", help="Repo root to search for config")

    # diagram 
    diag_cmd = sub.add_parser("diagram", help="Generate a visual architecture diagram")
    diag_cmd.add_argument("--repo-root", required=True)
    diag_cmd.add_argument("--output-root", required=False, default=None)
    diag_cmd.add_argument("--snapshot-id", required=False, default=None)
    diag_cmd.add_argument("--output", required=False, default=None)
    diag_cmd.add_argument("--title", required=False, default=None)
    diag_cmd.add_argument("--format", choices=["mermaid", "drawio"], default="mermaid", help="Output format (default: mermaid)")

    # export
    exp = sub.add_parser("export", help="Export derived artifacts")
    exp_sub = exp.add_subparsers(dest="export_command", required=True)
    flatten = exp_sub.add_parser("flatten")
    flatten.add_argument("--repo-root", required=True)
    flatten.add_argument("--output-root", required=False, default=None)
    flatten.add_argument("--snapshot-id", required=False, default=None)
    flatten.add_argument("--output", required=False, default=None)
    flatten.add_argument("--tree-only", action="store_true", default=False)
    flatten.add_argument("--include-readme", action="store_true", default=None)
    flatten.add_argument("--no-include-readme", action="store_false", dest="include_readme")
    flatten.add_argument("--scope", required=False, default="full")
    flatten.add_argument("--title", required=False, default=None)

    # ui
    sub.add_parser("ui", help="Launch the graphical control panel")

    return parser.parse_args()


def cli_progress(phase: str, current: int, total: int):
    """
    Renders an over-writable progress line suitable for standard terminals.
    """
    if total > 0:
        msg = f"[repo-runner] {phase}: {current}/{total}"
    else:
        msg = f"[repo-runner] {phase}: {current} files found..."
    
    sys.stdout.write(f"\r{msg:<70}")
    sys.stdout.flush()


def main():
    args = _parse_args()

    if args.command == "snapshot":
        config = ConfigLoader.load_config(args.repo_root)
        output_root = args.output_root if args.output_root is not None else config.output_root
        if not output_root:
            print("Error: --output-root must be provided via CLI flag or 'repo-runner.json'")
            sys.exit(1)

        snap_id = run_snapshot(
            repo_root=args.repo_root,
            output_root=output_root,
            depth=args.depth if args.depth is not None else config.depth,
            ignore=args.ignore if args.ignore is not None else config.ignore,
            include_extensions=args.include_extensions if args.include_extensions is not None else config.include_extensions,
            include_readme=args.include_readme if args.include_readme is not None else config.include_readme,
            write_current_pointer=args.write_current_pointer if args.write_current_pointer is not None else True,
            skip_graph=args.skip_graph if args.skip_graph is not None else config.skip_graph,
            export_flatten=args.export_flatten if args.export_flatten is not None else config.export_flatten,
            progress_callback=cli_progress
        )
        print(f"\nSnapshot created:\n  {os.path.abspath(os.path.join(output_root, snap_id))}")
        return

    if args.command == "diff":
        config = ConfigLoader.load_config(args.repo_root)
        output_root = args.output_root if args.output_root is not None else config.output_root
        if not output_root:
            print("Error: --output-root must be provided via CLI flag or 'repo-runner.json'")
            sys.exit(1)

        report = run_compare(output_root, args.base, args.target)
        
        print(f"\nStructural Diff: {report.base_snapshot_id} -> {report.target_snapshot_id}")
        print("="*60)
        print(f"Files:  +{report.files_added}  -{report.files_removed}  ~{report.files_modified}")
        print(f"Edges:  +{report.edges_added}  -{report.edges_removed}")
        print("-"*60)

        for fd in report.file_diffs:
            symbol = "  [~] " if fd.status == "modified" else "  [+] " if fd.status == "added" else "  [-] "
            print(f"{symbol}{fd.stable_id}")
            
        if report.edge_diffs:
            print("\nDependency Drift:")
            for ed in report.edge_diffs:
                symbol = "  (+) " if ed.status == "added" else "  (-) "
                print(f"{symbol}{ed.source} -> {ed.target}")
        print("="*60 + "\n")
        return

    if args.command == "slice":
        config = ConfigLoader.load_config(args.repo_root)
        output_root = args.output_root if args.output_root is not None else config.output_root
        # Added validation check
        if not output_root:
            print("Error: --output-root must be provided via CLI flag or 'repo-runner.json'")
            sys.exit(1)

        out = run_export_flatten(
            output_root=output_root,
            repo_root=args.repo_root,
            snapshot_id=args.snapshot_id,
            output_path=args.output,
            tree_only=False,
            include_readme=True,
            scope="full", 
            title=f"Context Slice: {args.focus}",
            focus_id=args.focus,
            radius=args.radius,
            max_tokens=args.max_tokens,
            print_summary=True
        )
        print(f"Slice generated:\n  {os.path.abspath(out) if out else 'None'}")
        return

    if args.command == "diagram":
        config = ConfigLoader.load_config(args.repo_root)
        output_root = args.output_root if args.output_root is not None else config.output_root
        if not output_root:
            print("Error: --output-root must be provided via CLI flag or 'repo-runner.json'")
            sys.exit(1)

        out = run_export_diagram(
            output_root=output_root,
            repo_root=args.repo_root,
            snapshot_id=args.snapshot_id,
            output_path=args.output,
            title=args.title,
            format=args.format
        )
        print(f"Diagram generated ({args.format}):\n  {os.path.abspath(out)}")
        return

    if args.command == "export":
        config = ConfigLoader.load_config(args.repo_root)
        output_root = args.output_root if args.output_root is not None else config.output_root
        # Added validation check
        if not output_root:
            print("Error: --output-root must be provided via CLI flag or 'repo-runner.json'")
            sys.exit(1)

        out = run_export_flatten(
            output_root=output_root,
            repo_root=args.repo_root,
            snapshot_id=args.snapshot_id,
            output_path=args.output,
            tree_only=args.tree_only,
            include_readme=args.include_readme if args.include_readme is not None else config.include_readme,
            scope=args.scope,
            title=args.title,
        )
        print(f"Wrote Export:\n  {os.path.abspath(out)}")
        return
    
    if args.command == "ui":
        from src.gui.app import run_gui
        run_gui()
        return

if __name__ == "__main__":
    main()
```

### `src/core/__init__.py`

```
# src/core/__init__.py
```

### `src/core/config_loader.py`

```
import os
import json
from typing import Optional
from src.core.types import RepoRunnerConfig

class ConfigLoader:
    """
    Locates and parses repo-runner.json project configuration files.
    """
    
    CONFIG_FILENAME = "repo-runner.json"

    @staticmethod
    def load_config(repo_root: str) -> RepoRunnerConfig:
        """
        Attempts to load the configuration from the target repository root.
        Returns a default RepoRunnerConfig if no file exists or if parsing fails.
        """
        config_path = os.path.join(repo_root, ConfigLoader.CONFIG_FILENAME)
        
        if not os.path.exists(config_path):
            return RepoRunnerConfig()
            
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return RepoRunnerConfig.model_validate(data)
        except json.JSONDecodeError as e:
            print(f"Warning: Invalid JSON in {config_path}. Using default configuration. Error: {e}")
            return RepoRunnerConfig()
        except Exception as e:
            print(f"Warning: Failed to load {config_path}. Using default configuration. Error: {e}")
            return RepoRunnerConfig()
```

### `src/core/controller.py`

```
import os
import time
import json
from collections import defaultdict
from typing import List, Optional, Set, Dict, Callable

from src.core.types import (
    Manifest, 
    FileEntry, 
    ManifestInputs, 
    ManifestConfig, 
    ManifestStats, 
    GitMetadata,
    GraphStructure,
    SnapshotDiffReport
)
from src.core.config_loader import ConfigLoader
from src.analysis.import_scanner import ImportScanner
from src.analysis.graph_builder import GraphBuilder
from src.analysis.context_slicer import ContextSlicer
from src.analysis.snapshot_comparator import SnapshotComparator
from src.observability.token_telemetry import TokenTelemetry
from src.exporters.flatten_markdown_exporter import (
    FlattenMarkdownExporter,
    FlattenOptions,
)
from src.exporters.mermaid_exporter import MermaidExporter
from src.exporters.drawio_exporter import DrawioExporter
from src.fingerprint.file_fingerprint import FileFingerprint
from src.normalize.path_normalizer import PathNormalizer
from src.scanner.filesystem_scanner import FileSystemScanner
from src.snapshot.snapshot_loader import SnapshotLoader
from src.snapshot.snapshot_writer import SnapshotWriter
from src.structure.structure_builder import StructureBuilder


def _filter_by_extensions(abs_files: List[str], include_exts: List[str]) -> List[str]:
    if not include_exts:
        return abs_files

    include = set([e.lower() for e in include_exts])
    out =[]

    for p in abs_files:
        ext = os.path.splitext(p)[1].lower()
        if ext in include:
            out.append(p)

    return out


def run_snapshot(
    repo_root: str,
    output_root: str,
    depth: int,
    ignore: List[str],
    include_extensions: List[str],
    include_readme: bool,
    write_current_pointer: bool,
    skip_graph: bool = False,
    explicit_file_list: Optional[List[str]] = None,
    export_flatten: bool = False,
    progress_callback: Optional[Callable[[str, int, int], None]] = None,
    manual_override: bool = False 
) -> str:
    """
    Creates a snapshot. Automatically ignores the output_root if it is inside the repo_root.
    Reports progress across 3 phases: Scanning, Fingerprinting, and Analysis.
    """
    repo_root_abs = os.path.abspath(repo_root)
    output_root_abs = os.path.abspath(output_root)

    if not os.path.isdir(repo_root_abs):
        raise ValueError(f"Repository root does not exist: {repo_root_abs}")

    # --- Self-Ignore Logic ---
    effective_ignore = set(ignore)
    try:
        if os.path.commonpath([repo_root_abs, output_root_abs]) == repo_root_abs:
            rel_to_out = os.path.relpath(output_root_abs, repo_root_abs)
            top_level_segment = rel_to_out.split(os.sep)[0]
            if top_level_segment and top_level_segment != '.':
                effective_ignore.add(top_level_segment)
    except ValueError:
        pass

    if explicit_file_list is not None:
        absolute_files =[os.path.abspath(f) for f in explicit_file_list]
    else:
        def scan_cb(count: int) -> bool:
            if progress_callback:
                progress_callback("Scanning Filesystem", count, 0)
            return True
            
        scanner = FileSystemScanner(depth=depth, ignore_names=list(effective_ignore))
        absolute_files = scanner.scan([repo_root_abs], progress_callback=scan_cb)
        absolute_files = _filter_by_extensions(absolute_files, include_extensions)

    normalizer = PathNormalizer(repo_root_abs)
    file_entries: List[FileEntry] =[]
    total_bytes = 0
    
    # COLLISION DETECTION STATE
    seen_ids: Dict[str, str] = {} 

    total_files = len(absolute_files)

    for i, abs_path in enumerate(absolute_files):
        # Progress Feedback for GUI/CLI
        if progress_callback and i % 10 == 0:
            progress_callback("Fingerprinting & Analysis", i, total_files)

        if not os.path.exists(abs_path):
            continue

        normalized = normalizer.normalize(abs_path)

        if explicit_file_list is None:
            if not include_readme and os.path.basename(normalized).lower().startswith("readme"):
                continue

        stable_id = normalizer.file_id(normalized)

        # COLLISION CHECK
        if stable_id in seen_ids:
            conflicting_path = seen_ids[stable_id]
            if explicit_file_list:
                if conflicting_path == abs_path:
                    continue
            
            raise ValueError(
                f"ID Collision Detected!\n"
                f"Stable ID: {stable_id}\n"
                f"Source 1: {conflicting_path}\n"
                f"Source 2: {abs_path}\n"
                f"Repo-runner enforces lowercase IDs. "
                f"Please rename one of these files to avoid ambiguity."
            )

        seen_ids[stable_id] = abs_path
        module_path = normalizer.module_path(normalized)
        
        try:
            fp = FileFingerprint.fingerprint(abs_path)
            total_bytes += fp["size_bytes"]
            
            # --- Analysis (Imports & Symbols) ---
            imports =[]
            symbols =[]
            if not skip_graph:
                try:
                    scan_res = ImportScanner.scan(abs_path, fp["language"])
                    imports = scan_res.get("imports",[])
                    symbols = scan_res.get("symbols",[])
                except Exception:
                    pass

            entry = FileEntry(
                stable_id=stable_id,
                path=normalized,
                module_path=module_path,
                sha256=fp["sha256"],
                size_bytes=fp["size_bytes"],
                language=fp["language"],
                imports=imports,
                symbols=symbols
            )
            file_entries.append(entry)
        except OSError:
            continue

    if progress_callback:
        progress_callback("Fingerprinting & Analysis", total_files, total_files)

    file_entries = sorted(file_entries, key=lambda x: x.path)

    if progress_callback:
        progress_callback("Building Graph & Structure", total_files, total_files)

    structure = StructureBuilder().build(
        repo_id=PathNormalizer.repo_id(),
        files=file_entries,
    )

    graph = None
    external_deps =[]

    if not skip_graph:
        graph = GraphBuilder().build(file_entries)
        if graph:
            external_deps = sorted([
                n.id.replace("external:", "") 
                for n in graph.nodes 
                if n.type == "external"
            ])
    # FIX: Removed the else block that was instantiating GraphStructure. 
    # SnapshotWriter expects None to skip file creation.

    symbols_index_raw = defaultdict(list)
    for entry in file_entries:
        for sym in entry.symbols:
            symbols_index_raw[sym].append(entry.stable_id)
            
    symbols_index = {
        sym: sorted(paths) 
        for sym, paths in sorted(symbols_index_raw.items())
    }

    timestamp = time.strftime("%Y-%m-%dT%H-%M-%SZ", time.gmtime())
    
    manifest = Manifest(
        tool={"name": "repo-runner", "version": "0.2.0"},
        snapshot={
            "snapshot_id": timestamp, 
            "created_utc": timestamp,
            "output_root": output_root_abs.replace("\\", "/")
        }, 
        inputs=ManifestInputs(
            repo_root=repo_root_abs.replace("\\", "/"),
            roots=[repo_root_abs.replace("\\", "/")],
            git=GitMetadata(
                is_repo=os.path.isdir(os.path.join(repo_root_abs, ".git")),
                commit=None
            )
        ),
        config=ManifestConfig(
            depth=depth,
            ignore_names=list(effective_ignore),
            include_extensions=include_extensions,
            include_readme=include_readme,
            tree_only=False,
            skip_graph=skip_graph,
            manual_override=explicit_file_list is not None or manual_override
        ),
        stats=ManifestStats(
            file_count=len(file_entries),
            total_bytes=total_bytes,
            external_dependencies=external_deps
        ),
        files=file_entries
    )

    writer = SnapshotWriter(output_root)
    snapshot_id = writer.write(
        manifest,
        structure,
        graph=graph,
        symbols=symbols_index,
        write_current_pointer=write_current_pointer
    )

    if export_flatten:
        exporter = FlattenMarkdownExporter()
        options = FlattenOptions(
            tree_only=False,
            include_readme=True,
            scope="full"
        )
        snapshot_dir = os.path.join(output_root, snapshot_id)
        
        exporter.export(
            repo_root=repo_root_abs,
            snapshot_dir=snapshot_dir,
            manifest=manifest.model_dump(mode='json'),
            output_path=None,
            options=options,
            title=f"Auto Export: {snapshot_id}"
        )

    return snapshot_id


def run_export_flatten(
    output_root: str,
    repo_root: str,
    snapshot_id: Optional[str],
    output_path: Optional[str],
    tree_only: bool,
    include_readme: bool,
    scope: str,
    title: Optional[str],
    focus_id: Optional[str] = None,
    radius: int = 1,
    max_tokens: Optional[int] = None,
    print_summary: bool = False
) -> str:
    """
    Exports a snapshot to Markdown.
    """
    loader = SnapshotLoader(output_root)
    snapshot_dir = loader.resolve_snapshot_dir(snapshot_id)
    manifest = loader.load_manifest(snapshot_dir)

    telemetry_md = None

    if focus_id:
        graph_path = os.path.join(snapshot_dir, "graph.json")
        if not os.path.exists(graph_path):
            raise FileNotFoundError(f"Cannot slice context: graph.json missing in {snapshot_dir}")
        
        with open(graph_path, "r") as f:
            graph_data = json.load(f)
            
        sliced_manifest = ContextSlicer.slice_manifest(
            manifest=manifest, 
            graph=graph_data, 
            focus_id=focus_id, 
            radius=radius,
            max_tokens=max_tokens
        )
        
        estimated = sliced_manifest.get("stats", {}).get("estimated_tokens", 0)
        usage_str = TokenTelemetry.format_usage(estimated, max_tokens or 0)
        cycles = sliced_manifest.get("stats", {}).get("cycles_included", 0)
        
        telemetry_md = f"""
## Context Telemetry
- **Focus:** `{focus_id}`
- **Radius:** {radius}
- **Usage:** {usage_str}
- **Cycles Included:** {cycles}
"""
        manifest = sliced_manifest
        
        if print_summary and "telemetry" in manifest:
            print("\n" + "="*45)
            print(" Context Slice Summary")
            print("="*45)
            print(f" Focus:    {manifest['telemetry']['focus_id']}")
            print(f" Resolved: {manifest['telemetry']['resolved_id']}")
            print(f" Radius:   {manifest['telemetry']['radius']} hops")
            print(f" Usage:    {usage_str}")
            print(f" Files:    {manifest['stats']['file_count']}")
            print(f" Cycles:   {cycles} captured")
            print("="*45 + "\n")

        if not title:
            title = f"Context Slice: {focus_id} (Radius: {radius})"

    exporter = FlattenMarkdownExporter()

    options = FlattenOptions(
        tree_only=tree_only,
        include_readme=include_readme,
        scope=scope,
    )

    out_path = exporter.export(
        repo_root=os.path.abspath(repo_root),
        snapshot_dir=snapshot_dir,
        manifest=manifest,
        output_path=output_path,
        options=options,
        title=title,
    )

    if telemetry_md and out_path and os.path.exists(out_path):
        with open(out_path, 'r', encoding='utf-8') as f:
            content = f.read()
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(telemetry_md + "\n\n" + content)

    return out_path


def run_export_diagram(
    output_root: str,
    repo_root: str,
    snapshot_id: Optional[str],
    output_path: Optional[str],
    title: Optional[str],
    format: str = "mermaid"
) -> str:
    """
    Orchestrates the creation of a visual diagram from an existing snapshot.
    """
    loader = SnapshotLoader(output_root)
    snapshot_dir = loader.resolve_snapshot_dir(snapshot_id)
    
    graph_path = os.path.join(snapshot_dir, "graph.json")
    if not os.path.exists(graph_path):
        raise FileNotFoundError(f"graph.json not found in {snapshot_dir}. Cannot generate diagram.")
        
    with open(graph_path, "r") as f:
        graph_data = json.load(f)
        
    graph = GraphStructure.model_validate(graph_data)
    
    if format == "mermaid":
        exporter = MermaidExporter()
    elif format == "drawio":
        exporter = DrawioExporter()
    else:
        raise ValueError(f"Unknown format: {format}")
        
    return exporter.export(snapshot_dir, graph, output_path, title)


def run_compare(
    output_root: str,
    base_id: str,
    target_id: str
) -> SnapshotDiffReport:
    """
    Loads two snapshots and performs a structural diff.
    """
    loader = SnapshotLoader(output_root)
    
    dir_a = loader.resolve_snapshot_dir(base_id)
    dir_b = loader.resolve_snapshot_dir(target_id)
    
    manifest_a = Manifest.model_validate(loader.load_manifest(dir_a))
    manifest_b = Manifest.model_validate(loader.load_manifest(dir_b))
    
    ga_path = os.path.join(dir_a, "graph.json")
    gb_path = os.path.join(dir_b, "graph.json")
    
    g_a, g_b = None, None
    if os.path.exists(ga_path):
        with open(ga_path, "r") as f:
            g_a = GraphStructure.model_validate(json.load(f))
    if os.path.exists(gb_path):
        with open(gb_path, "r") as f:
            g_b = GraphStructure.model_validate(json.load(f))

    return SnapshotComparator.compare(manifest_a, manifest_b, g_a, g_b)
```

### `src/core/repo-runner.code-workspace`

```
<<BINARY_OR_SKIPPED_FILE>>
size_bytes: 0
sha256: pre-snapshot
```

### `src/core/types.py`

```
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
    metadata: Optional[Any] = None

class GraphEdge(BaseModel):
    source: str
    target: str
    relation: str = "imports"

class UnresolvedReference(BaseModel):
    """
    Represents an import statement that could not be resolved to 
    a file node OR a canonical external package.
    Commonly caused by broken relative paths or typos.
    """
    source: str
    import_ref: str

class GraphStructure(BaseModel):
    schema_version: str = "1.1" # Bumped from 1.0 for new field
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    cycles: List[List[str]] = Field(default_factory=list)
    has_cycles: bool = False
    
    # New in v1.1: Track broken links instead of silently dropping them
    unresolved_references: List[UnresolvedReference] = Field(default_factory=list)

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
```

### `src/entry_point.py`

```
# src/entry_point.py
import sys
import multiprocessing

if sys.platform.startswith('win'):
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

def launch():
    if len(sys.argv) > 1:
        from src.cli.main import main
        main()
    else:
        from src.gui.app import run_gui
        run_gui()

if __name__ == "__main__":
    multiprocessing.freeze_support()
    launch()
```

### `src/exporters/drawio_exporter.py`

```
import os
import csv
import io
from collections import defaultdict
from typing import Optional
from src.core.types import GraphStructure

class DrawioExporter:
    """
    Exports the dependency graph into Draw.io's Auto-Layout CSV format.
    When this file is imported into Draw.io, it automatically generates
    styled nodes, relationships, and module containers without requiring
    manual X/Y coordinate math.
    """

    def export(
        self,
        snapshot_dir: str,
        graph: GraphStructure,
        output_path: Optional[str] = None,
        title: Optional[str] = None
    ) -> str:
        if output_path is None:
            exports_dir = os.path.join(snapshot_dir, "exports")
            os.makedirs(exports_dir, exist_ok=True)
            output_path = os.path.join(exports_dir, "graph.drawio.csv")

        content = self._generate_csv(graph)

        with open(output_path, "w", encoding="utf-8", newline="") as f:
            f.write(content)

        return output_path

    def _generate_csv(self, graph: GraphStructure) -> str:
        # Pre-compute outgoing edges for the 'refs' column
        edges_by_source = defaultdict(list)
        for edge in graph.edges:
            edges_by_source[edge.source].append(edge.target)

        output = io.StringIO()
        
        # --- Draw.io Configuration Headers ---
        output.write("## Draw.io auto-layout CSV\n")
        output.write("# label: %label%\n")
        output.write("# style: %style%\n")
        output.write("# parent: %parent%\n")
        output.write("# connect: {\"from\": \"refs\", \"to\": \"id\", \"invert\": false, \"style\": \"edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;strokeColor=#808080;\"}\n")
        output.write("# layout: horizontalflow\n")
        output.write("# nodespacing: 40\n")
        output.write("# levelspacing: 80\n")
        output.write("# edgespacing: 40\n")
        
        # CSV Data Header
        writer = csv.writer(output)
        writer.writerow(["id", "label", "style", "refs", "parent"])

        # 1. Module Containers (Swimlanes)
        modules = set()
        for node in graph.nodes:
            if node.type != "external":
                mod_path = os.path.dirname(node.id.replace("file:", ""))
                modules.add(mod_path if mod_path else "root")
        
        for mod in sorted(modules):
            mod_id = f"module_{mod}"
            # Draw.io swimlane style
            style = "shape=swimlane;fillColor=#f8f9fa;strokeColor=#ced4da;fontColor=#212529;rounded=1;startSize=25;"
            writer.writerow([mod_id, mod, style, "", ""])

        # 2. Nodes (Files & Externals)
        cycle_nodes = {n for cycle in graph.cycles for n in cycle}

        for node in graph.nodes:
            # Comma-separated list of target IDs
            refs = ",".join(edges_by_source.get(node.id, []))
            
            if node.type == "external":
                label = node.id.replace("external:", "")
                style = "shape=ellipse;fillColor=#fff3e0;strokeColor=#e65100;fontColor=#000000;whiteSpace=wrap;"
                parent = "" # Externals float globally
            else:
                label = os.path.basename(node.id.replace("file:", ""))
                style = "shape=rectangle;fillColor=#e1f5fe;strokeColor=#01579b;fontColor=#000000;rounded=1;whiteSpace=wrap;"
                mod_path = os.path.dirname(node.id.replace("file:", ""))
                parent = f"module_{mod_path if mod_path else 'root'}"

            # Highlight cycle nodes
            if node.id in cycle_nodes:
                style += "strokeWidth=3;strokeColor=#c62828;fillColor=#ffebee;"

            writer.writerow([node.id, label, style, refs, parent])

        return output.getvalue()
```

### `src/exporters/flatten_markdown_exporter.py`

```
import os
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass(frozen=True)
class FlattenOptions:
    tree_only: bool
    include_readme: bool
    scope: str  # full | module:<path> | file:<path> | list:<a,b,c> | prefix:<path>

class FlattenMarkdownExporter:
    TEXT_EXTENSIONS = {
        ".ts", ".tsx", ".js", ".jsx",
        ".py", ".rs", ".go", ".java",
        ".json", ".md", ".txt",
        ".html", ".css", ".sql", ".toml",
        ".ps1", ".ejs", ".yml", ".yaml",
        ".env", ".example", ".gitignore",
        ".d.ts",
    }

    def generate_content(
        self,
        repo_root: str,
        manifest: Dict,
        options: FlattenOptions,
        title: Optional[str] = None,
        snapshot_id: str = "PREVIEW"
    ) -> str:
        """Generates the markdown content as a string without writing to disk."""
        files = self._canonical_files_from_manifest(manifest, options)
        tree_md = self._render_tree([f["path"] for f in files])
        content_md = "" if options.tree_only else self._render_contents(repo_root, files)

        # Header Construction
        header_lines = [
            f"# {title or 'repo-runner flatten export'}",
            "",
            f"- repo_root: `{repo_root}`",
            f"- snapshot_id: `{snapshot_id}`",
            f"- file_count: `{len(files)}`",
            f"- tree_only: `{options.tree_only}`",
            "",
        ]

        # Body Construction
        body = "\n".join(header_lines) + tree_md + ("\n" + content_md if content_md else "")

        # Footer Construction (Token Estimation)
        # We estimate tokens simply as chars / 4 for standard English/Code mix.
        # This is not exact (tiktoken would be better), but good enough for a rough gauge.
        total_chars = len(body)
        est_tokens = total_chars // 4
        
        footer_lines = [
            "",
            "---",
            "## Context Stats",
            f"- **Total Characters:** {total_chars:,}",
            f"- **Estimated Tokens:** ~{est_tokens:,} (assuming ~4 chars/token)",
            "- **Model Fit:** " + self._get_model_fit(est_tokens),
            ""
        ]
        
        return body + "\n".join(footer_lines)

    def _get_model_fit(self, tokens: int) -> str:
        if tokens < 8000: return "GPT-4 (8k)"
        if tokens < 32000: return "GPT-4 (32k)"
        if tokens < 120000: return "GPT-4 Turbo / Claude 3 Haiku (128k)"
        if tokens < 200000: return "Claude 3.5 Sonnet (200k)"
        if tokens < 1000000: return "Gemini 1.5 Pro (1M)"
        return "⚠️ EXCEEDS 1M (Chunking Required)"

    def export(
        self,
        repo_root: str,
        snapshot_dir: str,
        manifest: Dict,
        output_path: Optional[str],
        options: FlattenOptions,
        title: Optional[str] = None,
    ) -> str:
        snapshot_id = os.path.basename(snapshot_dir)
        final_md = self.generate_content(repo_root, manifest, options, title, snapshot_id)

        if output_path is None:
            exports_dir = os.path.join(snapshot_dir, "exports")
            os.makedirs(exports_dir, exist_ok=True)
            output_path = os.path.join(exports_dir, "flatten.md")

        with open(output_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(final_md)

        return output_path

    def _canonical_files_from_manifest(self, manifest: Dict, options: FlattenOptions) -> List[Dict]:
        files = manifest.get("files", [])
        entries = []
        for entry in files:
            path = entry["path"]
            if not options.include_readme and path.lower().startswith("readme"):
                continue
            entries.append(entry)
        scoped = self._apply_scope(entries, options.scope)
        scoped.sort(key=lambda x: x["path"])
        return scoped

    def _apply_scope(self, entries: List[Dict], scope: str) -> List[Dict]:
        if scope == "full": return list(entries)
        if scope.startswith("module:"):
            prefix = scope.split("module:", 1)[1].rstrip("/")
            return [e for e in entries if e["path"].startswith(prefix + "/")]
        if scope.startswith("prefix:"):
            prefix = scope.split("prefix:", 1)[1]
            return [e for e in entries if e["path"].startswith(prefix)]
        if scope.startswith("file:"):
            target = scope.split("file:", 1)[1]
            return [e for e in entries if e["path"] == target]
        if scope.startswith("list:"):
            raw = scope.split("list:", 1)[1]
            targets = [t.strip() for t in raw.split(",") if t.strip()]
            target_set = set(targets)
            return [e for e in entries if e["path"] in target_set]
        raise ValueError(f"Invalid scope: {scope}")

    def _render_tree(self, paths: List[str]) -> str:
        root = {}
        for p in paths:
            parts = [x for x in p.split("/") if x]
            node = root
            for part in parts:
                node = node.setdefault(part, {})
        lines = ["## Tree", "", "```"]
        lines.extend(self._tree_lines(root, ""))
        lines.append("```")
        lines.append("")
        return "\n".join(lines)

    def _tree_lines(self, node: Dict, prefix: str) -> List[str]:
        keys = sorted(node.keys())
        lines = []
        for i, key in enumerate(keys):
            is_last = i == len(keys) - 1
            connector = "└── " if is_last else "├── "
            lines.append(prefix + connector + key)
            child_prefix = prefix + ("    " if is_last else "│   ")
            lines.extend(self._tree_lines(node[key], child_prefix))
        return lines

    def _render_contents(self, repo_root: str, files: List[Dict]) -> str:
        blocks = ["## File Contents", ""]
        for entry in files:
            path = entry["path"]
            abs_path = os.path.join(repo_root, path.replace("/", os.sep))
            blocks.append(f"### `{path}`")
            blocks.append("")
            ext = os.path.splitext(path)[1].lower()
            if ext not in self.TEXT_EXTENSIONS or self._sniff_binary(abs_path):
                blocks.append(self._binary_placeholder(entry))
                blocks.append("")
                continue
            try:
                with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
            except OSError as e:
                content = f"<<ERROR: {e}>>"
            blocks.append(f"```")
            blocks.append(content.rstrip("\n"))
            blocks.append("```")
            blocks.append("")
        return "\n".join(blocks)

    @staticmethod
    def _sniff_binary(abs_path: str) -> bool:
        try:
            with open(abs_path, "rb") as f:
                chunk = f.read(4096)
        except OSError: return False
        return b"\x00" in chunk

    @staticmethod
    def _binary_placeholder(entry: Dict) -> str:
        return "\n".join([
            "```",
            "<<BINARY_OR_SKIPPED_FILE>>",
            f"size_bytes: {entry.get('size_bytes')}",
            f"sha256: {entry.get('sha256')}",
            "```",
        ])
```

### `src/exporters/mermaid_exporter.py`

```
import os
from typing import Dict, List, Optional, Set
from src.core.types import GraphStructure, GraphNode, GraphEdge

class MermaidExporter:
    """
    Converts a dependency graph into a Mermaid.js diagram.
    Supports:
    - Module clustering (subgraphs)
    - External dependency styling
    - Cycle highlighting
    """

    def export(
        self,
        snapshot_dir: str,
        graph: GraphStructure,
        output_path: Optional[str] = None,
        title: Optional[str] = None
    ) -> str:
        """
        Generates a .mmd file from the provided GraphStructure.
        """
        if output_path is None:
            exports_dir = os.path.join(snapshot_dir, "exports")
            os.makedirs(exports_dir, exist_ok=True)
            output_path = os.path.join(exports_dir, "graph.mmd")

        mermaid_content = self._generate_content(graph, title)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(mermaid_content)

        return output_path

    def _generate_content(self, graph: GraphStructure, title: Optional[str]) -> str:
        lines = ["graph TD"]
        
        # Styles
        lines.append("    %% Styles")
        lines.append("    classDef file fill:#e1f5fe,stroke:#01579b,stroke-width:2px;")
        lines.append("    classDef external fill:#fff3e0,stroke:#e65100,stroke-width:2px,stroke-dasharray: 5 5;")
        lines.append("    classDef cycle fill:#ffebee,stroke:#c62828,stroke-width:4px;")

        # Group Nodes by Module (for subgraphs)
        modules: Dict[str, List[GraphNode]] = {}
        externals: List[GraphNode] = []
        
        cycle_nodes = set()
        for cycle in graph.cycles:
            for node_id in cycle:
                cycle_nodes.add(node_id)

        for node in graph.nodes:
            if node.type == "external":
                externals.append(node)
                continue
            
            # Extract module path from file ID
            # file:src/core/controller.py -> src/core
            path_part = node.id.replace("file:", "")
            module_dir = os.path.dirname(path_part)
            if not module_dir:
                module_dir = "root"
            
            if module_dir not in modules:
                modules[module_dir] = []
            modules[module_dir].append(node)

        # Render External Nodes
        lines.append("\n    %% External Dependencies")
        for node in externals:
            clean_id = self._escape_id(node.id)
            label = node.id.replace("external:", "")
            lines.append(f"    {clean_id}([{label}]):::external")

        # Render Internal Modules (Subgraphs)
        lines.append("\n    %% Internal Modules")
        for module_path, nodes in sorted(modules.items()):
            safe_module_id = self._escape_id(f"subgraph_{module_path}")
            lines.append(f"    subgraph {safe_module_id} [{module_path}]")
            lines.append(f"        direction TB")
            
            for node in nodes:
                clean_id = self._escape_id(node.id)
                label = os.path.basename(node.id.replace("file:", ""))
                
                style_class = "file"
                if node.id in cycle_nodes:
                    style_class = "cycle"
                
                lines.append(f"        {clean_id}[{label}]:::{style_class}")
            
            lines.append("    end")

        # Render Edges
        lines.append("\n    %% Relationships")
        for edge in graph.edges:
            src = self._escape_id(edge.source)
            tgt = self._escape_id(edge.target)
            
            # Highlight edges that are part of a cycle
            # (Simple heuristic: if both nodes are in the SAME cycle, color it)
            is_cycle_edge = self._is_cycle_edge(edge.source, edge.target, graph.cycles)
            
            arrow = "-->"
            if is_cycle_edge:
                arrow = "-.->|CYCLE|"
                # In mermaid, we can't easily style individual edges without ID hacks, 
                # but the label helps.
            
            lines.append(f"    {src} {arrow} {tgt}")

        return "\n".join(lines)

    def _escape_id(self, raw_id: str) -> str:
        """
        Mermaid node IDs cannot contain special chars like :, /, @, ., -.
        We replace them with underscores.
        """
        return (
            raw_id
            .replace(":", "_")
            .replace("/", "_")
            .replace(".", "_")
            .replace("-", "_")
            .replace("@", "_")
        )

    def _is_cycle_edge(self, source: str, target: str, cycles: List[List[str]]) -> bool:
        for cycle in cycles:
            if source in cycle and target in cycle:
                # Check if they are adjacent in the cycle list (considering wrap-around)
                try:
                    src_idx = cycle.index(source)
                    tgt_idx = cycle.index(target)
                    
                    if (src_idx + 1) % len(cycle) == tgt_idx:
                        return True
                except ValueError:
                    continue
        return False
```

### `src/fingerprint/file_fingerprint.py`

```
import hashlib
import os
from typing import Dict


class FileFingerprint:
    LANGUAGE_MAP = {
        ".ts": "typescript",
        ".tsx": "typescript",
        ".js": "javascript",
        ".jsx": "javascript",
        ".py": "python",
        ".rs": "rust",
        ".go": "go",
        ".java": "java",
        ".html": "html",
        ".css": "css",
        ".sql": "sql",
        ".toml": "toml",
        ".ps1": "powershell",
        ".md": "markdown",
        ".json": "json",
    }

    @staticmethod
    def fingerprint(path: str) -> Dict:
        """
        Computes the fingerprint of a file.
        Raises OSError if the file cannot be opened or read (e.g. locked, permissions).
        """
        sha = hashlib.sha256()
        
        # We allow OSError to propagate so the caller (Controller) can decide 
        # whether to skip the file or fail the run.
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha.update(chunk)

        try:
            size = os.path.getsize(path)
        except OSError:
            # Fallback if getsize fails but read succeeded (rare race condition)
            size = 0 

        ext = os.path.splitext(path)[1].lower()
        language = FileFingerprint.LANGUAGE_MAP.get(ext, "unknown")

        return {
            "sha256": sha.hexdigest(),
            "size_bytes": size,
            "language": language,
        }
```

### `src/gui/__init__.py`

```
# src/gui/__init__.py
```

### `src/gui/app.py`

```
import os
import re
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import ctypes
import datetime
import time
import platform
import subprocess

from src.scanner.filesystem_scanner import FileSystemScanner
from src.normalize.path_normalizer import PathNormalizer
from src.core.controller import run_snapshot
from src.exporters.flatten_markdown_exporter import FlattenMarkdownExporter, FlattenOptions

from src.gui.components.config_tabs import ConfigTabs
from src.gui.components.tree_view import FileTreePanel
from src.gui.components.preview_pane import PreviewPanel
from src.gui.components.export_preview import ExportPreviewWindow
from src.gui.components.progress_window import ProgressWindow

# High DPI
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

class RepoRunnerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("repo-runner Control Panel")
        self.geometry("1300x900")
        
        self.style = ttk.Style(self)
        self.style.theme_use('vista' if 'vista' in self.style.theme_names() else 'clam')
        
        self.repo_root = None
        self.scan_worker = None
        
        self._build_ui()

    def _build_ui(self):
        # Top Bar: Repository Selection
        top_bar = ttk.Frame(self, padding=10)
        top_bar.pack(side=tk.TOP, fill=tk.X)
        
        ttk.Label(top_bar, text="Repository Root:").pack(side=tk.LEFT)
        self.ent_root = ttk.Entry(top_bar)
        self.ent_root.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        ttk.Button(top_bar, text="Browse...", command=self._browse).pack(side=tk.LEFT)

        # Main Workspace: Paned Window
        main_paned = ttk.PanedWindow(self, orient=tk.VERTICAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Upper: Settings Tabs & Actions
        upper_frame = ttk.Frame(main_paned)
        main_paned.add(upper_frame, weight=0)
        
        self.config_tabs = ConfigTabs(upper_frame)
        self.config_tabs.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Wire the Quick Select Apply button
        self.config_tabs.btn_apply_selection.config(command=self._apply_quick_select)
        
        action_frame = ttk.Frame(upper_frame, padding=10)
        action_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        ttk.Button(action_frame, text="Scan Repository", command=self._start_scan, width=20).pack(pady=5)
        
        self.btn_snap = ttk.Button(action_frame, text="Snapshot Selection", command=self._snapshot, state=tk.DISABLED, width=20)
        self.btn_snap.pack(pady=5)
        
        self.btn_export = ttk.Button(action_frame, text="Quick Export (Preview)", command=self._quick_export, state=tk.DISABLED, width=20)
        self.btn_export.pack(pady=5)

        self.btn_batch_export = ttk.Button(action_frame, text="Batch Export Modules", command=self._batch_export, state=tk.DISABLED, width=20)
        self.btn_batch_export.pack(pady=5)

        # Lower: Tree and Preview
        lower_paned = ttk.PanedWindow(main_paned, orient=tk.HORIZONTAL)
        main_paned.add(lower_paned, weight=1)
        
        self.tree_panel = FileTreePanel(lower_paned, self._on_file_selected)
        lower_paned.add(self.tree_panel, weight=1)
        
        self.preview_panel = PreviewPanel(lower_paned)
        lower_paned.add(self.preview_panel, weight=2)

        # Status
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W).pack(side=tk.BOTTOM, fill=tk.X)

    def _browse(self):
        path = filedialog.askdirectory()
        if path:
            self.ent_root.delete(0, tk.END)
            self.ent_root.insert(0, path)
            self.repo_root = path

    def _start_scan(self):
        root = self.ent_root.get().strip()
        if not os.path.isdir(root):
            messagebox.showerror("Error", "Invalid Repository Path")
            return
        
        self.repo_root = root
        self.tree_panel.clear()
        self.preview_panel.clear()
        
        # Disable dependent buttons during scan
        self.config_tabs.btn_apply_selection.config(state=tk.DISABLED)
        self.btn_snap.config(state=tk.DISABLED)
        self.btn_export.config(state=tk.DISABLED)
        self.btn_batch_export.config(state=tk.DISABLED)
        
        # Get settings safely on Main Thread
        depth = self.config_tabs.depth_var.get()
        ignore = set(self.config_tabs.ignore_var.get().split())
        exts = self.config_tabs.ext_var.get().split()
        readme = self.config_tabs.include_readme_var.get()
        
        # Launch Progress Window
        self.progress_win = ProgressWindow(self, title="Scanning", message=f"Scanning {root}...")
        
        # Start Worker Thread
        self.scan_worker = threading.Thread(
            target=self._scan_thread,
            args=(root, depth, ignore, exts, readme),
            daemon=True
        )
        self.scan_worker.start()

    def _scan_thread(self, root, depth, ignore, exts, readme):
        try:
            scanner = FileSystemScanner(depth=depth, ignore_names=ignore)
            
            # Define callback for the scanner
            def on_progress(count):
                if self.progress_win.cancelled:
                    return False # Stop scanning
                
                # Update UI thread
                self.after(0, lambda: self.progress_win.update_message(f"Found {count} files..."))
                return True

            abs_files = scanner.scan([root], progress_callback=on_progress)
            
            if self.progress_win.cancelled:
                self.after(0, self._scan_cancelled)
                return

            self.after(0, lambda: self.progress_win.update_message("Filtering and Normalizing..."))
            
            # Filter
            filtered = []
            ext_set = set(e.lower() for e in exts)
            for f in abs_files:
                _, ext = os.path.splitext(f)
                is_readme = readme and os.path.basename(f).lower().startswith("readme")
                if not ext_set or ext.lower() in ext_set or is_readme:
                    filtered.append(f)
            
            # Normalize for tree
            normalizer = PathNormalizer(root)
            struct = {}
            for f in filtered:
                rel = normalizer.normalize(f)
                parts = rel.split('/')
                
                # Build nested dict
                curr = struct
                for i, p in enumerate(parts):
                    is_last = (i == len(parts) - 1)
                    if is_last:
                        if p not in curr:
                            curr[p] = {}
                        curr[p]['__metadata__'] = {'abs_path': f, 'stable_id': normalizer.file_id(rel)}
                    else:
                        curr = curr.setdefault(p, {})
            
            # Success
            self.after(0, lambda: self._scan_done(struct, len(filtered)))
            
        except Exception as e:
            self.after(0, lambda: self._scan_fail(str(e)))

    def _scan_done(self, struct, count):
        self.progress_win.close()
        self.tree_panel.populate(struct)
        self.status_var.set(f"Scan Complete. Found {count} files.")
        
        # Re-enable buttons
        self.config_tabs.btn_apply_selection.config(state=tk.NORMAL)
        self.btn_snap.config(state=tk.NORMAL)
        self.btn_export.config(state=tk.NORMAL)
        self.btn_batch_export.config(state=tk.NORMAL)

    def _scan_cancelled(self):
        self.progress_win.close()
        self.status_var.set("Scan Cancelled.")

    def _scan_fail(self, error):
        self.progress_win.close()
        messagebox.showerror("Scan Error", error)
        self.status_var.set("Scan Failed.")

    def _apply_quick_select(self):
        if not self.repo_root:
            return
            
        raw_text = self.config_tabs.txt_quick_select.get("1.0", tk.END).strip()
        
        if not raw_text:
            self.tree_panel.check_specific_files(set())
            self.status_var.set("Quick Select cleared.")
            return
            
        # Parse by comma or newline
        raw_paths = [p.strip() for p in re.split(r'[,\n]+', raw_text) if p.strip()]
        target_ids = set()
        
        repo_root_norm = self.repo_root.replace('\\', '/').lower().rstrip('/')
        
        for p in raw_paths:
            p = p.replace('\\', '/')
            if p.startswith("file:"):
                target_ids.add(p.lower())
                continue
            p_lower = p.lower()
            if p_lower.startswith(repo_root_norm):
                p = p[len(repo_root_norm):]
            while p.startswith('/') or p.startswith('./'):
                if p.startswith('/'):
                    p = p[1:]
                elif p.startswith('./'):
                    p = p[2:]
            if p:
                target_ids.add(f"file:{p.lower()}")
                
        matched_count = self.tree_panel.check_specific_files(target_ids)
        self.status_var.set(f"Quick Select applied. Mapped {len(target_ids)} inputs to {matched_count} tree items.")

    def _on_file_selected(self, abs_path, stable_id):
        self.preview_panel.load_file(abs_path, stable_id)

    def _snapshot(self):
        files = self.tree_panel.get_checked_files()
        if not files:
            messagebox.showwarning("Empty", "No files selected.")
            return
            
        out = filedialog.askdirectory(title="Select Snapshot Output Root")
        if not out: return
        
        self.btn_snap.config(state=tk.DISABLED)
        self.progress_win = ProgressWindow(self, title="Snapshotting", message="Calculating Hashes and Analyzing Imports...")
        
        def run():
            try:
                sid = run_snapshot(
                    repo_root=self.repo_root,
                    output_root=out,
                    depth=self.config_tabs.depth_var.get(),
                    ignore=self.config_tabs.ignore_var.get().split(),
                    include_extensions=[],
                    include_readme=False,
                    write_current_pointer=self.config_tabs.write_current_var.get(),
                    explicit_file_list=files
                )
                self.after(0, lambda: self._snapshot_done(sid))
            except Exception as e:
                self.after(0, lambda: self._snapshot_fail(str(e)))

        threading.Thread(target=run, daemon=True).start()

    def _snapshot_done(self, sid):
        self.progress_win.close()
        self.btn_snap.config(state=tk.NORMAL)
        self.status_var.set(f"Snapshot Created: {sid}")
        messagebox.showinfo("Success", f"Snapshot Created: {sid}")

    def _snapshot_fail(self, error):
        self.progress_win.close()
        self.btn_snap.config(state=tk.NORMAL)
        self.status_var.set("Snapshot Failed.")
        messagebox.showerror("Error", error)

    def _quick_export(self):
        files = self.tree_panel.get_checked_files()
        if not files:
            messagebox.showwarning("Empty", "No files selected.")
            return

        tree_only = self.config_tabs.export_tree_only_var.get()
        self.status_var.set("Generating Export Preview...")
        self.btn_export.config(state=tk.DISABLED)
        
        def run_export():
            try:
                normalizer = PathNormalizer(self.repo_root)
                manifest_files = []
                for abs_p in files:
                    rel = normalizer.normalize(abs_p)
                    manifest_files.append({"path": rel, "size_bytes": 0, "sha256": "pre-snapshot"})
                    
                dummy_manifest = {"files": manifest_files}
                options = FlattenOptions(tree_only=tree_only, include_readme=True, scope="full")
                exporter = FlattenMarkdownExporter()
                
                content = exporter.generate_content(
                    repo_root=self.repo_root,
                    manifest=dummy_manifest,
                    options=options,
                    title=f"Quick Export: {os.path.basename(self.repo_root)}",
                    snapshot_id="QUICK_EXPORT_PREVIEW"
                )
                
                self.after(0, lambda: self._quick_export_done(content))
            except Exception as e:
                self.after(0, lambda: self._quick_export_fail(str(e)))

        threading.Thread(target=run_export, daemon=True).start()

    def _quick_export_done(self, content):
        self.btn_export.config(state=tk.NORMAL)
        self.status_var.set("Export Preview Ready.")
        default_name = f"flattened_{os.path.basename(self.repo_root)}_{datetime.date.today()}.md"
        ExportPreviewWindow(self, content, default_name)

    def _quick_export_fail(self, error):
        self.btn_export.config(state=tk.NORMAL)
        self.status_var.set("Export Failed.")
        messagebox.showerror("Export Error", error)

    def _batch_export(self):
        modules = self.tree_panel.get_modules()
        if not modules:
            messagebox.showinfo("No Modules Found", "Please click a folder checkbox in the tree to lock it as a Module Root.")
            return

        # Automatic path generation
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        folder_name = f"{timestamp}_CONTEXT"
        out_dir = os.path.join(self.repo_root, ".context", "compressed-context", folder_name)

        # Create directories safely
        os.makedirs(out_dir, exist_ok=True)
        
        self.status_var.set(f"Batch Exporting {len(modules)} modules...")
        self.btn_batch_export.config(state=tk.DISABLED)
        tree_only = self.config_tabs.export_tree_only_var.get()

        def run_batch():
            try:
                normalizer = PathNormalizer(self.repo_root)
                exporter = FlattenMarkdownExporter()

                for mod_name, abs_files in modules.items():
                    manifest_files = []
                    for abs_p in abs_files:
                        rel = normalizer.normalize(abs_p)
                        manifest_files.append({"path": rel, "size_bytes": 0, "sha256": "pre-snapshot"})

                    dummy_manifest = {"files": manifest_files}
                    options = FlattenOptions(tree_only=tree_only, include_readme=True, scope="full")

                    content = exporter.generate_content(
                        repo_root=self.repo_root,
                        manifest=dummy_manifest,
                        options=options,
                        title=f"Module Export: {mod_name}",
                        snapshot_id="BATCH_EXPORT"
                    )

                    safe_name = re.sub(r'[\\/*?:"<>|]', "", mod_name)
                    out_path = os.path.join(out_dir, f"{safe_name}-context.md")
                    
                    with open(out_path, "w", encoding="utf-8") as f:
                        f.write(content)

                self.after(0, lambda: self._batch_export_done(out_dir, len(modules)))
            except Exception as e:
                self.after(0, lambda: self._batch_export_fail(str(e)))

        threading.Thread(target=run_batch, daemon=True).start()

    def _batch_export_done(self, out_dir, count):
        self.btn_batch_export.config(state=tk.NORMAL)
        self.status_var.set(f"Batch Export Complete. Saved {count} modules to {out_dir}")
        messagebox.showinfo("Success", f"Exported {count} module files to:\n{out_dir}")
        try:
            # Automatically open the new timestamped context folder
            if platform.system() == "Windows":
                os.startfile(out_dir)
            elif platform.system() == "Darwin":
                subprocess.call(["open", out_dir])
            else:
                subprocess.call(["xdg-open", out_dir])
        except:
            pass

    def _batch_export_fail(self, error):
        self.btn_batch_export.config(state=tk.NORMAL)
        self.status_var.set("Batch Export Failed.")
        messagebox.showerror("Batch Export Error", error)

def run_gui():
    RepoRunnerApp().mainloop()
```

### `src/gui/components/config_tabs.py`

```
import tkinter as tk
from tkinter import ttk

class ConfigTabs(ttk.Notebook):
    def __init__(self, parent):
        super().__init__(parent)
        
        # Variables
        self.depth_var = tk.IntVar(value=25)
        self.ignore_var = tk.StringVar(value=".git node_modules __pycache__ dist build .next .expo .venv")
        self.ext_var = tk.StringVar(value="")
        self.include_readme_var = tk.BooleanVar(value=True)
        self.write_current_var = tk.BooleanVar(value=True)
        
        # New: Export options
        self.export_tree_only_var = tk.BooleanVar(value=False)
        
        self._build_scan_tab()
        self._build_ignore_tab()
        self._build_output_tab()

    def _build_scan_tab(self):
        tab = ttk.Frame(self, padding=10)
        self.add(tab, text=" Scan Settings ")
        
        # Depth
        row1 = ttk.Frame(tab)
        row1.pack(fill=tk.X, pady=5)
        ttk.Label(row1, text="Maximum Traversal Depth:", width=25).pack(side=tk.LEFT)
        ttk.Spinbox(row1, from_=0, to=100, textvariable=self.depth_var, width=10).pack(side=tk.LEFT)
        
        # Extensions
        row2 = ttk.Frame(tab)
        row2.pack(fill=tk.X, pady=5)
        ttk.Label(row2, text="Include Extensions:", width=25).pack(side=tk.LEFT)
        ttk.Entry(row2, textvariable=self.ext_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(row2, text="(space separated, e.g. .ts .py)", font=("Segoe UI", 8), foreground="gray").pack(side=tk.LEFT, padx=5)

        # Readme
        row3 = ttk.Frame(tab)
        row3.pack(fill=tk.X, pady=5)
        ttk.Checkbutton(row3, text="Always include README files (overrides extension filter)", variable=self.include_readme_var).pack(side=tk.LEFT)

        # Quick Select
        row4 = ttk.Frame(tab)
        row4.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        lbl_frame = ttk.Frame(row4)
        lbl_frame.pack(fill=tk.X)
        ttk.Label(lbl_frame, text="Quick Select (Comma or newline separated paths):").pack(side=tk.LEFT)
        
        # Stored reference to wire in app.py
        self.btn_apply_selection = ttk.Button(lbl_frame, text="Apply Selection", state=tk.DISABLED)
        self.btn_apply_selection.pack(side=tk.RIGHT)
        
        self.txt_quick_select = tk.Text(row4, height=4, font=("Segoe UI", 9))
        self.txt_quick_select.pack(fill=tk.BOTH, expand=True, pady=(2, 0))

    def _build_ignore_tab(self):
        tab = ttk.Frame(self, padding=10)
        self.add(tab, text=" Ignore Rules ")
        
        ttk.Label(tab, text="Directory and File names to ignore:").pack(anchor=tk.W, pady=(0, 5))
        txt_ignore = tk.Text(tab, height=4, font=("Segoe UI", 9))
        txt_ignore.pack(fill=tk.BOTH, expand=True)
        
        # Sync the text box with the variable
        txt_ignore.insert("1.0", self.ignore_var.get())
        def sync_var(event=None):
            self.ignore_var.set(txt_ignore.get("1.0", tk.END).strip())
        txt_ignore.bind("<KeyRelease>", sync_var)

    def _build_output_tab(self):
        tab = ttk.Frame(self, padding=10)
        self.add(tab, text=" Output / Export ")
        
        # Snapshot Config
        lbl_snap = ttk.Label(tab, text="Snapshot Config", font=("Segoe UI", 9, "bold"))
        lbl_snap.pack(anchor=tk.W, pady=(0, 5))
        
        ttk.Checkbutton(tab, text="Update 'current.json' pointer on snapshot", variable=self.write_current_var).pack(anchor=tk.W, pady=2)
        
        ttk.Separator(tab, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=15)
        
        # Export Config
        lbl_exp = ttk.Label(tab, text="Quick Export Config", font=("Segoe UI", 9, "bold"))
        lbl_exp.pack(anchor=tk.W, pady=(0, 5))
        
        ttk.Checkbutton(tab, text="Tree Only (No file contents)", variable=self.export_tree_only_var).pack(anchor=tk.W, pady=2)

        ttk.Label(tab, text="Note: Snapshots are always created in a timestamped subfolder.", 
                  font=("Segoe UI", 8, "italic"), foreground="gray").pack(side=tk.BOTTOM, anchor=tk.W, pady=10)
```

### `src/gui/components/export_preview.py`

```
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

class ExportPreviewWindow(tk.Toplevel):
    def __init__(self, parent, content, default_filename="export.md"):
        super().__init__(parent)
        self.title("Export Preview & Token Estimator")
        self.geometry("1100x800")
        
        self.content = content
        self.default_filename = default_filename
        
        self._build_ui()
        
        # Behavior: Focus on this window
        self.focus_force()

    def _build_ui(self):
        # Toolbar
        toolbar = ttk.Frame(self, padding=5)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        
        # Actions
        btn_frame = ttk.Frame(toolbar)
        btn_frame.pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="💾 Save to File...", command=self._save).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="📋 Copy to Clipboard", command=self._copy).pack(side=tk.LEFT, padx=2)
        
        # Stats Calculation
        lines = self.content.count('\n') + 1
        chars = len(self.content)
        est_tokens = chars // 4
        
        # Context Health Logic
        if est_tokens < 8192:
            status_color = "#008000" # Green
            model_hint = "Fits: GPT-4 (8k)"
        elif est_tokens < 32768:
            status_color = "#228B22" # Forest Green
            model_hint = "Fits: GPT-4 (32k)"
        elif est_tokens < 128000:
            status_color = "#B8860B" # Dark Goldenrod
            model_hint = "Fits: GPT-4 Turbo / Claude 3 (128k)"
        elif est_tokens < 200000:
            status_color = "#FF8C00" # Dark Orange
            model_hint = "Fits: Claude 3.5 Sonnet (200k)"
        elif est_tokens < 1000000:
            status_color = "#FF4500" # Orange Red
            model_hint = "Fits: Gemini 1.5 Pro (1M)"
        else:
            status_color = "#FF0000" # Red
            model_hint = "⚠ EXCEEDS 1M TOKENS (Chunking Required)"

        # Stats Display
        stats_frame = ttk.Frame(toolbar)
        stats_frame.pack(side=tk.RIGHT, padx=10)

        # Basic Stats
        lbl_basic = ttk.Label(
            stats_frame, 
            text=f"Lines: {lines:,}  |  Chars: {chars:,}  |  ", 
            font=("Segoe UI", 9)
        )
        lbl_basic.pack(side=tk.LEFT)

        # Token Stats (Bold + Color)
        lbl_tokens = tk.Label(
            stats_frame, 
            text=f"~{est_tokens:,} Tokens", 
            font=("Segoe UI", 9, "bold"),
            fg=status_color
        )
        lbl_tokens.pack(side=tk.LEFT)
        
        # Model Hint
        lbl_hint = tk.Label(
            stats_frame,
            text=f"  [{model_hint}]",
            font=("Segoe UI", 8, "italic"),
            fg="gray"
        )
        lbl_hint.pack(side=tk.LEFT)

        # Separator
        ttk.Separator(self, orient=tk.HORIZONTAL).pack(fill=tk.X)

        # Content Area
        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.text_area = tk.Text(container, wrap=tk.NONE, font=("Consolas", 10), undo=False)
        self.text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        ysb = ttk.Scrollbar(container, orient=tk.VERTICAL, command=self.text_area.yview)
        ysb.pack(side=tk.RIGHT, fill=tk.Y)
        
        xsb = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.text_area.xview)
        xsb.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.text_area.configure(yscrollcommand=ysb.set, xscrollcommand=xsb.set)
        
        # Insert content (read-only state after insert)
        # Note: For massive files (100MB+), inserting into Tkinter Text widget is slow.
        # We truncate the preview visually if it's absurdly large, but keep the full content for saving/copying.
        
        PREVIEW_LIMIT = 5_000_000 # 5MB Preview Limit
        
        if chars > PREVIEW_LIMIT:
            preview_text = self.content[:PREVIEW_LIMIT] + f"\n\n... [Preview Truncated due to size ({chars:,} chars). Full content preserved for Save/Copy] ..."
            self.text_area.insert("1.0", preview_text)
            
            # Add a warning banner
            lbl_warn = ttk.Label(self, text=f"⚠ Preview truncated for performance. Full output ({chars:,} chars) is ready to save.", background="#fff3cd", anchor=tk.CENTER)
            lbl_warn.pack(side=tk.TOP, fill=tk.X, before=container)
        else:
            self.text_area.insert("1.0", self.content)
            
        self.text_area.configure(state=tk.DISABLED)

    def _save(self):
        out_path = filedialog.asksaveasfilename(
            defaultextension=".md",
            filetypes=[("Markdown", "*.md"), ("All Files", "*.*")],
            initialfile=self.default_filename,
            title="Save Export"
        )
        if out_path:
            try:
                # We write self.content (the full string), not the truncated preview
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(self.content)
                messagebox.showinfo("Saved", f"Successfully saved to:\n{out_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file:\n{e}")

    def _copy(self):
        self.clipboard_clear()
        self.clipboard_append(self.content)
        messagebox.showinfo("Copied", "Content copied to clipboard!")
```

### `src/gui/components/preview_pane.py`

```
import tkinter as tk
from tkinter import ttk
from src.fingerprint.file_fingerprint import FileFingerprint
from src.analysis.import_scanner import ImportScanner

class PreviewPanel(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        
        # Metadata Header (Brief)
        self.lbl_meta = ttk.Label(self, text="Select a file to preview properties.", 
                                  background="#f0f0f0", padding=5, relief=tk.RIDGE)
        self.lbl_meta.pack(fill=tk.X, side=tk.TOP)
        
        # Text Area
        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True)
        
        self.text_preview = tk.Text(container, wrap=tk.NONE, font=("Consolas", 10), undo=False)
        self.text_preview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=self.text_preview.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_preview.configure(yscrollcommand=scrollbar.set)
        
        # --- Syntax Highlighting Tags ---
        # A very basic "poor man's highlighter"
        self.text_preview.tag_configure("keyword", foreground="#0000FF") # Blue
        self.text_preview.tag_configure("string", foreground="#A31515")  # Red
        self.text_preview.tag_configure("comment", foreground="#008000") # Green
        self.text_preview.tag_configure("header", foreground="#800080", font=("Consolas", 10, "bold")) # Purple

    def clear(self):
        self.text_preview.delete("1.0", tk.END)
        self.lbl_meta.config(text="Select a file to preview properties.")

    def load_file(self, abs_path, stable_id):
        self.clear()
        try:
            # 1. Fingerprint (Size, SHA, Lang)
            fp = FileFingerprint.fingerprint(abs_path)
            
            # 2. Scan Imports (Lazy load on click using detected language)
            scan_res = ImportScanner.scan(abs_path, fp['language'])
            
            # Extract the actual lists from the dictionary
            actual_imports = scan_res.get('imports', [])
            actual_symbols = scan_res.get('symbols', [])
            
            # 3. Update Brief Header Label
            import_count = len(actual_imports)
            symbol_count = len(actual_symbols)
            self.lbl_meta.config(text=f" ID: {stable_id}  |  {fp['language']}  |  {import_count} Imports  |  {symbol_count} Symbols")

            # 4. Construct Detailed Metadata Header
            header_lines = [
                f"Path:    {abs_path}",
                f"SHA256:  {fp['sha256']}",
                f"Size:    {fp['size_bytes']:,} bytes",
                "-" * 60,
                "IMPORTS FOUND:",
            ]
            
            if actual_imports:
                for imp in actual_imports:
                    header_lines.append(f"  • {imp}")
            else:
                header_lines.append("  (none)")
                
            header_lines.append("")
            header_lines.append("SYMBOLS DEFINED:")
            
            if actual_symbols:
                for sym in actual_symbols:
                    header_lines.append(f"  ♦ {sym}")
            else:
                header_lines.append("  (none)")
                
            header_lines.append("-" * 60)
            header_lines.append("") # Spacer line
            
            full_header = "\n".join(header_lines)
            
            # 5. Insert Header
            self.text_preview.insert("1.0", full_header, "header")

            # 6. Append Real File Content
            if fp['size_bytes'] > 250_000:
                self.text_preview.insert(tk.END, "\n<< File too large for preview >>")
            else:
                try:
                    with open(abs_path, 'r', encoding='utf-8', errors='replace') as f:
                        content = f.read()
                        self.text_preview.insert(tk.END, content)
                        # Apply minimal highlighting after insert
                        self._highlight_syntax(content)
                except Exception as e:
                    self.text_preview.insert(tk.END, f"\n<< Error reading file: {e} >>")
                    
        except Exception as e:
            self.text_preview.insert("1.0", f"<< Error processing file: {e} >>")

    def _highlight_syntax(self, content):
        """Very basic highlighting for common keywords. 
           This is not a full lexer, just a visual aid."""
        keywords = {
            "def", "class", "import", "from", "return", "if", "else", "elif", 
            "for", "while", "try", "except", "with", "as", "pass", "lambda",
            "const", "let", "var", "function", "export", "interface", "type"
        }
        
        # We start searching after the header (heuristic: header is ~15 lines)
        start_index = "15.0" 
        
        for kw in keywords:
            # Search for whole words only
            idx = start_index
            while True:
                # search pattern, stop index, nocase, count, regexp...
                # using a regex to ensure word boundaries would be better, but simpler approach first:
                # We'll just search for the string. To do word boundaries in Tkinter search requires strict mode.
                idx = self.text_preview.search(kw, idx, stopindex=tk.END)
                if not idx:
                    break
                
                # Check length to calculate end index
                end_idx = f"{idx}+{len(kw)}c"
                
                # Apply tag
                self.text_preview.tag_add("keyword", idx, end_idx)
                
                # Move to next
                idx = end_idx
```

### `src/gui/components/progress_window.py`

```
import tkinter as tk
from tkinter import ttk

class ProgressWindow(tk.Toplevel):
    def __init__(self, parent, title="Processing...", message="Please wait"):
        super().__init__(parent)
        self.title(title)
        self.geometry("400x150")
        self.resizable(False, False)
        
        # Modal behavior
        self.transient(parent)
        self.grab_set()
        
        self.cancelled = False
        
        # Center the window
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
        
        self._build_ui(message)
        
    def _build_ui(self, message):
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        self.lbl_msg = ttk.Label(frame, text=message, wraplength=360)
        self.lbl_msg.pack(pady=(0, 15), anchor=tk.W)
        
        self.progress = ttk.Progressbar(frame, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=(0, 15))
        self.progress.start(15)
        
        self.btn_cancel = ttk.Button(frame, text="Cancel", command=self.cancel)
        self.btn_cancel.pack(anchor=tk.E)
        
    def update_message(self, text):
        self.lbl_msg.config(text=text)
        
    def update_progress(self, current: int, total: int = 0):
        """
        Dynamically shifts from indeterminate to determinate if total is known.
        """
        if total > 0:
            if self.progress.cget('mode') == 'indeterminate':
                self.progress.stop()
                self.progress.config(mode='determinate', maximum=total)
            self.progress['value'] = current
        else:
            if self.progress.cget('mode') == 'determinate':
                self.progress.config(mode='indeterminate')
                self.progress.start(15)
        
    def cancel(self):
        self.cancelled = True
        self.lbl_msg.config(text="Cancelling... please wait.")
        self.btn_cancel.state(['disabled'])

    def close(self):
        self.grab_release()
        self.destroy()
```

### `src/gui/components/tree_view.py`

```
import os
import tkinter as tk
from tkinter import ttk

class FileTreePanel(ttk.Frame):
    def __init__(self, parent, on_select_callback):
        super().__init__(parent)
        self.on_select_callback = on_select_callback
        
        tools = ttk.Frame(self)
        tools.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(tools, text="☑ Check All", command=lambda: self._bulk_toggle(True), width=12).pack(side=tk.LEFT)
        ttk.Button(tools, text="☐ Uncheck All", command=lambda: self._bulk_toggle(False), width=12).pack(side=tk.LEFT, padx=5)
        
        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True)
        
        self.tree = ttk.Treeview(container, columns=("check", "size", "id"), selectmode="browse")
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.column("#0", width=300, minwidth=200)
        self.tree.heading("#0", text="File / Folder Name", anchor=tk.W)
        
        self.tree.column("check", width=40, minwidth=40, stretch=False, anchor=tk.CENTER)
        self.tree.heading("check", text="Inc.")
        
        self.tree.column("size", width=80, anchor=tk.E)
        self.tree.heading("size", text="Size")
        
        self.tree.column("id", width=150)
        self.tree.heading("id", text="Stable ID")
        
        # UI Tags for locked modules
        self.tree.tag_configure("locked", foreground="#999999")
        self.tree.tag_configure("module_root", font=("Segoe UI", 9, "bold"), foreground="#0055AA")
        
        self.tree.bind("<Button-1>", self._on_click)
        self.tree.bind("<<TreeviewSelect>>", self._on_selection_change)

    def clear(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

    def _on_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region == "cell":
            column = self.tree.identify_column(event.x)
            item_id = self.tree.identify_row(event.y)
            
            if column == "#1" and item_id:
                tags = self.tree.item(item_id, "tags")
                if "locked" in tags:
                    # Ignore clicks on locked children
                    return "break"
                
                self._toggle_item(item_id)
                return "break"
        return

    def _set_node_state(self, item_id, check_state, add_tags=None, remove_tags=None):
        vals = list(self.tree.item(item_id, "values"))
        vals[0] = check_state
        self.tree.item(item_id, values=vals)

        tags = list(self.tree.item(item_id, "tags"))
        changed = False
        if add_tags:
            for t in add_tags:
                if t not in tags:
                    tags.append(t)
                    changed = True
        if remove_tags:
            for t in remove_tags:
                if t in tags:
                    tags.remove(t)
                    changed = True
        if changed:
            self.tree.item(item_id, tags=tags)

    def _lock_children(self, parent_id, lock: bool):
        for child in self.tree.get_children(parent_id):
            tags = list(self.tree.item(child, "tags"))
            state = "☑" if lock else "☐"

            # Always strip module_root if a parent asserts a lock over this node
            if "module_root" in tags:
                tags.remove("module_root")

            if lock:
                if "locked" not in tags:
                    tags.append("locked")
            else:
                if "locked" in tags:
                    tags.remove("locked")

            self.tree.item(child, tags=tags)
            vals = list(self.tree.item(child, "values"))
            vals[0] = state
            self.tree.item(child, values=vals)

            self._lock_children(child, lock)

    def _toggle_item(self, item_id):
        current_vals = list(self.tree.item(item_id, "values"))
        current_check = current_vals[0]
        new_state = "☐" if current_check == "☑" else "☑"
        
        tags = list(self.tree.item(item_id, "tags"))
        if "folder" in tags:
            if new_state == "☑":
                self._set_node_state(item_id, "☑", add_tags=["module_root"])
                self._lock_children(item_id, True)
            else:
                self._set_node_state(item_id, "☐", remove_tags=["module_root"])
                self._lock_children(item_id, False)
        else:
            self._set_node_state(item_id, new_state)

    def _bulk_toggle(self, checked: bool):
        """Standard check/uncheck that clears all locks."""
        state = "☑" if checked else "☐"
        def recurse(item_id):
            self._set_node_state(item_id, state, remove_tags=["locked", "module_root"])
            for child in self.tree.get_children(item_id):
                recurse(child)
                
        for child in self.tree.get_children(""):
            recurse(child)

    def check_specific_files(self, target_stable_ids: set) -> int:
        self._bulk_toggle(False)
        matched = [0]
        
        def traverse_and_check(item_id) -> bool:
            vals = list(self.tree.item(item_id, "values"))
            tags = self.tree.item(item_id, "tags")
            is_file = tags and tags[0] != "folder"
            
            has_checked_child = False
            
            if is_file:
                stable_id = vals[2]
                if stable_id in target_stable_ids:
                    vals[0] = "☑"
                    self.tree.item(item_id, values=vals)
                    matched[0] += 1
                    return True
            else:
                for child in self.tree.get_children(item_id):
                    if traverse_and_check(child):
                        has_checked_child = True
                        
                if has_checked_child:
                    self.tree.item(item_id, open=True)
                    
            return has_checked_child

        for child in self.tree.get_children():
            traverse_and_check(child)
            
        return matched[0]

    def _on_selection_change(self, event):
        selected = self.tree.selection()
        if selected:
            tags = self.tree.item(selected[0], "tags")
            if tags and tags[0] != "folder":
                stable_id = self.tree.item(selected[0], "values")[2]
                self.on_select_callback(tags[0], stable_id)

    def populate(self, tree_structure):
        self.clear()
        
        def insert_node(parent_id, structure):
            keys = sorted(structure.keys())
            folders = [k for k in keys if k != '__metadata__' and '__metadata__' not in structure[k]]
            files = [k for k in keys if k != '__metadata__' and '__metadata__' in structure[k]]
            
            for name in folders + files:
                node_data = structure[name]
                is_file = '__metadata__' in node_data
                
                values = ["☑", "", ""]
                
                if is_file:
                    meta = node_data['__metadata__']
                    try:
                        size = os.path.getsize(meta['abs_path'])
                        values = ["☑", f"{size:,} B", meta['stable_id']]
                    except OSError:
                        values = ["☑", "Err", meta['stable_id']]
                    icon = "📄 "
                else:
                    icon = "📁 "

                item_id = self.tree.insert(parent_id, "end", text=f"{icon}{name}", values=values, open=False)
                
                if is_file:
                    self.tree.item(item_id, tags=(node_data['__metadata__']['abs_path'], "file"))
                else:
                    self.tree.item(item_id, tags=("folder",))
                    insert_node(item_id, node_data)

        insert_node("", tree_structure)

    def get_checked_files(self, parent_id="") -> list:
        paths = []
        for item_id in self.tree.get_children(parent_id):
            vals = self.tree.item(item_id, "values")
            if vals[0] == "☑":
                tags = self.tree.item(item_id, "tags")
                if tags and tags[0] != "folder":
                    paths.append(tags[0])
            paths.extend(self.get_checked_files(item_id))
        return paths

    def get_modules(self) -> dict:
        """
        Returns a dictionary of { "module_name": [list_of_abs_paths] }
        for all nodes explicitly tagged as module_root.
        """
        modules = {}
        def traverse(item_id):
            tags = self.tree.item(item_id, "tags")
            if "module_root" in tags:
                raw_text = self.tree.item(item_id, "text")
                name = raw_text.replace("📁 ", "").strip()
                paths = self.get_checked_files(item_id)
                modules[name] = paths
            else:
                for child in self.tree.get_children(item_id):
                    traverse(child)

        for child in self.tree.get_children(""):
            traverse(child)

        return modules
```

### `src/normalize/path_normalizer.py`

```
import os


class PathNormalizer:
    def __init__(self, repo_root: str):
        self.repo_root = os.path.abspath(repo_root)

    def normalize(self, absolute_path: str) -> str:
        """
        Converts an absolute path to a repo-relative, lowercased, forward-slash normalized string.
        Raises ValueError if the path escapes the repo root.
        """
        # 1. Compute relative path
        try:
            relative = os.path.relpath(absolute_path, self.repo_root)
        except ValueError:
            # On Windows, relpath fails if drives differ (C: vs D:)
            raise ValueError(f"Path {absolute_path} is on a different drive than repo root {self.repo_root}")

        # 2. Normalize separators immediately to handle cross-OS logic safely
        normalized = relative.replace("\\", "/")

        # 3. Security: Check for Root Escape
        # We check for ".." segments at the start.
        if normalized.startswith("../") or normalized == "..":
            raise ValueError(f"Path escapes repository root: {normalized} (from {absolute_path})")

        # 4. Strip purely decorative prefixes
        if normalized.startswith("./"):
            normalized = normalized[2:]

        # 5. Defensive: Strip leading slashes (shouldn't happen with relpath but be safe)
        while normalized.startswith("/"):
            normalized = normalized[1:]

        # 6. Enforce Lowercase (v0.2 Spec)
        return normalized.lower()

    def module_path(self, normalized_file_path: str) -> str:
        """
        Derives the module (directory) path from a normalized file path.
        Returns '.' if the file is at the repo root.
        """
        directory = os.path.dirname(normalized_file_path)
        
        # Standardize empty directory (root) to "."
        if not directory or directory == "":
            return "."
            
        return directory.replace("\\", "/")

    @staticmethod
    def file_id(normalized_path: str) -> str:
        return f"file:{normalized_path}"

    @staticmethod
    def module_id(module_path: str) -> str:
        # If the module is root, we map it to repo:root logically, 
        # but if we need a distinct ID for the directory node:
        if module_path == ".":
            return "module:." 
        return f"module:{module_path}"

    @staticmethod
    def repo_id() -> str:
        return "repo:root"
```

### `src/observability/init.py`

```
# Observability Module
# Responsible for tracking LLM tokenomics, performance heuristics, and system telemetry.
```

### `src/observability/token_telemetry.py`

```
from typing import Dict, Any, Optional

class TokenTelemetry:
    # Approximate tokens per byte (Average for code: ~4 chars per token)
    TOKENS_PER_BYTE = 0.25 
    
    # Cost per 1M input tokens (GPT-4o pricing heuristic)
    COST_PER_1M_INPUT = 5.00

    @staticmethod
    def estimate_tokens(size_bytes: int, language: str = "unknown") -> int:
        """
        Estimates token count based on file size.
        """
        return int(size_bytes * TokenTelemetry.TOKENS_PER_BYTE)

    @staticmethod
    def format_usage(current: int, max_tokens: int) -> str:
        """
        Returns a formatted string like '100/500 (20.0%)'.
        """
        if max_tokens <= 0:
            return f"{current} tokens"
        percent = (current / max_tokens) * 100
        return f"{current}/{max_tokens} ({percent:.1f}%)"

    @staticmethod
    def calculate_telemetry(
        original_manifest: Dict[str, Any],
        sliced_manifest: Dict[str, Any],
        focus_id: str,
        radius: int
    ) -> str:
        """
        Generates a markdown summary of the context slicing reduction.
        Calculates reduction percentage, estimated tokens, and cost.
        """
        orig_stats = original_manifest.get("stats", {})
        orig_count = orig_stats.get("file_count", 0)
        orig_bytes = orig_stats.get("total_bytes", 0)
        
        slice_stats = sliced_manifest.get("stats", {})
        slice_count = slice_stats.get("file_count", 0)
        
        # Calculate sliced bytes: prefer stats, fallback to summing file entries
        slice_bytes = slice_stats.get("total_bytes", 0)
        if slice_bytes == 0 and "files" in sliced_manifest:
            slice_bytes = sum(f.get("size_bytes", 0) for f in sliced_manifest["files"])

        # Calculate reduction
        reduction_bytes = orig_bytes - slice_bytes
        reduction_pct = (reduction_bytes / orig_bytes * 100) if orig_bytes > 0 else 0.0
        
        # Estimate tokens & Cost
        est_tokens = TokenTelemetry.estimate_tokens(slice_bytes)
        cost = (est_tokens / 1_000_000) * TokenTelemetry.COST_PER_1M_INPUT
        
        # Format Markdown (Must match test expectations)
        return f"""
## Context Telemetry
- **Focus:** `{focus_id}`
- **Radius:** {radius}
- **Reduction:** {reduction_pct:.1f}% reduction (Pruned from {orig_count} total files)
- **Content Size:** {slice_bytes:,} bytes (Original: {orig_bytes:,} bytes)
- **Estimated Tokens:** {est_tokens:,}
- **Est. Input Cost (GPT-4o):** ${cost:.5f}
"""
```

### `src/scanner/filesystem_scanner.py`

```
import os
from typing import List, Set, Optional, Callable


class FileSystemScanner:
    def __init__(self, depth: int, ignore_names: Set[str]):
        self.depth = depth
        self.ignore_names = ignore_names

    def scan(self, root_paths: List[str], progress_callback: Optional[Callable[[int], None]] = None) -> List[str]:
        all_files = []
        visited_realpaths = set()
        count = 0

        for root in root_paths:
            # Hardening: Resolve user provided paths to realpaths immediately.
            try:
                abs_root = os.path.realpath(root)
            except OSError:
                continue

            # Handle explicit file inputs
            if os.path.isfile(abs_root):
                all_files.append(abs_root)
                count += 1
                if progress_callback and count % 100 == 0:
                     if not progress_callback(count): return all_files
                continue

            # Handle directories
            if os.path.isdir(abs_root):
                # We start the recursive walk
                if not self._walk(abs_root, 0, all_files, visited_realpaths, progress_callback):
                    # If _walk returns False, it means scan was cancelled
                    return sorted(all_files)

        return sorted(all_files)

    def _walk(self, directory: str, current_depth: int, results: List[str], visited: Set[str], 
              progress_callback: Optional[Callable[[int], bool]]) -> bool:
        """
        Returns True if walk should continue, False if cancelled.
        """
        if self.depth >= 0 and current_depth > self.depth:
            return True

        # 1. Symlink Cycle Detection & Canonicalization
        try:
            real_path = os.path.realpath(directory)
            if real_path in visited:
                return True
            visited.add(real_path)
        except OSError:
            return True

        # 2. List Directory (Robust)
        try:
            entries = sorted(os.listdir(directory))
        except (PermissionError, OSError):
            return True

        for entry in entries:
            if entry in self.ignore_names:
                continue

            full_path = os.path.join(directory, entry)

            # 3. Classify and Recurse
            try:
                if os.path.isdir(full_path):
                    if not self._walk(full_path, current_depth + 1, results, visited, progress_callback):
                        return False
                elif os.path.isfile(full_path):
                    results.append(os.path.abspath(full_path))
                    
                    # Report Progress every 50 files to avoid UI spam
                    if progress_callback and len(results) % 50 == 0:
                        should_continue = progress_callback(len(results))
                        if not should_continue:
                            return False
            except (PermissionError, OSError):
                continue
                
        return True
```

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

### `src/structure/structure_builder.py`

```
from typing import List, Dict, Any
from src.core.types import FileEntry

class StructureBuilder:
    def build(self, repo_id: str, files: List[FileEntry]) -> Dict[str, Any]:
        """
        Organizes files into a hierarchical structure.
        Accepts Pydantic Models for FileEntry.
        """
        
        # Root Structure
        structure = {
            "schema_version": "1.0",
            "repo": {
                "stable_id": repo_id,
                "root": ".",
                "modules": []
            }
        }
        
        modules_map = {}
        
        for f in files:
            # Attribute access
            mod_path = f.module_path
            
            if mod_path not in modules_map:
                modules_map[mod_path] = {
                    "stable_id": f"module:{mod_path}",
                    "path": mod_path,
                    "files": []
                }
            
            modules_map[mod_path]["files"].append(f.stable_id)
            
        # Convert map to sorted list
        sorted_keys = sorted(modules_map.keys())
        for k in sorted_keys:
            structure["repo"]["modules"].append(modules_map[k])
            
        return structure
```

---
## Context Stats
- **Total Characters:** 138,086
- **Estimated Tokens:** ~34,521 (assuming ~4 chars/token)
- **Model Fit:** GPT-4 Turbo / Claude 3 Haiku (128k)
