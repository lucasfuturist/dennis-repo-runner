# ARCHITECTURE.md

# Architecture (v0.1)

Repo-runner is a deterministic pipeline with strict phase boundaries. In v0.1, the output is purely structural (containment and file fingerprints).

## Pipeline Overview

Inputs:
- Root path(s)
- Config (depth, ignore, extensions, include_readme, tree_only, output root, etc.)

Phases:
1. Scan
2. Normalize
3. Fingerprint
4. Build Structure
5. Write Snapshot
6. Optional Exports

Outputs:
- `manifest.json`
- `structure.json`
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
- Record language detection (extension-based in v0.1)

Constraints:
- Hash is over file bytes only (no newline normalization)

### 4) Structure Builder
Responsibility:
- Build hierarchical containment:
  - repo root
  - modules (directories)
  - files (leaf nodes)
- Sort modules and files deterministically

### 5) Snapshot Writer
Responsibility:
- Create append-only snapshot folder
- Write `manifest.json` and `structure.json`
- Optionally write `current.json` pointer

Constraints:
- Snapshot folder is immutable once written

### 6) Exporters (Optional)
Responsibility:
- Produce auxiliary human-readable exports (e.g., flatten.md)
- Exporters must not change canonical snapshot data
- Exporters must read from the same scanned set to remain consistent

Example Exporter:
- FlattenMarkdownExporter
  - Produces a deterministic flattened tree and optional file bodies.
  - Intended for context assembly (e.g., Dennis).
  - Must not influence manifest.json or structure.json.

## Data Flow Rules

- No component may “reach backward” and mutate earlier outputs.
- Only the Snapshot Writer touches disk for canonical artifacts.
- Exports are derived and must be safe to delete/regenerate.

## Non-Goals in v0.1

- Graph edges
- Import/export parsing
- Symbol indexing
- Call graph
- Diagram projection

Those are introduced in v0.2+ with separate specs.

