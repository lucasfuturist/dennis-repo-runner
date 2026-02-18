# ID_SPEC.md

# Stable ID Spec (v0.1)

Stable IDs are required for deterministic outputs and future graph layering.

## ID Types (v0.1)

- Repository: repo:root
- Module (directory): module:{path}
- File: file:{path}

Where `{path}` is a normalized repo-relative path.

Examples:
- repo:root
- module:src/modules/catalog
- file:src/modules/catalog/index.ts

## Path Normalization

All paths stored in artifacts must be:

1) Repo-relative
- No drive letters
- No absolute paths
- No leading "./" (use plain relative)

2) Forward slashes
- Always use "/" even on Windows

3) Stable casing
- On Windows: normalize to the actual filesystem casing if available, otherwise lower-case.
- Recommended v0.1 rule: lower-case all paths to avoid case drift.
  (This can be revised later, but must be consistent.)

4) No trailing slashes for modules
- module path: "src/app", not "src/app/"

5) No redundant segments
- Remove "." segments
- Collapse ".." deterministically (or disallow roots that escape repo root)

## Stable ID Generation

Given a normalized path:
- file stable_id: "file:" + path
- module stable_id: "module:" + directory_path
- repo stable_id: "repo:root"

No UUIDs.
No random identifiers.

## Collisions

If two included files normalize to the same path (rare, but possible with case conflicts on Windows):
- Repo-runner must detect the collision and fail the run with an explicit error.
- No silent overwrites.

## Future Types (Reserved)

These are not used in v0.1, but reserved for later:
- symbol:{file_path}#{symbol_name}
- external:{package_name}
- edge IDs derived from endpoint IDs