# ID_SPEC.md

# Stable ID Spec (v0.2)

Stable IDs are required for deterministic outputs and future graph layering.

## ID Types (v0.2)

- Repository: `repo:root`
- Module (directory): `module:{path}`
- File: `file:{path}`
- External Dependency: `external:{package_name}`
- Symbol (Virtual): `symbol:{name}`

Where `{path}` is a normalized repo-relative path.

Examples:
- `repo:root`
- `module:src/modules/catalog`
- `file:src/modules/catalog/index.ts`
- `external:react`
- `symbol:GraphBuilder`

## Path Normalization

All paths stored in artifacts must be:

1) Repo-relative
- No drive letters
- No absolute paths
- No leading "./" (use plain relative)

2) Forward slashes
- Always use "/" even on Windows

3) Strict Lowercase (v0.2 Rule)
- To prevent "shimmering" IDs across OS environments (e.g., Windows "File.txt" vs Linux "file.txt"), all paths must be lowercased.
- This applies to both file paths and module paths.

4) Security: No Root Escape
- Paths must not contain ".." segments that traverse above the repo root.
- Any file resolving to a path outside the repo root must trigger a hard failure.

5) No redundant segments
- Remove "." segments.
- Root-level files have a directory path of "." (which maps to the repo root container).

## Stable ID Generation

Given a normalized path:
- file stable_id: `"file:" + path`
- module stable_id: `"module:" + directory_path`
- repo stable_id: `"repo:root"`
- external stable_id: `"external:" + package_name`

## Symbol IDs

Symbols are primarily used for Context Slicing queries and logical navigation.
- Format: `symbol:{name}`
- Example: `symbol:ContextSlicer` -> Resolves to `file:src/analysis/context_slicer.py` via `symbols.json`.

## Collisions

If two included files normalize to the same path (e.g., `README.md` and `readme.md` on a case-sensitive filesystem):
- Repo-runner must detect the collision and fail the run with an explicit error.
- No silent overwrites.