# TESTING_STRATEGY.md

# Testing Strategy (v0.1)

Repo-runner must prove determinism and correctness under realistic repo conditions.

## Test Categories

### 1) Golden Snapshot Tests
- Run repo-runner on a small fixture repo.
- Store expected `structure.json` and `manifest.json` (excluding snapshot_id and timestamp).
- Compare normalized outputs.

### 2) Determinism Re-run Tests
- Run twice on the same fixture with identical config.
- Assert:
  - file list is identical
  - module grouping identical
  - sha256 hashes identical
  - ordering identical

### 3) Drift Detection Tests
- Modify one file byte.
- Assert only that file’s sha256 changes, and totals adjust accordingly.

### 4) Ignore Rule Tests
- Ensure ignored directories are never traversed.
- Ensure ignore list is name-based and deterministic.

### 5) Path Normalization Tests
- Windows-style input paths normalize to repo-relative forward slash format.
- Case normalization policy is enforced consistently.

### 6) Collision Tests
- Simulate two inputs that normalize to the same path.
- Assert hard failure.

## Performance Smoke Test (Non-Blocking v0.1)
- Run on a medium repo (tens of thousands of files).
- Confirm completion and stable output.
- No optimization requirements yet.

## CI Recommendation
- Run fixture tests on:
  - Windows
  - Linux
to catch path normalization and separator issues early.