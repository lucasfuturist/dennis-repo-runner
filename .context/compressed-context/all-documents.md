# Quick Export: repo-runner

- repo_root: `C:/projects/repo-runner`
- snapshot_id: `QUICK_EXPORT_PREVIEW`
- file_count: `11`
- tree_only: `False`
## Tree

```
└── documents
    ├── architecture.md
    ├── config_spec.md
    ├── contributing.md
    ├── determinism_rules.md
    ├── id_spec.md
    ├── language_support.md
    ├── repo_layout.md
    ├── roadmap.md
    ├── snapshot_spec.md
    ├── testing_strategy.md
    └── versioning_policy.md
```

## File Contents

### `documents/architecture.md`

```
# ARCHITECTURE.md

# Architecture (v0.1.5)

Repo-runner is a deterministic pipeline with strict phase boundaries. In v0.1.5, the output includes structural containment, file fingerprints, and preliminary dependency graph construction.

## Pipeline Overview

Inputs:
- Root path(s)
- Config (depth, ignore, extensions, include_readme, tree_only, output root, etc.)

Phases:
1. Scan
2. Normalize
3. Fingerprint
4. Analysis & Graph Construction
5. Build Structure
6. Write Snapshot
7. Optional Exports

Outputs:
- `manifest.json`
- `structure.json`
- `graph.json` (Preliminary)
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

### 4) Analysis & Graph Construction
Responsibility:
- Parse file content (AST for Python, Regex for TS/JS)
- Extract import statements and dependency edges
- Construct a directed graph (`GraphStructure`)
- Resolve internal modules vs. external packages

Constraints:
- Analysis must handle syntax errors gracefully (skip file or log warning)
- Must be deterministic (sort imports before hashing/linking)
- Graph construction must not mutate file fingerprints

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
- Write `manifest.json` and `structure.json`
- Optionally write `current.json` pointer

Constraints:
- Snapshot folder is immutable once written

### 7) Exporters (Optional)
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

## Non-Goals in v0.1.5

- Symbol indexing
- Call graph resolution (function-to-function)
- Diagram projection

Those are introduced in v0.2+ with separate specs.
```

### `documents/config_spec.md`

```
# CONFIG_SPEC.md

# Config Spec (v0.1)

Repo-runner accepts configuration via CLI flags. A config file may be introduced later, but v0.1 defines CLI as canonical.

## Required Config Inputs

- One or more root paths (positional args)
- Output root directory

## Core Options

- depth (integer)
  - Maximum directory depth to traverse from each root
  - depth=0 means treat roots as explicit files/directories only (no recursion)

- ignore_names (list of directory/file names)
  - Name-based ignore (not glob)
  - Applies to directory names during traversal, and to file base names if desired
  - Example: node_modules, .git, dist, build, .next

- include_extensions (list of extensions)
  - Only include files whose extension is in this list
  - Extensions must include the dot (e.g., ".ts")

- include_readme (boolean)
  - If true: include README files even if extension filtering would exclude them
  - README detection: README, README.md, README.txt (case-insensitive)

- tree_only (boolean)
  - v0.1 affects exporters only
  - structure.json + manifest.json are unaffected by tree_only
  - tree_only may skip reading file bodies for exports

## Output Options

- output_root (path)
  - Root directory to place snapshots
  - Example: C:\repo-runner-output

- write_current_pointer (boolean)
  - If true, write/update current.json

## Precedence Rules

In v0.1:
- CLI flags are the only config source.
- Defaults apply when flags are omitted.

## Defaults (Recommended)

- depth: 25
- ignore_names: [".git", "node_modules", "__pycache__", "dist", "build", ".next", ".expo", ".venv"]
- include_extensions: common code + config (user-defined)
- include_readme: true
- tree_only: false
- write_current_pointer: true
```

### `documents/contributing.md`

```
# CONTRIBUTING.md

# Contributing (Solo Discipline)

This project is primarily for internal use, but it follows strict engineering hygiene to protect determinism and compatibility.

## Rules

1) Specs First
- Any change to snapshot formats, ID rules, or determinism rules must update the relevant spec document first.

2) Breaking Changes Require Version Bumps
- Output schema changes require VERSIONING_POLICY compliance.

3) No “Convenient” Non-Determinism
- No random IDs
- No reliance on unordered maps/sets
- No OS-specific ordering assumptions

4) Append-Only Snapshots
- Never overwrite snapshots
- Only current.json may be updated

## Branching (If Using Git)
- main: stable
- dev: active work
- feature/*: scoped changes

## Commit Hygiene
- One change category per commit where possible:
  - spec update
  - implementation
  - tests

## “Dennis Integration” Boundary
- Repo-runner stays generic and deterministic.
- Dennis-specific logic belongs in Dennis.
```

### `documents/determinism_rules.md`

```
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
```

### `documents/id_spec.md`

```
# ID_SPEC.md

# Stable ID Spec (v0.2)

Stable IDs are required for deterministic outputs and future graph layering.

## ID Types (v0.2)

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
- file stable_id: "file:" + path
- module stable_id: "module:" + directory_path
- repo stable_id: "repo:root"

No UUIDs.
No random identifiers.

## Collisions

If two included files normalize to the same path (e.g., `README.md` and `readme.md` on a case-sensitive filesystem):
- Repo-runner must detect the collision and fail the run with an explicit error.
- No silent overwrites.

## Future Types (Reserved)

These are not used in v0.2, but reserved for later:
- symbol:{file_path}#{symbol_name}
- external:{package_name}
- edge IDs derived from endpoint IDs
```

### `documents/language_support.md`

```
# LANGUAGE_SUPPORT.md

# Language Support (v0.1)

In v0.1, language support is limited to extension-based detection for metadata only.

## Detection Rules

- language is derived from file extension.
- mapping is configured internally or via a simple mapping table.

Example mapping (illustrative):
- .ts, .tsx, .js, .jsx -> "typescript" or "javascript" (choose one policy and keep it consistent)
- .py -> "python"
- .rs -> "rust"
- .go -> "go"
- .java -> "java"
- .html -> "html"
- .css -> "css"
- .sql -> "sql"
- .toml -> "toml"
- .ps1 -> "powershell"
- .md -> "markdown"

## Policy

- Unknown extensions should be labeled "unknown" and may still be included if allowed by include_extensions.
- README inclusion is controlled separately by include_readme.

## Future (v0.2+)

Language adapters (AST parsing, imports, symbols) will be added later and specified in separate documents.
```

### `documents/repo_layout.md`

```
# REPO_LAYOUT.md

# Repository Layout (repo-runner)

This document defines the expected folder structure for the repo-runner repository itself. The goal is to keep specs stable, implementation modular, and outputs reproducible.

## Top-Level Layout

/
  README.md
  ARCHITECTURE.md
  SNAPSHOT_SPEC.md
  ID_SPEC.md
  CONFIG_SPEC.md
  DETERMINISM_RULES.md
  LANGUAGE_SUPPORT.md
  ROADMAP.md
  TESTING_STRATEGY.md
  VERSIONING_POLICY.md
  CONTRIBUTING.md
  REPO_LAYOUT.md

  src/
  tests/
  fixtures/
  scripts/
  dist/                (optional; build output if applicable)
  .gitignore
  LICENSE              (optional)

## Directory Purposes

### src/
Implementation code lives here.

Recommended internal modules (names are suggestions, not mandates):
- src/scanner/
- src/normalize/
- src/fingerprint/
- src/structure/
- src/snapshot/
- src/exporters/
- src/cli/

Rules:
- Keep phase boundaries clean.
- Do not mix exporters with canonical snapshot writing.

### tests/
Automated tests.

Suggested structure:
- tests/unit/
- tests/integration/
- tests/golden/

Golden tests should compare normalized outputs with snapshot_id/timestamp removed or ignored.

### fixtures/
Small, version-controlled fixture repos for testing.

Examples:
- fixtures/tiny_ts_repo/
- fixtures/mixed_repo/
- fixtures/windows_path_edgecases/

Rules:
- Fixtures must be small enough to run in CI quickly.
- Fixtures should include “annoying” cases (nested dirs, ignored dirs, mixed extensions).

### scripts/
Developer utilities and runner scripts.

Examples:
- scripts/run_fixture_tests.ps1
- scripts/run_fixture_tests.sh
- scripts/dev_snapshot.ps1

Rules:
- scripts/ must never be required for core functionality; they are convenience only.

### dist/ (optional)
Build artifacts if using a compiled language or bundler.

Rules:
- dist/ is never committed unless explicitly desired.
- dist/ should be ignored by git by default.

## Output Location Policy

Repo-runner should never write snapshots into its own repository by default.

Instead:
- Default output root should be user-specified, or
- A safe default like: {repo_root}/.repo-runner/ (for scanned repos), not the tool repo.

## Spec Discipline

All canonical contracts are the spec documents at repo root:
- SNAPSHOT_SPEC.md
- ID_SPEC.md
- CONFIG_SPEC.md
- DETERMINISM_RULES.md
- VERSIONING_POLICY.md

Implementation must follow specs. If implementation needs to change behavior, update specs first.

## Dennis Integration Boundary

Repo-runner is a standalone tool. Dennis consumes outputs.

Repo-runner must not:
- depend on Dennis code
- embed Dennis paths
- assume Dennis runtime environment beyond “local filesystem + CLI execution”

Dennis-specific orchestration belongs in Dennis.
```

### `documents/roadmap.md`

```
# ROADMAP.md

# Roadmap

This roadmap is intentionally staged to preserve determinism and keep complexity layered.

## v0.1 — Structure + Fingerprints (Complete)

- [x] structure.json (repo/module/file containment)
- [x] manifest.json (config + file hashes)
- [x] append-only snapshots
- [x] optional exports (flatten.md)

## v0.1.5 — Schema Assurance & Graph Hardening (Immediate Focus)

- [ ] **Migrate `src/core/types.py` to Pydantic**
  - Enforce strict typing for `FileEntry` and `Manifest` at the class level
  - Implement runtime validators for normalized paths (lowercase, forward-slash)
- [ ] **Integration with "Dennis" Context Engine**
  - Verify structured output validation against AllSpice-style requirements

## v0.2 — Dependency Extraction & Graph Layer (In Progress)

- [x] **Basic AST-based import scanning (Python)**
  - `src/analysis/import_scanner.py`
- [x] **Regex-based import scanning (JS/TS)**
  - `src/analysis/import_scanner.py`
- [x] **Initial `GraphStructure` implementation**
  - `src/analysis/graph_builder.py`
- [ ] symbols.json (definitions optional)
- [ ] external_deps.json (package usage)
- [ ] Cycle detection and handling strategy
- [ ] Stable external IDs (e.g., `external:pydantic`)

## v0.3 — Graph Canonicalization

- graph.json as the canonical structure:
  - nodes: repo/module/file/external
  - edges: contains/imports/depends_on
- cycle handling policy
- full determinism audit for graph edges

## v0.4 — Diagram Projection

- draw.io export:
  - diagram.drawio
  - mxgraph.xml
- deterministic layout strategy

## v0.5 — Structural Artifacts

- per-node structural artifacts:
  - file artifact
  - module artifact
  - repo artifact
- still non-semantic, template-based

## v0.6+ — Optional LLM Layer (Dennis-Owned)

- semantic compression as a separate layer
- must not break determinism of structural substrate
```

### `documents/snapshot_spec.md`

```
# SNAPSHOT_SPEC.md

# Snapshot Spec (v0.2)

This document defines the canonical snapshot format and on-disk layout.

## Output Root

Repo-runner writes into an output root directory (configurable). Within it, each run creates a new snapshot folder.

Example:

/repo-runner-output/
  /{snapshot_id}/
    manifest.json
    structure.json
    graph.json
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
    "version": "0.2.0"
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
    "tree_only": true/false,
    "skip_graph": true/false,
    "manual_override": true/false
  },
  "stats": {
    "file_count": number,
    "total_bytes": number,
    "external_dependencies": ["react", "pandas", ...]
  },
  "files": [
    {
      "stable_id": "file:src/app/page.tsx",
      "path": "src/app/page.tsx",
      "sha256": "hex string",
      "size_bytes": number,
      "language": "typescript",
      "imports": ["./layout.tsx", "react"]
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

## graph.json Schema

graph.json provides the topological dependency map.

{
  "schema_version": "1.0",
  "nodes": [
    {
      "id": "file:src/app/page.tsx",
      "type": "file"
    },
    {
      "id": "external:react",
      "type": "external"
    }
  ],
  "edges": [
    {
      "source": "file:src/app/page.tsx",
      "target": "external:react",
      "relation": "imports"
    }
  ]
}

Rules:
- `nodes` array must be sorted ascending by `id`.
- `edges` array must be sorted ascending by `source`, then `target`, then `relation`.
- `external:` nodes represent inferred external boundaries (e.g., npm packages, python site-packages).

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

## Snapshot Resolution Policy

When invoked without explicit snapshot_id:
- Repo-runner or its consumer may default to current.json pointer.

If snapshot_id is provided:
- The specified snapshot folder must exist.
- If not found, fail explicitly.

Snapshot resolution does not mutate snapshots.
```

### `documents/testing_strategy.md`

```
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
```

### `documents/versioning_policy.md`

```
# VERSIONING_POLICY.md

# Versioning Policy

Repo-runner uses semantic versioning: MAJOR.MINOR.PATCH.

Because Dennis will consume repo-runner outputs, output compatibility matters.

## MAJOR Version Bump (Breaking)

Any of the following requires a MAJOR bump:
- Changes to stable ID formats
- Changes to path normalization policy
- Changes to snapshot folder contract
- Changes to manifest.json or structure.json schema that are not backward compatible
- Removal/renaming of required fields

## MINOR Version Bump (Backward-Compatible Additions)

Any of the following requires a MINOR bump:
- Adding new optional fields to manifest/structure
- Adding new exporters
- Adding new CLI flags that do not change defaults
- Adding new language detection mappings (if it doesn’t alter existing labels)

## PATCH Version Bump (Fixes Only)

Any of the following requires a PATCH bump:
- Bug fixes that restore intended determinism
- Documentation corrections
- Performance improvements that do not change outputs

## Schema Versioning

Both manifest.json and structure.json include `schema_version`.
- If schema changes in a backward-compatible way: increment MINOR in schema_version (e.g., 1.1)
- If schema changes incompatibly: increment MAJOR in schema_version (e.g., 2.0)

Tool version and schema_version are related but distinct.
```

---
## Context Stats
- **Total Characters:** 22,182
- **Estimated Tokens:** ~5,545 (assuming ~4 chars/token)
- **Model Fit:** GPT-4 (8k)
