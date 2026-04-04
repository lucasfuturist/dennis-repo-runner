import os
import json
import argparse
from typing import List

def render_ascii_tree(paths: List[str]) -> str:
    """
    Builds a standard ASCII directory tree from a list of relative file paths.
    """
    tree = {}
    for path in paths:
        parts = path.split('/')
        curr = tree
        for part in parts:
            curr = curr.setdefault(part, {})
            
    lines = ["."]
    
    def _walk(node, prefix=""):
        entries = sorted(node.keys())
        for i, key in enumerate(entries):
            is_last = (i == len(entries) - 1)
            connector = "└── " if is_last else "├── "
            
            # If the node has children, it's a directory
            if node[key]:
                lines.append(f"{prefix}{connector}{key}/")
                extension = "    " if is_last else "│   "
                _walk(node[key], prefix + extension)
            else:
                lines.append(f"{prefix}{connector}{key}")
                
    _walk(tree)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Stitches compressed JSON state into a single Markdown context file.")
    parser.add_argument("--state-dir", required=True, help="Directory containing master_compressed_context.json")
    parser.add_argument("--output", required=True, help="Path to write the final markdown file (e.g., compressed_context.md)")
    args = parser.parse_args()

    master_path = os.path.join(args.state_dir, "master_compressed_context.json")

    if not os.path.exists(master_path):
        print(f"Error: {master_path} not found.")
        return

    with open(master_path, "r", encoding="utf-8") as f:
        master_context = json.load(f)

    if not master_context:
        print("Warning: Master context is empty. Nothing to stitch.")
        return

    # Extract clean paths and sort them deterministically
    sorted_files = sorted(master_context.items(), key=lambda x: x[0])
    
    # Generate Tree paths (stripping 'file:' prefix)
    clean_paths = [
        key.replace("file:", "", 1) 
        for key in master_context.keys() 
        if key.startswith("file:")
    ]
    tree_markdown = render_ascii_tree(clean_paths)

    print(f"Stitching {len(sorted_files)} compressed files...")

    # Ensure output directory exists
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)

    with open(args.output, "w", encoding="utf-8") as out:
        # 1. Header
        out.write("# Codebase Architectural Context\n\n")
        out.write("> *This document contains high-resolution structural maps of the codebase, compressed to exclude implementation logic.*\n\n")
        
        # 2. Directory Tree
        out.write("## Directory Tree\n\n")
        out.write("```text\n")
        out.write(tree_markdown + "\n")
        out.write("```\n\n")
        out.write("---\n\n")
        
        # 3. File Summaries
        for stable_id, compressed_text in sorted_files:
            out.write(f"{compressed_text}\n\n---\n\n")

    file_size_kb = os.path.getsize(args.output) / 1024
    print(f"Success! Wrote {args.output} ({file_size_kb:.1f} KB)")


if __name__ == "__main__":
    main()

    # test