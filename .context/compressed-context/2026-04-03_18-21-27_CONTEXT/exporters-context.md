# Module Export: exporters

- repo_root: `C:/projects/repo-runner`
- snapshot_id: `BATCH_EXPORT`
- file_count: `3`
- tree_only: `False`
## Tree

```
└── src
    └── exporters
        ├── drawio_exporter.py
        ├── flatten_markdown_exporter.py
        └── mermaid_exporter.py
```

## File Contents

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

---
## Context Stats
- **Total Characters:** 16,483
- **Estimated Tokens:** ~4,120 (assuming ~4 chars/token)
- **Model Fit:** GPT-4 (8k)
