# ARCHITECTURE.md

# Architecture (v0.2)

Repo-runner is a deterministic pipeline with strict phase boundaries. Output includes containment structure, file fingerprints, and a dependency graph.

## Pipeline Overview

Inputs:
- Root path(s)
- Config (depth, ignore, extensions, include_readme, skip_graph, output root, etc.)

Phases:
1. Scan
2. Normalize
3. Fingerprint
4. Analysis (Graph Construction)
5. Build Structure
6. Write Snapshot
7. Optional Exports

Outputs:
- `manifest.json`
- `structure.json`
- `graph.json` (optional)
- Optional export files under `exports/`

## Components

### 1) Scanner
Responsibility:
- Walk filesystem roots
- Apply ignore rules and depth limits
- Collect candidate files and directories
- Produce a raw file list (absolute paths allowed internally)

Constraints:
- Must be deterministic (sorted traversal)
- Must not depend on OS-specific ordering

### 2) Normalizer
Responsibility:
- Convert absolute paths into normalized repo-relative paths
- Enforce path normalization rules (see ID_SPEC)
- Derive module paths (directories) deterministically
- Produce canonical, comparable identifiers and paths

### 3) Fingerprinter
Responsibility:
- Compute SHA256 for each included file
- Record file size in bytes
- Record language detection

### 4) Analysis (Graph Builder)
Responsibility:
- Parse file contents to extract imports (Regex/AST)
- Resolve imports to internal `stable_id` or external packages
- Construct a directed graph of dependencies

Constraints:
- Must tolerate parsing errors (fail safe)
- Must be deterministic in node/edge ordering

### 5) Structure Builder
Responsibility:
- Build hierarchical containment:
  - repo root
  - modules (directories)
  - files (leaf nodes)
- Sort modules and files deterministically

### 6) Snapshot Writer
Responsibility:
- Create append-only snapshot folder
- Write `manifest.json`, `structure.json`, and `graph.json`
- Optionally write `current.json` pointer

Constraints:
- Snapshot folder is immutable once written

### 7) Exporters (Optional)
Responsibility:
- Produce auxiliary human-readable exports (e.g., flatten.md)
- Exporters must not change canonical snapshot data
- Exporters must read from the same scanned set to remain consistent

## Data Flow Rules

- No component may “reach backward” and mutate earlier outputs.
- Only the Snapshot Writer touches disk for canonical artifacts.
- Exports are derived and must be safe to delete/regenerate.

## Non-Goals in v0.2

- Symbol indexing (definitions/references within files)
- Call graph (function-level edges)
- Diagram projection (Draw.io/Mermaid export)

Those are introduced in v0.3+ with separate specs.