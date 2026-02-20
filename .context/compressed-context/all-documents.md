# Quick Export: repo-runner

- repo_root: `C:/projects/repo-runner`
- snapshot_id: `QUICK_EXPORT_PREVIEW`
- file_count: `12`
- tree_only: `False`
## Tree

```
├── documents
│   ├── architecture.md
│   ├── config_spec.md
│   ├── contributing.md
│   ├── determinism_rules.md
│   ├── id_spec.md
│   ├── language_support.md
│   ├── repo_layout.md
│   ├── roadmap.md
│   ├── snapshot_spec.md
│   ├── testing_strategy.md
│   └── versioning_policy.md
└── readme.md
```

## File Contents

### `documents/architecture.md`

```
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

## v0.1 — Structure + Fingerprints (Current)

- structure.json (repo/module/file containment)
- manifest.json (config + file hashes)
- append-only snapshots
- optional exports (flatten.md)

## v0.2 — Dependency Extraction (Imports Only)

- symbols.json (definitions optional)
- imports.json (file-to-file/module import edges)
- external_deps.json (package usage)
- stable external IDs

## v0.3 — Graph Canonicalization

- graph.json as the canonical structure:
  - nodes: repo/module/file/external
  - edges: contains/imports/depends_on
- cycle handling policy

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

### `readme.md`

```
# repo-runner

Deterministic repository structure compiler.

repo-runner scans a repository, produces an immutable structural snapshot, and exports derived context artifacts (such as a flattened markdown tree) for downstream systems like Dennis.

It is not an LLM tool.
It is a structural substrate generator.

---

## Design Goals

* Deterministic outputs
* Stable IDs
* Append-only snapshots
* Canonical structure first, exports second
* No semantic interpretation
* No mutation of past snapshots

repo-runner is built to be a foundational layer in a larger AI ecosystem, but remains completely standalone.

---

## Core Concepts

### 1. Snapshot-First Architecture

Every operation begins with a snapshot.

```
Filesystem
  → snapshot
    → manifest.json
    → structure.json
    → exports/
```

Snapshots are immutable.
The `current.json` pointer references the latest snapshot.

Exports are derived projections of a snapshot — never of the live filesystem.

---

### 2. Determinism

Given:

* the same repository state
* the same configuration
* the same repo-runner version

You will get:

* identical manifest.json
* identical structure.json
* identical flatten exports (byte-for-byte)

repo-runner does not rely on:

* timestamps inside exports
* random IDs
* UUIDs
* unordered traversal

All ordering is lexicographically deterministic.

---

### 3. Stable IDs

Files use canonical normalized paths:

```
file:src/app/page.tsx
module:src/app
repo:root
```

Path normalization:

* repo-relative
* forward slashes
* preserves leading dots (e.g., `.context-docs`)
* lowercase normalized IDs
* collision detection enforced

Stable IDs never use random values.

---

## Commands

### Create a Snapshot

```powershell
python -m src.cli.main snapshot C:\projects\caffeine-melts-website `
  --output-root C:\repo-runner-output `
  --depth 10 `
  --ignore node_modules .expo .git __pycache__ dist build .next
```

Produces:

```
C:\repo-runner-output\
  2026-02-18T06-16-09Z\
    manifest.json
    structure.json
    exports\
  current.json
```

`current.json` is automatically updated unless disabled.

---

### Export Flatten (list_tree replacement)

Export from the current snapshot:

```powershell
python -m src.cli.main export flatten `
  --output-root C:\repo-runner-output `
  --repo-root C:\projects\caffeine-melts-website
```

Writes:

```
<snapshot>\exports\flatten.md
```

This replaces manual `list_tree.py` workflows.

---

### Export Tree Only

```powershell
python -m src.cli.main export flatten `
  --output-root C:\repo-runner-output `
  --repo-root C:\projects\caffeine-melts-website `
  --tree-only
```

Equivalent to your old `--tree-only` usage.

---

### Export From a Specific Snapshot

```powershell
python -m src.cli.main export flatten `
  --output-root C:\repo-runner-output `
  --repo-root C:\projects\caffeine-melts-website `
  --snapshot-id 2026-02-18T06-16-09Z
```

If `--snapshot-id` is not provided, repo-runner defaults to `current.json`.

---

## Flatten Export Behavior

The flatten exporter:

* uses the canonical file set from `manifest.json`
* renders a deterministic tree
* optionally concatenates file contents
* skips binary files by default
* emits stable placeholders for binary files:

```
<<BINARY_OR_SKIPPED_FILE>>
language: unknown
size_bytes: 182343
sha256: ...
```

No binary garbage is ever inlined.

---

## Snapshot Contents

### manifest.json

Contains:

* schema_version
* tool metadata
* inputs
* config
* stats
* canonical file list (with sha256, size, language)
* snapshot metadata

### structure.json

Contains:

* schema_version
* repository node
* modules
* file containment

structure.json is structural only — no imports, no semantics.

---

## What repo-runner Is Not

* Not an LLM summarizer
* Not a semantic analyzer (yet)
* Not a code modifier
* Not a refactoring engine
* Not tied to Dennis

repo-runner produces deterministic structure.
Dennis consumes it.

---

## Architecture Overview

```
scanner/
normalize/
fingerprint/
structure/
snapshot/
exporters/
cli/
```

Flow:

```
filesystem
  → scanner
    → normalizer
      → fingerprint
        → structure builder
          → snapshot writer
            → exporter
```

Exports are projections of snapshot state.

---

## Determinism Rules

* Files sorted lexicographically
* Modules sorted lexicographically
* No random UUIDs
* No nondeterministic traversal
* No implicit filesystem rescans during export
* Exporters consume manifest, not filesystem discovery

---

## Versioning

repo-runner follows semantic versioning:

MAJOR.MINOR.PATCH

Breaking changes include:

* stable ID format changes
* path normalization changes
* snapshot schema changes
* manifest/structure schema changes

Backward-compatible additions increment MINOR.

---

## Why This Exists

repo-runner exists to create a clean, stable structural substrate for:

* context assembly
* dependency graph generation
* change impact analysis
* semantic layering
* AI orchestration

But v0.1 intentionally does only structure and flatten export.

Graph generation is planned for a future version.

---

## Roadmap (High-Level)

v0.1

* deterministic snapshot
* flatten exporter

v0.2

* import graph
* external dependency edges
* graph.json

v0.3

* draw.io exporter
* subgraph exports
* scoped context export

---

## Development Philosophy

* Deterministic first
* Structure before semantics
* Append-only snapshots
* Explicit contracts
* No hidden magic

repo-runner is infrastructure.

---

If you want, next we can:

* write a minimal CONTRIBUTING.md aligned to this readme
* or implement `--scope module:` support to eliminate your manual PowerShell zoo entirely
* or move into graph layer design cleanly without contaminating determinism

You’ve got a real substrate now.
```
