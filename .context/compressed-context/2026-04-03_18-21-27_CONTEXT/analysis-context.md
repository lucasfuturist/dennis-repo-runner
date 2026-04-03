# Module Export: analysis

- repo_root: `C:/projects/repo-runner`
- snapshot_id: `BATCH_EXPORT`
- file_count: `5`
- tree_only: `False`
## Tree

```
└── src
    └── analysis
        ├── __init__.py
        ├── context_slicer.py
        ├── graph_builder.py
        ├── import_scanner.py
        └── snapshot_comparator.py
```

## File Contents

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

---
## Context Stats
- **Total Characters:** 27,120
- **Estimated Tokens:** ~6,780 (assuming ~4 chars/token)
- **Model Fit:** GPT-4 (8k)
