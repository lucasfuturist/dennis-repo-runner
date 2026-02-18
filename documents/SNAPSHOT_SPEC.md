# SNAPSHOT_SPEC.md

# Snapshot Spec (v0.1)

This document defines the canonical snapshot format and on-disk layout.

## Output Root

Repo-runner writes into an output root directory (configurable). Within it, each run creates a new snapshot folder.

Example:

/repo-runner-output/
  /{snapshot_id}/
    manifest.json
    structure.json
    exports/
      ...
  current.json

## Snapshot Mode

Append-only snapshots are required.

- Every run creates a new `{snapshot_id}` folder.
- No run may overwrite an existing snapshot folder.
- `current.json` may be overwritten to point to the latest snapshot.

## snapshot_id Format

snapshot_id must be:
- Unique per run
- Safe as a folder name on Windows/macOS/Linux
- Deterministic *enough* to avoid collisions, but may include timestamp

Recommended format:

YYYY-MM-DDTHH-mm-ssZ_{short_hash}

Where `short_hash` is derived from:
- normalized roots
- config (ignore/ext/depth)
- optional git commit
- optional file list hash (if available after scan)

## manifest.json Schema

manifest.json describes:
- When the snapshot was made
- What inputs and config were used
- What files were included
- How to fingerprint and compare runs

Required fields:

{
  "schema_version": "1.0",
  "tool": {
    "name": "repo-runner",
    "version": "0.1.0"
  },
  "snapshot": {
    "snapshot_id": "...",
    "created_utc": "YYYY-MM-DDTHH:MM:SSZ",
    "output_root": "normalized path string"
  },
  "inputs": {
    "repo_root": "normalized path string",
    "roots": ["normalized path string", ...],
    "git": {
      "is_repo": true/false,
      "commit": "string or null"
    }
  },
  "config": {
    "depth": number,
    "ignore_names": ["node_modules", ".git", ...],
    "include_extensions": [".ts", ".tsx", ...],
    "include_readme": true/false,
    "tree_only": true/false
  },
  "stats": {
    "file_count": number,
    "total_bytes": number
  },
  "files": [
    {
      "stable_id": "file:src/app/page.tsx",
      "path": "src/app/page.tsx",
      "sha256": "hex string",
      "size_bytes": number,
      "language": "typescript"
    }
  ]
}

Rules:
- `files` must be sorted by `path` ascending.
- `sha256` must be computed from file bytes.
- `path` must follow normalization rules in ID_SPEC.md.

## structure.json Schema

structure.json is hierarchical containment only.

{
  "schema_version": "1.0",
  "repo": {
    "stable_id": "repo:root",
    "root": "repo-relative root (usually '.')",
    "modules": [
      {
        "stable_id": "module:src/app",
        "path": "src/app",
        "files": [
          "file:src/app/page.tsx",
          "file:src/app/layout.tsx"
        ]
      }
    ]
  }
}

Rules:
- `modules` sorted by `path` ascending.
- `files` entries sorted by their file path ascending.
- module membership is defined by directory containment of the file path.

## exports/ Folder

`exports/` is optional.

Anything in `exports/`:
- Must be derivable from the canonical snapshot
- Must be safe to delete and regenerate
- Must not be used as a source of truth

## current.json

Optional pointer for convenience:

{
  "schema_version": "1.0",
  "current_snapshot_id": "{snapshot_id}",
  "path": "{snapshot_id}"
}

Overwriting current.json is allowed.