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