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