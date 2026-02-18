# DETERMINISM_RULES.md

# Determinism Rules (v0.1)

Repo-runner must be deterministic across runs given identical repo content and config.

## Ordering

- Directory traversal must be sorted lexicographically by entry name.
- Included file list must be sorted by normalized repo-relative path.
- Module list must be sorted by module path.
- File lists within modules must be sorted.

## Serialization

- JSON must be emitted deterministically:
  - stable key ordering
  - stable list ordering
  - no non-deterministic map iteration

## Hashing

- SHA256 computed from raw file bytes.
- No newline normalization.
- No trimming.
- If a file cannot be read, fail with explicit error.

## Normalization

- Path normalization must be applied before:
  - sorting
  - ID generation
  - JSON emission

## Allowed Non-Determinism

- snapshot_id
- created_utc timestamp

Everything else must remain stable.

## Failure Is Preferred Over Ambiguity

Repo-runner should fail hard if:
- path collisions occur after normalization
- roots escape repo boundary (if enforced)
- unreadable files in the included set
- output snapshot folder already exists

Exporters must consume the canonical scanned file set.
Exporters must not independently walk the filesystem.