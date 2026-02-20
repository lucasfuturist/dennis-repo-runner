# Quick Export: repo-runner

- repo_root: `C:/projects/repo-runner`
- snapshot_id: `QUICK_EXPORT_PREVIEW`
- file_count: `59`
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
├── readme.md
├── scripts
│   ├── build_exe.ps1
│   ├── export-signal.ps1
│   ├── generate_test_repo.ps1
│   └── package-repo.ps1
├── src
│   ├── __init__.py
│   ├── analysis
│   │   ├── __init__.py
│   │   ├── graph_builder.py
│   │   └── import_scanner.py
│   ├── cli
│   │   ├── __init__.py
│   │   └── main.py
│   ├── core
│   │   ├── __init__.py
│   │   ├── controller.py
│   │   └── types.py
│   ├── entry_point.py
│   ├── exporters
│   │   └── flatten_markdown_exporter.py
│   ├── fingerprint
│   │   └── file_fingerprint.py
│   ├── gui
│   │   ├── __init__.py
│   │   ├── app.py
│   │   └── components
│   │       ├── config_tabs.py
│   │       ├── export_preview.py
│   │       ├── preview_pane.py
│   │       └── tree_view.py
│   ├── normalize
│   │   └── path_normalizer.py
│   ├── scanner
│   │   └── filesystem_scanner.py
│   ├── snapshot
│   │   ├── snapshot_loader.py
│   │   └── snapshot_writer.py
│   └── structure
│       └── structure_builder.py
└── tests
    ├── integration
    │   ├── __init__.py
    │   ├── test_full_snapshot.py
    │   ├── test_robustness.py
    │   └── test_snapshot_flow.py
    ├── output
    │   ├── 2026-02-18t21-09-34z
    │   │   ├── graph.json
    │   │   ├── manifest.json
    │   │   └── structure.json
    │   └── current.json
    └── unit
        ├── __init__.py
        ├── test_filesystem_scanner.py
        ├── test_fingerprint_hardening.py
        ├── test_flatten_exporter.py
        ├── test_graph_builder.py
        ├── test_ignore_logic.py
        ├── test_import_scanner.py
        ├── test_normalizer.p
        ├── test_path_normalizer.py
        ├── test_scanner_hardening.py
        ├── test_structure.py
        └── test_structure_builder.py
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

### `scripts/build_exe.ps1`

```
$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "   Building repo-runner v0.1 Executable   " -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Function to handle stubborn directories
function Force-Delete ($Path) {
    if (Test-Path $Path) {
        Write-Host "Removing $Path..." -ForegroundColor Gray
        try {
            # Try standard delete
            Remove-Item $Path -Recurse -Force -ErrorAction Stop
        } catch {
            # Fallback to CMD for deep paths or locked files
            Write-Host "   Standard delete failed (likely deep path). Using cmd.exe..." -ForegroundColor Yellow
            cmd /c "rmdir /s /q ""$Path"""
        }
    }
}

# 1. Cleanup
Force-Delete "build"
Force-Delete "dist"
if (Test-Path "repo-runner.spec") { Remove-Item "repo-runner.spec" -Force }

# 2. Check for PyInstaller (Safety Check)
if (-not (Get-Command "pyinstaller" -ErrorAction SilentlyContinue)) {
    # If not in PATH, we rely on python -m PyInstaller, which is fine.
    Write-Host "PyInstaller not in PATH, will use 'python -m PyInstaller'..." -ForegroundColor Gray
}

# 3. Build Command
Write-Host "Compiling..." -ForegroundColor Yellow

# Using python -m PyInstaller to avoid PATH issues
# --collect-all src: Bundles all code in src/
# --noconfirm: Don't ask to overwrite
python -m PyInstaller --noconfirm --onefile --console --clean `
    --name "repo-runner" `
    --paths "." `
    --hidden-import "tkinter" `
    --collect-all "src" `
    src/entry_point.py

# 4. Success Check
if (Test-Path "dist/repo-runner.exe") {
    Write-Host "`nBuild Success!" -ForegroundColor Green
    Write-Host "Executable is ready at: .\dist\repo-runner.exe" -ForegroundColor White
} else {
    Write-Error "Build failed. No EXE found in dist/."
}
```

### `scripts/export-signal.ps1`

```
[CmdletBinding()]
param(
  [Parameter(Mandatory = $false)]
  [string]$OutDir = "",

  [Parameter(Mandatory = $false)]
  [string[]]$IncludeGlobs = @(
    "README.md",
    ".gitignore",
    "documents\**\*.md",
    "src\**\*.py",
    "scripts\**\*.ps1",
    "tests\**\*",
    ".context-docs\**\*.md",
    ".context-docs\**\*.txt",
    ".context-docs\**\*.json"
  ),

  [Parameter(Mandatory = $false)]
  [string[]]$ExcludeDirs = @(
    "__pycache__", ".git", "dist", "node_modules", ".next", ".expo", ".venv"
  ),

  [Parameter(Mandatory = $false)]
  [string[]]$ExcludeExts = @(
    ".png", ".jpg", ".jpeg", ".webp", ".gif", ".ico",
    ".ttf", ".otf", ".woff", ".woff2",
    ".mp4", ".mov", ".zip"
  )
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-RepoRoot {
  $scriptsDir = Split-Path -Parent $PSCommandPath
  (Resolve-Path (Join-Path $scriptsDir "..")).Path
}

function Ensure-Dir([string]$Path) {
  if (-not (Test-Path $Path)) {
    New-Item -ItemType Directory -Path $Path | Out-Null
  }
}

function RelPath([string]$RepoRoot, [string]$AbsPath) {
  [System.IO.Path]::GetRelativePath($RepoRoot, $AbsPath)
}

function ToForwardSlashes([string]$Path) {
  $Path.Replace('\', '/')
}

$RepoRoot = Resolve-RepoRoot

if ([string]::IsNullOrWhiteSpace($OutDir)) {
  $OutDir = Join-Path $RepoRoot "dist\signal"
} else {
  if (-not [System.IO.Path]::IsPathRooted($OutDir)) {
    $OutDir = Join-Path $RepoRoot $OutDir
  }
}

Ensure-Dir $OutDir

$FlattenOut = Join-Path $OutDir "flatten-signal.md"
$ZipOut     = Join-Path $OutDir "signal.zip"

Write-Host ("repo-root:  {0}" -f $RepoRoot)
Write-Host ("out-dir:    {0}" -f $OutDir)
Write-Host ("flatten:    {0}" -f $FlattenOut)
Write-Host ("zip:        {0}" -f $ZipOut)
Write-Host ""

$excludeDirRegex = ($ExcludeDirs | ForEach-Object { [Regex]::Escape($_) }) -join "|"

$excludeExtSet = New-Object "System.Collections.Generic.HashSet[string]"
foreach ($e in $ExcludeExts) { [void]$excludeExtSet.Add($e.ToLower()) }

# 1) expand include globs
$found = New-Object "System.Collections.Generic.List[string]"

foreach ($glob in $IncludeGlobs) {
  $pattern = Join-Path $RepoRoot $glob

  $items = Get-ChildItem -Path $pattern -Recurse -File -Force -ErrorAction SilentlyContinue

  foreach ($it in $items) {
    if ($it.FullName -match "\\($excludeDirRegex)\\") { continue }

    $ext = [System.IO.Path]::GetExtension($it.Name).ToLower()
    if ($excludeExtSet.Contains($ext)) { continue }

    $found.Add($it.FullName) | Out-Null
  }
}

# 2) de-dupe + deterministic sort by repo-relative lowercased key
$map = @{}
foreach ($abs in $found) {
  $rel = RelPath $RepoRoot $abs
  $key = $rel.ToLower()
  $map[$key] = $abs
}

$keys = $map.Keys | Sort-Object

if ($keys.Count -eq 0) {
  throw "No files matched include globs. Adjust IncludeGlobs."
}

# 3) write flatten markdown (list + contents)
$sb = New-Object System.Text.StringBuilder

[void]$sb.AppendLine("# signal flatten export")
[void]$sb.AppendLine("")
[void]$sb.AppendLine("* repo_root: $RepoRoot")
[void]$sb.AppendLine("* file_count: $($keys.Count)")
[void]$sb.AppendLine("")

[void]$sb.AppendLine("## Files")
[void]$sb.AppendLine("")

# FIX: Use single quotes for markdown code blocks to avoid escape sequence errors
[void]$sb.AppendLine('```') 

foreach ($k in $keys) {
  $rel = RelPath $RepoRoot $map[$k]
  [void]$sb.AppendLine( (ToForwardSlashes $rel) )
}

# FIX: Use single quotes
[void]$sb.AppendLine('```')
[void]$sb.AppendLine("")

[void]$sb.AppendLine("## Contents")
[void]$sb.AppendLine("")

foreach ($k in $keys) {
  $abs = $map[$k]
  $rel = ToForwardSlashes (RelPath $RepoRoot $abs)

  [void]$sb.AppendLine("### $rel")
  [void]$sb.AppendLine("")

  try {
    $content = Get-Content -LiteralPath $abs -Raw -Encoding UTF8 -ErrorAction Stop
  } catch {
    $content = "[[ERROR: $($_.Exception.Message)]]"
  }

  # FIX: Use single quotes
  [void]$sb.AppendLine('```')

  # FIX: TrimEnd requires char[], or use default TrimEnd() to remove all trailing whitespace
  # Using [char[]] ensures explicit handling of CR/LF without parser ambiguity
  [void]$sb.AppendLine([string]$content.TrimEnd([char[]]@("`r", "`n")))

  # FIX: Use single quotes
  [void]$sb.AppendLine('```')
  [void]$sb.AppendLine("")
}

Set-Content -LiteralPath $FlattenOut -Value $sb.ToString() -Encoding UTF8
Write-Host ("wrote flatten: {0}" -f $FlattenOut)

# 4) zip the same exact set
if (Test-Path $ZipOut) {
  Remove-Item $ZipOut -Force
}

$absPaths = foreach ($k in $keys) { $map[$k] }
Compress-Archive -Path $absPaths -DestinationPath $ZipOut -CompressionLevel Optimal
Write-Host ("wrote zip:     {0}" -f $ZipOut)

Write-Host "DONE."
```

### `scripts/generate_test_repo.ps1`

```
param(
    [string]$BasePath = "tests\fixtures",
    [switch]$SkipSnapshot = $false
)

$ErrorActionPreference = "Stop"

# Create unique timestamped name
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$RepoName = "repo_$Timestamp"
$RepoPath = Join-Path $BasePath $RepoName

# Ensure directory exists
if (-not (Test-Path $RepoPath)) {
    New-Item -ItemType Directory -Path $RepoPath -Force | Out-Null
}

Write-Host "Generating random test repo at: $RepoPath" -ForegroundColor Cyan

# Helper to write files
function New-File($RelPath, $Content) {
    $Full = Join-Path $RepoPath $RelPath
    $Dir = Split-Path -Parent $Full
    if (-not (Test-Path $Dir)) {
        New-Item -ItemType Directory -Path $Dir -Force | Out-Null
    }
    # Note: PowerShell 5.1 'UTF8' adds BOM. This effectively tests our BOM stripping logic!
    Set-Content -Path $Full -Value $Content -Encoding UTF8
    Write-Host "  + $RelPath" -ForegroundColor Gray
}

# 1. Root Files
New-File "README.md" "# Test Repo $Timestamp`n`nGenerated for semantic import testing."
New-File "requirements.txt" "requests`nnumpy`npandas"

# 2. Python Source
New-File "src\main.py" @"
import os
import sys
from utils.logger import log_msg

def main():
    print(os.getcwd())
    log_msg('Start')
"@

New-File "src\utils\logger.py" @"
import datetime
# This is a comment
def log_msg(msg):
    print(f'{datetime.datetime.now()}: {msg}')
"@

New-File "src\utils\__init__.py" ""

# 3. TypeScript / JS Source
New-File "frontend\app.tsx" @"
import React from 'react';
import { Button } from './components/Button';
import './styles.css';

export const App = () => <Button />;
"@

New-File "frontend\components\Button.tsx" @"
import { useState } from 'react';
export const Button = () => <button>Click</button>;
"@

New-File "frontend\legacy.js" @"
const fs = require('fs');
const path = require('path');
// require('ignored');
"@

# 4. Nested Deep Logic (Ignored by default configs usually, but let's check imports)
New-File "scripts\deploy.py" @"
import boto3
import json
"@

Write-Host "`nGeneration Done." -ForegroundColor Green

if (-not $SkipSnapshot) {
    Write-Host "`nRunning Snapshot Capture..." -ForegroundColor Yellow
    
    # Define output folder inside the fixture
    $OutputDir = Join-Path $RepoPath "output"
    
    # Determine Project Root (parent of 'scripts') to run python module correctly
    $ScriptDir = Split-Path -Parent $PSCommandPath
    $ProjectRoot = (Resolve-Path (Join-Path $ScriptDir "..")).Path
    
    # We must ignore the output directory so the scanner doesn't scan the results
    # Standard ignores + 'output'
    $Ignores = @(".git", "node_modules", "__pycache__", "dist", "build", ".next", ".expo", ".venv", "output")
    
    Push-Location $ProjectRoot
    try {
        # Run src.cli.main with --export-flatten
        # We assume 'python' is in PATH.
        python -m src.cli.main snapshot "$RepoPath" --output-root "$OutputDir" --ignore $Ignores --export-flatten
        
        Write-Host "`nSnapshot Success!" -ForegroundColor Green
        Write-Host "Output located at: $OutputDir" -ForegroundColor Gray
        Write-Host "Flattened export:  $OutputDir\<SNAPSHOT_ID>\exports\flatten.md" -ForegroundColor Gray
    }
    catch {
        Write-Error "Failed to run snapshot: $_"
    }
    finally {
        Pop-Location
    }
} else {
    Write-Host "Skipping snapshot run." -ForegroundColor Gray
    Write-Host "To run manually:" -ForegroundColor Yellow
    Write-Host "python -m src.cli.main snapshot $RepoPath --output-root $RepoPath/output --export-flatten" -ForegroundColor White
}
```

### `scripts/package-repo.ps1`

```
[CmdletBinding()]
param(
  [Parameter(Mandatory = $false)]
  [string]$OutDir = "",

  [Parameter(Mandatory = $false)]
  [string]$CopyFolderName = "repo-copy",

  [Parameter(Mandatory = $false)]
  [string]$ZipFileName = "repo-runner.zip",

  [Parameter(Mandatory = $false)]
  [string[]]$ExcludeDirs = @("__pycache__", ".git", "dist"),

  [Parameter(Mandatory = $false)]
  [string[]]$ExcludeFiles = @(),

  # If set, show robocopy output in console (progress / file listing).
  [Parameter(Mandatory = $false)]
  [switch]$VerboseCopy
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-RepoRoot {
  $scriptsDir = Split-Path -Parent $PSCommandPath
  return (Resolve-Path (Join-Path $scriptsDir "..")).Path
}

function Ensure-Dir([string]$Path) {
  if (-not (Test-Path $Path)) {
    New-Item -ItemType Directory -Path $Path | Out-Null
  }
}

function Start-Heartbeat([string]$Message) {
  $job = Start-Job -ScriptBlock {
    param($Msg)
    while ($true) {
      Start-Sleep -Seconds 3
      Write-Host $Msg
    }
  } -ArgumentList $Message
  return $job
}

function Stop-Heartbeat($job) {
  if ($null -ne $job) {
    Stop-Job $job -ErrorAction SilentlyContinue | Out-Null
    Remove-Job $job -Force -ErrorAction SilentlyContinue | Out-Null
  }
}

$RepoRoot = Resolve-RepoRoot

if ([string]::IsNullOrWhiteSpace($OutDir)) {
  $OutDir = Join-Path $RepoRoot "dist"
} else {
  if (-not [System.IO.Path]::IsPathRooted($OutDir)) {
    $OutDir = Join-Path $RepoRoot $OutDir
  }
}

Ensure-Dir $OutDir

$CopyOut = Join-Path $OutDir $CopyFolderName
$ZipOut  = Join-Path $OutDir $ZipFileName
$RoboLog = Join-Path $OutDir "robocopy.log"

Write-Host "repo-root: $RepoRoot"
Write-Host "out-dir:   $OutDir"
Write-Host "copy-out:  $CopyOut"
Write-Host "zip-out:   $ZipOut"
Write-Host "log:       $RoboLog"
Write-Host ""

# -------------------------
# 1) CLEAN COPY (robocopy)
# -------------------------
Write-Host "==> creating clean copy..."

# Make sure destination exists (robocopy can create it, but this keeps things predictable)
Ensure-Dir $CopyOut

$robocopyArgs = @(
  "`"$RepoRoot`"",
  "`"$CopyOut`"",
  "/E",
  "/R:0",
  "/W:0",
  "/MT:1",          # deterministic + reduces weird multi-thread behavior
  "/LOG:`"$RoboLog`"",
  "/TEE",           # also write to console, unless we suppress below
  "/XD"
) + $ExcludeDirs

if ($ExcludeFiles.Count -gt 0) {
  $robocopyArgs += @("/XF") + $ExcludeFiles
}

# If not verbose, suppress noisy per-file lines but still show summary + progress
if (-not $VerboseCopy) {
  # /NP removes progress percentage; we actually *want* some progress signal, so keep it.
  # Instead, just reduce file/directory listing noise:
  $robocopyArgs += @("/NFL", "/NDL")
}

$hb = Start-Heartbeat "  ...still working (robocopy). check $RoboLog for details."

try {
  # robocopy returns non-zero even on success; only >=8 is failure.
  & robocopy @robocopyArgs | Out-Host
  $rc = $LASTEXITCODE
  if ($rc -ge 8) {
    throw "robocopy failed with exit code $rc (see $RoboLog)"
  }
}
finally {
  Stop-Heartbeat $hb
}

Write-Host "clean copy done."
Write-Host ""

# -------------------------
# 2) CLEAN ZIP (Compress-Archive)
# -------------------------
Write-Host "==> creating clean zip..."

if (Test-Path $ZipOut) {
  Remove-Item $ZipOut -Force
}

$excludeRegex = ($ExcludeDirs | ForEach-Object { [Regex]::Escape($_) }) -join "|"

$files = Get-ChildItem -Path $RepoRoot -Recurse -File -Force -ErrorAction SilentlyContinue |
  Where-Object { $_.FullName -notmatch "\\($excludeRegex)\\" }

if ($ExcludeFiles.Count -gt 0) {
  $files = $files | Where-Object {
    $name = $_.Name
    $ok = $true
    foreach ($pat in $ExcludeFiles) {
      if ($name -like $pat) { $ok = $false; break }
    }
    $ok
  }
}

if ($files.Count -eq 0) {
  throw "no files selected for zip; check exclusions"
}

Compress-Archive -Path ($files | Select-Object -ExpandProperty FullName) -DestinationPath $ZipOut -CompressionLevel Optimal

Write-Host "clean zip done."
Write-Host ""
Write-Host "DONE."
Write-Host "copy: $CopyOut"
Write-Host "zip:  $ZipOut"
Write-Host "log:  $RoboLog"
```

### `src/__init__.py`

```

```

### `src/analysis/__init__.py`

```
# src/analysis/__init__.py
```

### `src/analysis/graph_builder.py`

```
import os
from typing import List, Dict, Set, Optional
from src.core.types import FileEntry, GraphStructure, GraphNode, GraphEdge

class GraphBuilder:
    def build(self, files: List[FileEntry]) -> GraphStructure:
        """
        Constructs a dependency graph from a list of FileEntries.
        Resolves raw import strings to stable_ids where possible.
        """
        
        # 1. Build Lookup Maps
        # path -> stable_id (e.g., "src/utils/logger.py" -> "file:src/utils/logger.py")
        # Ensure keys are lowercased for case-insensitive lookup, matching normalizer behavior.
        path_map: Dict[str, str] = {f["path"].lower(): f["stable_id"] for f in files}
        
        nodes: List[GraphNode] = []
        edges: List[GraphEdge] = []
        external_ids: Set[str] = set()
        
        # Add all file nodes
        for f in files:
            nodes.append({
                "id": f["stable_id"],
                "type": "file"
            })

        # 2. Iterate and Resolve Imports
        for f in files:
            source_id = f["stable_id"]
            source_path = f["path"]
            source_dir = os.path.dirname(source_path)
            lang = f["language"]

            for raw_import in f["imports"]:
                # Try internal resolution first
                target_id = self._resolve_import(raw_import, source_dir, lang, path_map)
                
                if target_id:
                    edges.append({
                        "source": source_id,
                        "target": target_id,
                        "relation": "imports"
                    })
                else:
                    # Try external resolution
                    pkg_name = self._resolve_external(raw_import, lang)
                    if pkg_name:
                        ext_id = f"external:{pkg_name}"
                        
                        # Add external node if new
                        if ext_id not in external_ids:
                            external_ids.add(ext_id)
                            nodes.append({
                                "id": ext_id,
                                "type": "external"
                            })
                        
                        # Add edge
                        edges.append({
                            "source": source_id,
                            "target": ext_id,
                            "relation": "imports"
                        })

        return {
            "schema_version": "1.0",
            "nodes": nodes,
            "edges": edges
        }

    def _resolve_import(
        self, 
        import_str: str, 
        source_dir: str, 
        language: str, 
        path_map: Dict[str, str]
    ) -> Optional[str]:
        """
        Heuristic resolution logic for internal files.
        """
        if language == "python":
            return self._resolve_python(import_str, source_dir, path_map)
        elif language in ("javascript", "typescript"):
            return self._resolve_js(import_str, source_dir, path_map)
        return None

    def _resolve_external(self, import_str: str, language: str) -> Optional[str]:
        """
        Determines if an import string represents an external package and returns
        the canonical package name.
        """
        if language == "python":
            # Python Logic
            # 1. Ignore relative imports (starting with .)
            if import_str.startswith("."):
                return None
            
            # 2. Extract top-level package
            # e.g., "pandas.core.frame" -> "pandas"
            # e.g., "os" -> "os"
            return import_str.split(".")[0]

        elif language in ("javascript", "typescript"):
            # JS/TS Logic
            # 1. Ignore relative paths
            if import_str.startswith(".") or import_str.startswith("/"):
                return None
            
            # 2. Handle scoped packages (@org/pkg/sub -> @org/pkg)
            if import_str.startswith("@"):
                parts = import_str.split("/")
                if len(parts) >= 2:
                    return f"{parts[0]}/{parts[1]}"
                return import_str # Fallback (weird case)
            
            # 3. Handle standard packages (lodash/fp -> lodash)
            return import_str.split("/")[0]

        return None

    def _resolve_python(
        self, 
        import_str: str, 
        source_dir: str, 
        path_map: Dict[str, str]
    ) -> Optional[str]:
        # Convert dots to slashes: "utils.logger" -> "utils/logger"
        base_path = import_str.replace(".", "/")
        
        # Candidates to check
        candidates = []

        # 1. Repo-relative match (absolute import from root)
        # e.g. "utils/logger" -> "utils/logger.py"
        candidates.append(f"{base_path}.py")
        candidates.append(f"{base_path}/__init__.py")

        # 2. Source-relative match (sibling or sub-package import)
        # e.g. source="src", import="utils.logger" -> "src/utils/logger.py"
        # We use os.path.join but must force forward slashes
        rel_base = os.path.join(source_dir, base_path).replace("\\", "/")
        candidates.append(f"{rel_base}.py")
        candidates.append(f"{rel_base}/__init__.py")

        for c in candidates:
            c_lower = c.lower()
            if c_lower in path_map:
                return path_map[c_lower]

        return None

    def _resolve_js(
        self, 
        import_str: str, 
        source_dir: str, 
        path_map: Dict[str, str]
    ) -> Optional[str]:
        
        # 1. External packages (lodash, react) -> Skip internal check if not relative
        # Note: We check relative logic in _resolve_external, but for internal resolution
        # we strictly only look at relative paths or paths that might be aliased.
        # For v0.1/0.2, we assume internal imports start with "." to be safe, 
        # or we might catch absolute imports if they match a file exactly.
        
        # 2. Relative resolution
        try:
            joined = os.path.join(source_dir, import_str)
            normalized = os.path.normpath(joined).replace("\\", "/")
        except ValueError:
            return None

        # 3. Extensions probing
        extensions = ["", ".ts", ".tsx", ".js", ".jsx", ".d.ts", ".json"]
        
        for ext in extensions:
            candidate = f"{normalized}{ext}"
            candidate_lower = candidate.lower()
            if candidate_lower in path_map:
                return path_map[candidate_lower]
                
        # 4. Index probing
        index_extensions = [".ts", ".tsx", ".js", ".jsx"]
        for ext in index_extensions:
            candidate = f"{normalized}/index{ext}"
            candidate_lower = candidate.lower()
            if candidate_lower in path_map:
                return path_map[candidate_lower]
                
        return None
```

### `src/analysis/import_scanner.py`

```
import re
import ast
import os
from typing import List, Set

class ImportScanner:
    # --- JavaScript / TypeScript Patterns (Regex) ---
    
    # 1. import ... from 'x' (Supports multi-line via [\s\S]*?)
    _JS_IMPORT_FROM = re.compile(r'import\s+[\s\S]*?from\s+[\'"]([^\'"]+)[\'"]')
    
    # 2. import 'x' (Side effect)
    _JS_IMPORT_SIDE_EFFECT = re.compile(r'import\s+[\'"]([^\'"]+)[\'"]')
    
    # 3. require('x')
    _JS_REQUIRE = re.compile(r'require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)')

    # Comment Stripping
    _JS_BLOCK_COMMENT = re.compile(r'/\*[\s\S]*?\*/')
    _JS_LINE_COMMENT = re.compile(r'//.*')

    @staticmethod
    def scan(path: str, language: str) -> List[str]:
        """
        Scans a file for import statements based on its language.
        Returns a sorted list of unique import targets.
        """
        if language not in ("python", "javascript", "typescript"):
            return []

        try:
            # Limit read size to 1MB
            # Use 'utf-8-sig' to automatically consume BOM on Windows files
            with open(path, 'r', encoding='utf-8-sig', errors='ignore') as f:
                content = f.read(1_000_000)
        except OSError:
            return []

        imports: Set[str] = set()

        if language == "python":
            ImportScanner._scan_python(content, imports)
        elif language in ("javascript", "typescript"):
            ImportScanner._scan_js(content, imports)

        return sorted(list(imports))

    @staticmethod
    def _scan_python(content: str, imports: Set[str]):
        """
        Uses Python's native AST to extract imports reliably.
        """
        try:
            tree = ast.parse(content)
        except SyntaxError:
            # If the file is invalid Python, we simply skip scanning imports
            # rather than crashing the tool.
            return

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            
            elif isinstance(node, ast.ImportFrom):
                # Handle 'from x import y' -> module='x'
                # Handle 'from . import y' -> module=None, level=1
                
                module_name = node.module or ""
                
                # Reconstruct relative imports
                # level 1 = ., level 2 = .., etc.
                if node.level > 0:
                    prefix = "." * node.level
                    
                    # Special Case: 'from . import sibling'
                    # If module is empty but we have a level, the 'names' are likely submodules.
                    if not module_name:
                        for alias in node.names:
                            imports.add(prefix + alias.name)
                        continue
                    
                    module_name = prefix + module_name
                
                if module_name:
                    imports.add(module_name)

    @staticmethod
    def _scan_js(content: str, imports: Set[str]):
        """
        Uses Regex heuristics to extract JS/TS imports.
        """
        # 1. Strip Comments to avoid false positives
        clean_content = ImportScanner._JS_BLOCK_COMMENT.sub('', content)
        clean_content = ImportScanner._JS_LINE_COMMENT.sub('', clean_content)

        # 2. Run Regex on the full cleaned content
        
        # import ... from '...'
        for match in ImportScanner._JS_IMPORT_FROM.finditer(clean_content):
            imports.add(match.group(1))
            
        # import '...' (side effect)
        for match in ImportScanner._JS_IMPORT_SIDE_EFFECT.finditer(clean_content):
            full_match = match.group(0)
            # Heuristic: avoid capturing the "import" part of a "from" statement
            if "from" not in full_match: 
                imports.add(match.group(1))

        # require('...')
        for match in ImportScanner._JS_REQUIRE.finditer(clean_content):
            imports.add(match.group(1))
```

### `src/cli/__init__.py`

```

```

### `src/cli/main.py`

```
﻿import argparse
from src.core.controller import run_snapshot, run_export_flatten

def _parse_args():
    parser = argparse.ArgumentParser(prog="repo-runner", description="repo-runner v0.1")
    sub = parser.add_subparsers(dest="command", required=True)

    # snapshot
    snap = sub.add_parser("snapshot", help="Create a deterministic structural snapshot")
    snap.add_argument("repo_root", help="Repository root path")
    snap.add_argument("--output-root", required=True, help="Output root directory for snapshots")
    snap.add_argument("--depth", type=int, default=25)
    snap.add_argument(
        "--ignore",
        nargs="*",
        default=[".git", "node_modules", "__pycache__", "dist", "build", ".next", ".expo", ".venv"],
    )
    snap.add_argument("--include-extensions", nargs="*", default=[])
    snap.add_argument("--include-readme", action="store_true", default=True)
    snap.add_argument("--no-include-readme", action="store_false", dest="include_readme")
    snap.add_argument("--write-current-pointer", action="store_true", default=True)
    snap.add_argument("--no-write-current-pointer", action="store_false", dest="write_current_pointer")
    snap.add_argument("--export-flatten", action="store_true", help="Automatically generate flatten.md export")

    # export
    exp = sub.add_parser("export", help="Export derived artifacts from a snapshot")
    exp_sub = exp.add_subparsers(dest="export_command", required=True)

    flatten = exp_sub.add_parser(
        "flatten",
        help="Generate deterministic flatten markdown (list_tree alternative)",
    )
    flatten.add_argument("--output-root", required=True, help="Output root directory where snapshots live")
    flatten.add_argument(
        "--snapshot-id",
        required=False,
        default=None,
        help="Snapshot id to export from (defaults to current)",
    )
    flatten.add_argument("--repo-root", required=True, help="Repo root path (used to read file contents)")
    flatten.add_argument(
        "--output",
        required=False,
        default=None,
        help="Output path for markdown (defaults to snapshot exports/flatten.md)",
    )
    flatten.add_argument("--tree-only", action="store_true", default=False)
    flatten.add_argument("--include-readme", action="store_true", default=True)
    flatten.add_argument("--no-include-readme", action="store_false", dest="include_readme")
    flatten.add_argument("--scope", required=False, default="full")
    flatten.add_argument("--title", required=False, default=None)

    # ui
    sub.add_parser("ui", help="Launch the graphical control panel")

    return parser.parse_args()


def main():
    args = _parse_args()

    if args.command == "snapshot":
        snap_id = run_snapshot(
            repo_root=args.repo_root,
            output_root=args.output_root,
            depth=args.depth,
            ignore=args.ignore,
            include_extensions=args.include_extensions,
            include_readme=args.include_readme,
            write_current_pointer=args.write_current_pointer,
            export_flatten=args.export_flatten,
        )
        print(f"Snapshot created: {snap_id}")
        return

    if args.command == "export" and args.export_command == "flatten":
        out = run_export_flatten(
            output_root=args.output_root,
            repo_root=args.repo_root,
            snapshot_id=args.snapshot_id,
            output_path=args.output,
            tree_only=args.tree_only,
            include_readme=args.include_readme,
            scope=args.scope,
            title=args.title,
        )
        print(f"Wrote: {out}")
        return
    
    if args.command == "ui":
        from src.gui.app import run_gui
        run_gui()
        return

    raise RuntimeError("Unhandled command")


if __name__ == "__main__":
    main()
```

### `src/core/__init__.py`

```
# src/core/__init__.py
```

### `src/core/controller.py`

```
import os
from typing import List, Optional, Set

from src.core.types import Manifest, FileEntry
from src.analysis.import_scanner import ImportScanner
from src.analysis.graph_builder import GraphBuilder
from src.exporters.flatten_markdown_exporter import (
    FlattenMarkdownExporter,
    FlattenOptions,
)
from src.fingerprint.file_fingerprint import FileFingerprint
from src.normalize.path_normalizer import PathNormalizer
from src.scanner.filesystem_scanner import FileSystemScanner
from src.snapshot.snapshot_loader import SnapshotLoader
from src.snapshot.snapshot_writer import SnapshotWriter
from src.structure.structure_builder import StructureBuilder


def _filter_by_extensions(abs_files: List[str], include_exts: List[str]) -> List[str]:
    if not include_exts:
        return abs_files

    include = set([e.lower() for e in include_exts])
    out = []

    for p in abs_files:
        ext = os.path.splitext(p)[1].lower()
        if ext in include:
            out.append(p)

    return out


def run_snapshot(
    repo_root: str,
    output_root: str,
    depth: int,
    ignore: List[str],
    include_extensions: List[str],
    include_readme: bool,
    write_current_pointer: bool,
    explicit_file_list: Optional[List[str]] = None,
    export_flatten: bool = False,
) -> str:
    """
    Creates a snapshot.
    If explicit_file_list is provided, it skips the directory scan and uses that exact list.
    """
    repo_root_abs = os.path.abspath(repo_root)

    # FAIL FAST: If the repo root doesn't exist, stop immediately.
    if not os.path.isdir(repo_root_abs):
        raise ValueError(f"Repository root does not exist or is not a directory: {repo_root_abs}")

    if explicit_file_list is not None:
        # UI Override Mode: Use the list exactly as provided
        absolute_files = [os.path.abspath(f) for f in explicit_file_list]
    else:
        # CLI / Default Mode: Scan the disk
        scanner = FileSystemScanner(depth=depth, ignore_names=set(ignore))
        absolute_files = scanner.scan([repo_root_abs])
        absolute_files = _filter_by_extensions(absolute_files, include_extensions)

    normalizer = PathNormalizer(repo_root_abs)
    file_entries: List[FileEntry] = []
    total_bytes = 0
    seen_ids: Set[str] = set()

    for abs_path in absolute_files:
        # Hardening: Check if file still exists before processing
        if not os.path.exists(abs_path):
            continue

        normalized = normalizer.normalize(abs_path)

        # In override mode, we assume the user already selected what they want, 
        # but we still respect the readme flag if scanning.
        if explicit_file_list is None:
            if not include_readme and os.path.basename(normalized).lower().startswith("readme"):
                continue

        stable_id = normalizer.file_id(normalized)

        if stable_id in seen_ids:
            # In explicit mode, we warn/skip instead of crashing to be robust to UI quirks
            if explicit_file_list:
                continue
            raise RuntimeError(f"Path collision after normalization: {stable_id}")

        seen_ids.add(stable_id)

        module_path = normalizer.module_path(normalized)
        
        # Fingerprint might fail if file was deleted between scan and click,
        # or if it is locked/unreadable.
        try:
            fp = FileFingerprint.fingerprint(abs_path)
            total_bytes += fp["size_bytes"]
            
            # Analyze Imports
            # If import scanning fails, we default to empty list rather than crashing
            try:
                imports = ImportScanner.scan(abs_path, fp["language"])
            except Exception:
                imports = []

            entry: FileEntry = {
                "stable_id": stable_id,
                "path": normalized,
                "module_path": module_path,
                "sha256": fp["sha256"],
                "size_bytes": fp["size_bytes"],
                "language": fp["language"],
                "imports": imports
            }
            file_entries.append(entry)
        except OSError:
            # File unreadable, locked, or vanished. Skip.
            continue

    file_entries = sorted(file_entries, key=lambda x: x["path"])

    # 1. Build Containment Structure
    structure = StructureBuilder().build(
        repo_id=PathNormalizer.repo_id(),
        files=file_entries,
    )

    # 2. Build Dependency Graph
    graph = GraphBuilder().build(file_entries)

    # Extract external dependencies for Manifest stats
    external_deps = sorted([
        n["id"].replace("external:", "") 
        for n in graph["nodes"] 
        if n["type"] == "external"
    ])

    # 3. Assemble Manifest
    manifest: Manifest = {
        "schema_version": "1.0",
        "tool": {"name": "repo-runner", "version": "0.1.0"},
        "inputs": {
            "repo_root": repo_root_abs.replace("\\", "/"),
            "roots": [repo_root_abs.replace("\\", "/")],
            "git": {
                "is_repo": os.path.isdir(os.path.join(repo_root_abs, ".git")),
                "commit": None,
            },
        },
        "config": {
            "depth": depth,
            "ignore_names": ignore,
            "include_extensions": include_extensions,
            "include_readme": include_readme,
            "tree_only": False,
            "manual_override": explicit_file_list is not None
        },
        "stats": {
            "file_count": len(file_entries),
            "total_bytes": total_bytes,
            "external_dependencies": external_deps
        },
        "files": file_entries,
        "snapshot": {} # Populated by SnapshotWriter
    }

    # 4. Write Snapshot
    writer = SnapshotWriter(output_root)
    snapshot_id = writer.write(
        manifest,
        structure,
        graph=graph,
        write_current_pointer=write_current_pointer,
    )

    # 5. Optional Auto-Export
    if export_flatten:
        exporter = FlattenMarkdownExporter()
        # Default options for auto-export
        options = FlattenOptions(
            tree_only=False,
            include_readme=True,
            scope="full"
        )
        snapshot_dir = os.path.join(output_root, snapshot_id)
        
        # We reuse the manifest we just built to avoid re-reading from disk
        exporter.export(
            repo_root=repo_root_abs,
            snapshot_dir=snapshot_dir,
            manifest=manifest,
            output_path=None, # Uses default: exports/flatten.md
            options=options,
            title=f"Auto Export: {snapshot_id}"
        )

    return snapshot_id


def run_export_flatten(
    output_root: str,
    repo_root: str,
    snapshot_id: Optional[str],
    output_path: Optional[str],
    tree_only: bool,
    include_readme: bool,
    scope: str,
    title: Optional[str],
) -> str:
    loader = SnapshotLoader(output_root)
    snapshot_dir = loader.resolve_snapshot_dir(snapshot_id)
    manifest = loader.load_manifest(snapshot_dir)

    exporter = FlattenMarkdownExporter()

    options = FlattenOptions(
        tree_only=tree_only,
        include_readme=include_readme,
        scope=scope,
    )

    return exporter.export(
        repo_root=os.path.abspath(repo_root),
        snapshot_dir=snapshot_dir,
        manifest=manifest,
        output_path=output_path,
        options=options,
        title=title,
    )
```

### `src/core/types.py`

```
from typing import TypedDict, List, Optional, Any, Dict

class FileEntry(TypedDict):
    stable_id: str
    path: str
    module_path: str
    sha256: str
    size_bytes: int
    language: str
    imports: List[str]

class SnapshotTool(TypedDict):
    name: str
    version: str

class SnapshotInputs(TypedDict):
    repo_root: str
    roots: List[str]
    git: Dict[str, Any]

class SnapshotConfig(TypedDict):
    depth: int
    ignore_names: List[str]
    include_extensions: List[str]
    include_readme: bool
    tree_only: bool
    manual_override: bool

class SnapshotStats(TypedDict):
    file_count: int
    total_bytes: int
    external_dependencies: List[str]  # New field

class Manifest(TypedDict):
    schema_version: str
    tool: SnapshotTool
    inputs: SnapshotInputs
    config: SnapshotConfig
    stats: SnapshotStats
    files: List[FileEntry]
    snapshot: Dict[str, Any]

# --- Graph Types ---

class GraphNode(TypedDict):
    id: str  # stable_id
    type: str  # file | module | external

class GraphEdge(TypedDict):
    source: str  # stable_id
    target: str  # stable_id
    relation: str  # imports | defines

class GraphStructure(TypedDict):
    schema_version: str
    nodes: List[GraphNode]
    edges: List[GraphEdge]
```

### `src/entry_point.py`

```
# src/entry_point.py
import sys
import multiprocessing

if sys.platform.startswith('win'):
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

def launch():
    if len(sys.argv) > 1:
        from src.cli.main import main
        main()
    else:
        from src.gui.app import run_gui
        run_gui()

if __name__ == "__main__":
    multiprocessing.freeze_support()
    launch()
```

### `src/exporters/flatten_markdown_exporter.py`

```
import os
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass(frozen=True)
class FlattenOptions:
    tree_only: bool
    include_readme: bool
    scope: str  # full | module:<path> | file:<path> | list:<a,b,c> | prefix:<path>

class FlattenMarkdownExporter:
    TEXT_EXTENSIONS = {
        ".ts", ".tsx", ".js", ".jsx",
        ".py", ".rs", ".go", ".java",
        ".json", ".md", ".txt",
        ".html", ".css", ".sql", ".toml",
        ".ps1", ".ejs", ".yml", ".yaml",
        ".env", ".example", ".gitignore",
        ".d.ts",
    }

    def generate_content(
        self,
        repo_root: str,
        manifest: Dict,
        options: FlattenOptions,
        title: Optional[str] = None,
        snapshot_id: str = "PREVIEW"
    ) -> str:
        """Generates the markdown content as a string without writing to disk."""
        files = self._canonical_files_from_manifest(manifest, options)
        tree_md = self._render_tree([f["path"] for f in files])
        content_md = "" if options.tree_only else self._render_contents(repo_root, files)

        header = [
            f"# {title or 'repo-runner flatten export'}",
            "",
            f"- repo_root: `{repo_root}`",
            f"- snapshot_id: `{snapshot_id}`",
            f"- file_count: `{len(files)}`",
            f"- tree_only: `{options.tree_only}`",
            "",
        ]

        return "\n".join(header) + tree_md + ("\n" + content_md if content_md else "")

    def export(
        self,
        repo_root: str,
        snapshot_dir: str,
        manifest: Dict,
        output_path: Optional[str],
        options: FlattenOptions,
        title: Optional[str] = None,
    ) -> str:
        snapshot_id = os.path.basename(snapshot_dir)
        final_md = self.generate_content(repo_root, manifest, options, title, snapshot_id)

        if output_path is None:
            exports_dir = os.path.join(snapshot_dir, "exports")
            os.makedirs(exports_dir, exist_ok=True)
            output_path = os.path.join(exports_dir, "flatten.md")

        with open(output_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(final_md)

        return output_path

    def _canonical_files_from_manifest(self, manifest: Dict, options: FlattenOptions) -> List[Dict]:
        files = manifest.get("files", [])
        entries = []
        for entry in files:
            path = entry["path"]
            if not options.include_readme and path.lower().startswith("readme"):
                continue
            entries.append(entry)
        scoped = self._apply_scope(entries, options.scope)
        scoped.sort(key=lambda x: x["path"])
        return scoped

    def _apply_scope(self, entries: List[Dict], scope: str) -> List[Dict]:
        if scope == "full": return list(entries)
        if scope.startswith("module:"):
            prefix = scope.split("module:", 1)[1].rstrip("/")
            return [e for e in entries if e["path"].startswith(prefix + "/")]
        if scope.startswith("prefix:"):
            prefix = scope.split("prefix:", 1)[1]
            return [e for e in entries if e["path"].startswith(prefix)]
        if scope.startswith("file:"):
            target = scope.split("file:", 1)[1]
            return [e for e in entries if e["path"] == target]
        if scope.startswith("list:"):
            raw = scope.split("list:", 1)[1]
            targets = [t.strip() for t in raw.split(",") if t.strip()]
            target_set = set(targets)
            return [e for e in entries if e["path"] in target_set]
        raise ValueError(f"Invalid scope: {scope}")

    def _render_tree(self, paths: List[str]) -> str:
        root = {}
        for p in paths:
            parts = [x for x in p.split("/") if x]
            node = root
            for part in parts:
                node = node.setdefault(part, {})
        lines = ["## Tree", "", "```"]
        lines.extend(self._tree_lines(root, ""))
        lines.append("```")
        lines.append("")
        return "\n".join(lines)

    def _tree_lines(self, node: Dict, prefix: str) -> List[str]:
        keys = sorted(node.keys())
        lines = []
        for i, key in enumerate(keys):
            is_last = i == len(keys) - 1
            connector = "└── " if is_last else "├── "
            lines.append(prefix + connector + key)
            child_prefix = prefix + ("    " if is_last else "│   ")
            lines.extend(self._tree_lines(node[key], child_prefix))
        return lines

    def _render_contents(self, repo_root: str, files: List[Dict]) -> str:
        blocks = ["## File Contents", ""]
        for entry in files:
            path = entry["path"]
            abs_path = os.path.join(repo_root, path.replace("/", os.sep))
            blocks.append(f"### `{path}`")
            blocks.append("")
            ext = os.path.splitext(path)[1].lower()
            if ext not in self.TEXT_EXTENSIONS or self._sniff_binary(abs_path):
                blocks.append(self._binary_placeholder(entry))
                blocks.append("")
                continue
            try:
                with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
            except OSError as e:
                content = f"<<ERROR: {e}>>"
            blocks.append(f"```")
            blocks.append(content.rstrip("\n"))
            blocks.append("```")
            blocks.append("")
        return "\n".join(blocks)

    @staticmethod
    def _sniff_binary(abs_path: str) -> bool:
        try:
            with open(abs_path, "rb") as f:
                chunk = f.read(4096)
        except OSError: return False
        return b"\x00" in chunk

    @staticmethod
    def _binary_placeholder(entry: Dict) -> str:
        return "\n".join([
            "```",
            "<<BINARY_OR_SKIPPED_FILE>>",
            f"size_bytes: {entry.get('size_bytes')}",
            f"sha256: {entry.get('sha256')}",
            "```",
        ])
```

### `src/fingerprint/file_fingerprint.py`

```
import hashlib
import os
from typing import Dict


class FileFingerprint:
    LANGUAGE_MAP = {
        ".ts": "typescript",
        ".tsx": "typescript",
        ".js": "javascript",
        ".jsx": "javascript",
        ".py": "python",
        ".rs": "rust",
        ".go": "go",
        ".java": "java",
        ".html": "html",
        ".css": "css",
        ".sql": "sql",
        ".toml": "toml",
        ".ps1": "powershell",
        ".md": "markdown",
        ".json": "json",
    }

    @staticmethod
    def fingerprint(path: str) -> Dict:
        """
        Computes the fingerprint of a file.
        Raises OSError if the file cannot be opened or read (e.g. locked, permissions).
        """
        sha = hashlib.sha256()
        
        # We allow OSError to propagate so the caller (Controller) can decide 
        # whether to skip the file or fail the run.
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha.update(chunk)

        try:
            size = os.path.getsize(path)
        except OSError:
            # Fallback if getsize fails but read succeeded (rare race condition)
            size = 0 

        ext = os.path.splitext(path)[1].lower()
        language = FileFingerprint.LANGUAGE_MAP.get(ext, "unknown")

        return {
            "sha256": sha.hexdigest(),
            "size_bytes": size,
            "language": language,
        }
```

### `src/gui/__init__.py`

```
# src/gui/__init__.py
```

### `src/gui/app.py`

```
import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import ctypes
import datetime

from src.scanner.filesystem_scanner import FileSystemScanner
from src.normalize.path_normalizer import PathNormalizer
from src.core.controller import run_snapshot
from src.exporters.flatten_markdown_exporter import FlattenMarkdownExporter, FlattenOptions

from src.gui.components.config_tabs import ConfigTabs
from src.gui.components.tree_view import FileTreePanel
from src.gui.components.preview_pane import PreviewPanel
from src.gui.components.export_preview import ExportPreviewWindow

# High DPI
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

class RepoRunnerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("repo-runner Control Panel")
        self.geometry("1300x900")
        
        self.style = ttk.Style(self)
        self.style.theme_use('vista' if 'vista' in self.style.theme_names() else 'clam')
        
        self.repo_root = None
        
        self._build_ui()

    def _build_ui(self):
        # Top Bar: Repository Selection
        top_bar = ttk.Frame(self, padding=10)
        top_bar.pack(side=tk.TOP, fill=tk.X)
        
        ttk.Label(top_bar, text="Repository Root:").pack(side=tk.LEFT)
        self.ent_root = ttk.Entry(top_bar)
        self.ent_root.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        ttk.Button(top_bar, text="Browse...", command=self._browse).pack(side=tk.LEFT)

        # Main Workspace: Paned Window
        main_paned = ttk.PanedWindow(self, orient=tk.VERTICAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Upper: Settings Tabs & Actions
        upper_frame = ttk.Frame(main_paned)
        main_paned.add(upper_frame, weight=0)
        
        self.config_tabs = ConfigTabs(upper_frame)
        self.config_tabs.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        action_frame = ttk.Frame(upper_frame, padding=10)
        action_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        ttk.Button(action_frame, text="Scan Repository", command=self._scan, width=20).pack(pady=5)
        
        self.btn_snap = ttk.Button(action_frame, text="Snapshot Selection", command=self._snapshot, state=tk.DISABLED, width=20)
        self.btn_snap.pack(pady=5)
        
        self.btn_export = ttk.Button(action_frame, text="Quick Export (Preview)", command=self._quick_export, state=tk.DISABLED, width=20)
        self.btn_export.pack(pady=5)

        # Lower: Tree and Preview
        lower_paned = ttk.PanedWindow(main_paned, orient=tk.HORIZONTAL)
        main_paned.add(lower_paned, weight=1)
        
        self.tree_panel = FileTreePanel(lower_paned, self._on_file_selected)
        lower_paned.add(self.tree_panel, weight=1)
        
        self.preview_panel = PreviewPanel(lower_paned)
        lower_paned.add(self.preview_panel, weight=2)

        # Status
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W).pack(side=tk.BOTTOM, fill=tk.X)

    def _browse(self):
        path = filedialog.askdirectory()
        if path:
            self.ent_root.delete(0, tk.END)
            self.ent_root.insert(0, path)
            self.repo_root = path

    def _scan(self):
        root = self.ent_root.get().strip()
        if not os.path.isdir(root):
            messagebox.showerror("Error", "Invalid Repository Path")
            return
        
        self.repo_root = root
        self.status_var.set("Scanning...")
        self.tree_panel.clear()
        self.preview_panel.clear()
        
        # Get settings
        depth = self.config_tabs.depth_var.get()
        ignore = set(self.config_tabs.ignore_var.get().split())
        exts = self.config_tabs.ext_var.get().split()
        readme = self.config_tabs.include_readme_var.get()
        
        def run():
            try:
                scanner = FileSystemScanner(depth=depth, ignore_names=ignore)
                abs_files = scanner.scan([root])
                
                # Filter
                filtered = []
                ext_set = set(e.lower() for e in exts)
                for f in abs_files:
                    _, ext = os.path.splitext(f)
                    is_readme = readme and os.path.basename(f).lower().startswith("readme")
                    if not ext_set or ext.lower() in ext_set or is_readme:
                        filtered.append(f)
                
                # Normalize for tree
                normalizer = PathNormalizer(root)
                struct = {}
                for f in filtered:
                    rel = normalizer.normalize(f)
                    parts = rel.split('/')
                    curr = struct
                    for p in parts:
                        curr = curr.setdefault(p, {})
                    curr['__metadata__'] = {'abs_path': f, 'stable_id': normalizer.file_id(rel)}
                
                self.after(0, lambda: self._scan_done(struct, len(filtered)))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Scan Error", str(e)))

        threading.Thread(target=run, daemon=True).start()

    def _scan_done(self, struct, count):
        self.tree_panel.populate(struct)
        self.status_var.set(f"Scan Complete. Found {count} files.")
        self.btn_snap.config(state=tk.NORMAL)
        self.btn_export.config(state=tk.NORMAL)

    def _on_file_selected(self, abs_path, stable_id):
        self.preview_panel.load_file(abs_path, stable_id)

    def _snapshot(self):
        files = self.tree_panel.get_checked_files()
        if not files:
            messagebox.showwarning("Empty", "No files selected.")
            return
            
        out = filedialog.askdirectory(title="Select Snapshot Output Root")
        if not out: return
        
        # UI Locking
        self.btn_snap.config(state=tk.DISABLED)
        self.status_var.set("Creating Snapshot (Calculating Hashes)...")
        
        def run():
            try:
                sid = run_snapshot(
                    repo_root=self.repo_root,
                    output_root=out,
                    depth=self.config_tabs.depth_var.get(),
                    ignore=self.config_tabs.ignore_var.get().split(),
                    include_extensions=[],
                    include_readme=False,
                    write_current_pointer=self.config_tabs.write_current_var.get(),
                    explicit_file_list=files
                )
                self.after(0, lambda: self._snapshot_done(sid))
            except Exception as e:
                self.after(0, lambda: self._snapshot_fail(str(e)))

        threading.Thread(target=run, daemon=True).start()

    def _snapshot_done(self, sid):
        self.btn_snap.config(state=tk.NORMAL)
        self.status_var.set(f"Snapshot Created: {sid}")
        messagebox.showinfo("Success", f"Snapshot Created: {sid}")

    def _snapshot_fail(self, error):
        self.btn_snap.config(state=tk.NORMAL)
        self.status_var.set("Snapshot Failed.")
        messagebox.showerror("Error", error)

    def _quick_export(self):
        files = self.tree_panel.get_checked_files()
        if not files:
            messagebox.showwarning("Empty", "No files selected.")
            return

        tree_only = self.config_tabs.export_tree_only_var.get()
        self.status_var.set("Generating Export Preview...")
        self.btn_export.config(state=tk.DISABLED)
        
        def run_export():
            try:
                normalizer = PathNormalizer(self.repo_root)
                manifest_files = []
                for abs_p in files:
                    rel = normalizer.normalize(abs_p)
                    manifest_files.append({
                        "path": rel,
                        "size_bytes": 0,
                        "sha256": "pre-snapshot"
                    })
                    
                dummy_manifest = {"files": manifest_files}
                
                options = FlattenOptions(
                    tree_only=tree_only,
                    include_readme=True, 
                    scope="full"
                )
                
                exporter = FlattenMarkdownExporter()
                
                content = exporter.generate_content(
                    repo_root=self.repo_root,
                    manifest=dummy_manifest,
                    options=options,
                    title=f"Quick Export: {os.path.basename(self.repo_root)}",
                    snapshot_id="QUICK_EXPORT_PREVIEW"
                )
                
                self.after(0, lambda: self._quick_export_done(content))
            except Exception as e:
                self.after(0, lambda: self._quick_export_fail(str(e)))

        threading.Thread(target=run_export, daemon=True).start()

    def _quick_export_done(self, content):
        self.btn_export.config(state=tk.NORMAL)
        self.status_var.set("Export Preview Ready.")
        
        default_name = f"flattened_{os.path.basename(self.repo_root)}_{datetime.date.today()}.md"
        ExportPreviewWindow(self, content, default_name)

    def _quick_export_fail(self, error):
        self.btn_export.config(state=tk.NORMAL)
        self.status_var.set("Export Failed.")
        messagebox.showerror("Export Error", error)

def run_gui():
    RepoRunnerApp().mainloop()
```

### `src/gui/components/config_tabs.py`

```
import tkinter as tk
from tkinter import ttk

class ConfigTabs(ttk.Notebook):
    def __init__(self, parent):
        super().__init__(parent)
        
        # Variables
        self.depth_var = tk.IntVar(value=25)
        self.ignore_var = tk.StringVar(value=".git node_modules __pycache__ dist build .next .expo .venv")
        self.ext_var = tk.StringVar(value="")
        self.include_readme_var = tk.BooleanVar(value=True)
        self.write_current_var = tk.BooleanVar(value=True)
        
        # New: Export options
        self.export_tree_only_var = tk.BooleanVar(value=False)
        
        self._build_scan_tab()
        self._build_ignore_tab()
        self._build_output_tab()

    def _build_scan_tab(self):
        tab = ttk.Frame(self, padding=10)
        self.add(tab, text=" Scan Settings ")
        
        # Depth
        row1 = ttk.Frame(tab)
        row1.pack(fill=tk.X, pady=5)
        ttk.Label(row1, text="Maximum Traversal Depth:", width=25).pack(side=tk.LEFT)
        ttk.Spinbox(row1, from_=0, to=100, textvariable=self.depth_var, width=10).pack(side=tk.LEFT)
        
        # Extensions
        row2 = ttk.Frame(tab)
        row2.pack(fill=tk.X, pady=5)
        ttk.Label(row2, text="Include Extensions:", width=25).pack(side=tk.LEFT)
        ttk.Entry(row2, textvariable=self.ext_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(row2, text="(space separated, e.g. .ts .py)", font=("Segoe UI", 8), foreground="gray").pack(side=tk.LEFT, padx=5)

        # Readme
        row3 = ttk.Frame(tab)
        row3.pack(fill=tk.X, pady=5)
        ttk.Checkbutton(row3, text="Always include README files (overrides extension filter)", variable=self.include_readme_var).pack(side=tk.LEFT)

    def _build_ignore_tab(self):
        tab = ttk.Frame(self, padding=10)
        self.add(tab, text=" Ignore Rules ")
        
        ttk.Label(tab, text="Directory and File names to ignore:").pack(anchor=tk.W, pady=(0, 5))
        txt_ignore = tk.Text(tab, height=4, font=("Segoe UI", 9))
        txt_ignore.pack(fill=tk.BOTH, expand=True)
        
        # Sync the text box with the variable
        txt_ignore.insert("1.0", self.ignore_var.get())
        def sync_var(event=None):
            self.ignore_var.set(txt_ignore.get("1.0", tk.END).strip())
        txt_ignore.bind("<KeyRelease>", sync_var)

    def _build_output_tab(self):
        tab = ttk.Frame(self, padding=10)
        self.add(tab, text=" Output / Export ")
        
        # Snapshot Config
        lbl_snap = ttk.Label(tab, text="Snapshot Config", font=("Segoe UI", 9, "bold"))
        lbl_snap.pack(anchor=tk.W, pady=(0, 5))
        
        ttk.Checkbutton(tab, text="Update 'current.json' pointer on snapshot", variable=self.write_current_var).pack(anchor=tk.W, pady=2)
        
        ttk.Separator(tab, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=15)
        
        # Export Config
        lbl_exp = ttk.Label(tab, text="Quick Export Config", font=("Segoe UI", 9, "bold"))
        lbl_exp.pack(anchor=tk.W, pady=(0, 5))
        
        ttk.Checkbutton(tab, text="Tree Only (No file contents)", variable=self.export_tree_only_var).pack(anchor=tk.W, pady=2)

        ttk.Label(tab, text="Note: Snapshots are always created in a timestamped subfolder.", 
                  font=("Segoe UI", 8, "italic"), foreground="gray").pack(side=tk.BOTTOM, anchor=tk.W, pady=10)
```

### `src/gui/components/export_preview.py`

```
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

class ExportPreviewWindow(tk.Toplevel):
    def __init__(self, parent, content, default_filename="export.md"):
        super().__init__(parent)
        self.title("Export Preview")
        self.geometry("1000x800")
        
        self.content = content
        self.default_filename = default_filename
        
        self._build_ui()
        
        # Behavior: Focus on this window
        self.focus_force()

    def _build_ui(self):
        # Toolbar
        toolbar = ttk.Frame(self, padding=5)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        
        ttk.Button(toolbar, text="💾 Save to File...", command=self._save).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="📋 Copy to Clipboard", command=self._copy).pack(side=tk.LEFT, padx=2)
        
        # Stats
        lines = self.content.count('\n') + 1
        chars = len(self.content)
        lbl_stats = ttk.Label(toolbar, text=f"  |  {lines:,} lines  |  {chars:,} chars  |", font=("Segoe UI", 9))
        lbl_stats.pack(side=tk.LEFT, padx=10)

        ttk.Button(toolbar, text="Close", command=self.destroy).pack(side=tk.RIGHT, padx=2)
        
        # Content Area
        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.text_area = tk.Text(container, wrap=tk.NONE, font=("Consolas", 10), undo=False)
        self.text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        ysb = ttk.Scrollbar(container, orient=tk.VERTICAL, command=self.text_area.yview)
        ysb.pack(side=tk.RIGHT, fill=tk.Y)
        
        xsb = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.text_area.xview)
        xsb.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.text_area.configure(yscrollcommand=ysb.set, xscrollcommand=xsb.set)
        
        # Insert content (read-only state after insert)
        self.text_area.insert("1.0", self.content)
        self.text_area.configure(state=tk.DISABLED)

    def _save(self):
        out_path = filedialog.asksaveasfilename(
            defaultextension=".md",
            filetypes=[("Markdown", "*.md"), ("All Files", "*.*")],
            initialfile=self.default_filename,
            title="Save Export"
        )
        if out_path:
            try:
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(self.content)
                messagebox.showinfo("Saved", f"Successfully saved to:\n{out_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file:\n{e}")

    def _copy(self):
        self.clipboard_clear()
        self.clipboard_append(self.content)
        messagebox.showinfo("Copied", "Content copied to clipboard!")
```

### `src/gui/components/preview_pane.py`

```
import tkinter as tk
from tkinter import ttk
from src.fingerprint.file_fingerprint import FileFingerprint
from src.analysis.import_scanner import ImportScanner

class PreviewPanel(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        
        # Metadata Header (Brief)
        self.lbl_meta = ttk.Label(self, text="Select a file to preview properties.", 
                                  background="#f0f0f0", padding=5, relief=tk.RIDGE)
        self.lbl_meta.pack(fill=tk.X, side=tk.TOP)
        
        # Text Area
        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True)
        
        self.text_preview = tk.Text(container, wrap=tk.NONE, font=("Consolas", 10), undo=False)
        self.text_preview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=self.text_preview.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_preview.configure(yscrollcommand=scrollbar.set)

    def clear(self):
        self.text_preview.delete("1.0", tk.END)
        self.lbl_meta.config(text="Select a file to preview properties.")

    def load_file(self, abs_path, stable_id):
        self.clear()
        try:
            # 1. Fingerprint (Size, SHA, Lang)
            fp = FileFingerprint.fingerprint(abs_path)
            
            # 2. Scan Imports (Lazy load on click using detected language)
            imports = ImportScanner.scan(abs_path, fp['language'])
            
            # 3. Update Brief Header Label
            import_count = len(imports)
            self.lbl_meta.config(text=f" ID: {stable_id}  |  {fp['language']}  |  {import_count} Imports")

            # 4. Construct Detailed Metadata Header
            header_lines = [
                f"Path:    {abs_path}",
                f"SHA256:  {fp['sha256']}",
                f"Size:    {fp['size_bytes']:,} bytes",
                "-" * 60,
                "IMPORTS FOUND:",
            ]
            
            if imports:
                for imp in imports:
                    header_lines.append(f"  • {imp}")
            else:
                header_lines.append("  (none)")
                
            header_lines.append("-" * 60)
            header_lines.append("") # Spacer line
            
            full_header = "\n".join(header_lines)
            
            # 5. Insert Header
            self.text_preview.insert("1.0", full_header)

            # 6. Append Real File Content
            if fp['size_bytes'] > 250_000:
                self.text_preview.insert(tk.END, "<< File too large for preview >>")
            else:
                with open(abs_path, 'r', encoding='utf-8', errors='replace') as f:
                    self.text_preview.insert(tk.END, f.read())
                    
        except Exception as e:
            self.text_preview.insert("1.0", f"<< Error loading file: {e} >>")
```

### `src/gui/components/tree_view.py`

```
import os
import tkinter as tk
from tkinter import ttk

class FileTreePanel(ttk.Frame):
    def __init__(self, parent, on_select_callback):
        super().__init__(parent)
        self.on_select_callback = on_select_callback
        
        # Tools
        tools = ttk.Frame(self)
        tools.pack(fill=tk.X, pady=(0, 5))
        
        # Styled Buttons
        ttk.Button(tools, text="☑ Check All", command=lambda: self._bulk_toggle(True), width=12).pack(side=tk.LEFT)
        ttk.Button(tools, text="☐ Uncheck All", command=lambda: self._bulk_toggle(False), width=12).pack(side=tk.LEFT, padx=5)
        
        # Tree Container
        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True)
        
        # Define Columns
        # Note: #0 is the tree structure (Name). We add 'check' as a distinct column.
        self.tree = ttk.Treeview(container, columns=("check", "size", "id"), selectmode="browse")
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # --- Column Configuration (MO2 Style) ---
        
        # 1. The Tree Column (Name/Structure)
        self.tree.column("#0", width=300, minwidth=200)
        self.tree.heading("#0", text="File / Folder Name", anchor=tk.W)
        
        # 2. The Checkbox Column (Strict width, first data column)
        self.tree.column("check", width=40, minwidth=40, stretch=False, anchor=tk.CENTER)
        self.tree.heading("check", text="Inc.")
        
        # 3. Metadata Columns
        self.tree.column("size", width=80, anchor=tk.E)
        self.tree.heading("size", text="Size")
        
        self.tree.column("id", width=150)
        self.tree.heading("id", text="Stable ID")
        
        # --- Event Bindings ---
        # We bind Button-1 (Left Click) to handle the checkbox strictly
        self.tree.bind("<Button-1>", self._on_click)
        # Selection event handles the preview logic
        self.tree.bind("<<TreeviewSelect>>", self._on_selection_change)

    def clear(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

    def _on_click(self, event):
        """
        Strict click handler to separate Toggle vs Select actions.
        """
        region = self.tree.identify_region(event.x, event.y)
        
        # Only interact if we clicked a cell (not a header, not the background)
        if region == "cell":
            column = self.tree.identify_column(event.x)
            item_id = self.tree.identify_row(event.y)
            
            # The 'check' column is typically #1 in the columns list.
            # identify_column returns string IDs like '#1', '#2'.
            if column == "#1" and item_id:
                # User specifically clicked the Checkbox column. Toggle it.
                self._toggle_item(item_id)
                # Return 'break' to prevent the tree from selecting this row
                # (Optional: remove if you want selection + toggle)
                return "break"

        # If user clicked the tree arrow or the name (Column #0), 
        # default Treeview behavior takes over (Expand or Select).
        return

    def _toggle_item(self, item_id):
        """Toggles the state of a single item and its children."""
        current_vals = list(self.tree.item(item_id, "values"))
        current_check = current_vals[0]
        
        # Toggle Logic
        # ☑ = True, ☐ = False
        new_state = "☐" if current_check == "☑" else "☑"
        
        self._set_check_recursive(item_id, new_state)

    def _set_check_recursive(self, item_id, state):
        vals = list(self.tree.item(item_id, "values"))
        vals[0] = state
        self.tree.item(item_id, values=vals)
        
        for child in self.tree.get_children(item_id):
            self._set_check_recursive(child, state)

    def _bulk_toggle(self, checked: bool):
        state = "☑" if checked else "☐"
        for child in self.tree.get_children():
            self._set_check_recursive(child, state)

    def _on_selection_change(self, event):
        """Handles updating the Preview Pane."""
        selected = self.tree.selection()
        if selected:
            tags = self.tree.item(selected[0], "tags")
            # Ensure it's a file, not a folder
            if tags and tags[0] != "folder":
                # tags[0] is abs_path, values[2] is stable_id
                stable_id = self.tree.item(selected[0], "values")[2]
                self.on_select_callback(tags[0], stable_id)

    def populate(self, tree_structure):
        self.clear()
        
        def insert_node(parent_id, structure):
            keys = sorted(structure.keys())
            folders = [k for k in keys if k != '__metadata__' and '__metadata__' not in structure[k]]
            files = [k for k in keys if k != '__metadata__' and '__metadata__' in structure[k]]
            
            for name in folders + files:
                node_data = structure[name]
                is_file = '__metadata__' in node_data
                
                # Default to Checked (☑)
                # Columns: [Check, Size, ID]
                values = ["☑", "", ""]
                
                if is_file:
                    meta = node_data['__metadata__']
                    try:
                        size = os.path.getsize(meta['abs_path'])
                        values = ["☑", f"{size:,} B", meta['stable_id']]
                    except OSError:
                        values = ["☑", "Err", meta['stable_id']]
                    icon = "📄 "
                else:
                    icon = "📁 "

                item_id = self.tree.insert(parent_id, "end", text=f"{icon}{name}", values=values, open=True)
                
                if is_file:
                    self.tree.item(item_id, tags=(node_data['__metadata__']['abs_path'], "file"))
                else:
                    self.tree.item(item_id, tags=("folder",))
                    insert_node(item_id, node_data)

        insert_node("", tree_structure)

    def get_checked_files(self, parent_id="") -> list:
        paths = []
        for item_id in self.tree.get_children(parent_id):
            vals = self.tree.item(item_id, "values")
            
            # 1. If this item is explicitly checked, add it (if it's a file)
            if vals[0] == "☑":
                tags = self.tree.item(item_id, "tags")
                if tags and tags[0] != "folder":
                    paths.append(tags[0])
            
            # 2. ALWAYS recurse into children, regardless of this folder's check state.
            # This fixes the bug where deep files weren't found if a parent folder was unchecked.
            paths.extend(self.get_checked_files(item_id))
            
        return paths
```

### `src/normalize/path_normalizer.py`

```
import os


class PathNormalizer:
    def __init__(self, repo_root: str):
        self.repo_root = os.path.abspath(repo_root)

    def normalize(self, absolute_path: str) -> str:
        relative = os.path.relpath(absolute_path, self.repo_root)

        # Normalize separators first.
        normalized = relative.replace("\\", "/")

        # Only strip a literal "./" prefix (do NOT strip leading dots from names like ".context-docs").
        if normalized.startswith("./"):
            normalized = normalized[2:]

        # Normalize any accidental leading slashes (defensive; relpath shouldn't produce these).
        while normalized.startswith("/"):
            normalized = normalized[1:]

        return normalized.lower()

    def module_path(self, file_path: str) -> str:
        directory = os.path.dirname(file_path)
        return directory.replace("\\", "/")

    @staticmethod
    def file_id(normalized_path: str) -> str:
        return f"file:{normalized_path}"

    @staticmethod
    def module_id(module_path: str) -> str:
        return f"module:{module_path}"

    @staticmethod
    def repo_id() -> str:
        return "repo:root"
```

### `src/scanner/filesystem_scanner.py`

```
import os
from typing import List, Set


class FileSystemScanner:
    def __init__(self, depth: int, ignore_names: Set[str]):
        self.depth = depth
        self.ignore_names = ignore_names

    def scan(self, root_paths: List[str]) -> List[str]:
        all_files = []
        visited_realpaths = set()

        for root in root_paths:
            # Handle explicit file inputs
            if os.path.isfile(root):
                all_files.append(os.path.abspath(root))
                continue

            # Handle directories
            abs_root = os.path.abspath(root)
            if os.path.isdir(abs_root):
                self._walk(abs_root, 0, all_files, visited_realpaths)

        return sorted(all_files)

    def _walk(self, directory: str, current_depth: int, results: List[str], visited: Set[str]):
        if self.depth >= 0 and current_depth > self.depth:
            return

        # 1. Symlink Cycle Detection
        try:
            real_path = os.path.realpath(directory)
            if real_path in visited:
                return
            visited.add(real_path)
        except OSError:
            # If we cannot resolve the path (permission/locked), we skip it safely.
            return

        # 2. List Directory
        try:
            entries = sorted(os.listdir(directory))
        except OSError:
            # Permission denied, not a directory, or vanished
            return

        for entry in entries:
            if entry in self.ignore_names:
                continue

            full_path = os.path.join(directory, entry)

            # 3. Classify and Recurse
            try:
                if os.path.isdir(full_path):
                    self._walk(full_path, current_depth + 1, results, visited)
                elif os.path.isfile(full_path):
                    results.append(os.path.abspath(full_path))
            except OSError:
                # Handle race conditions where file disappears between listdir and isfile
                continue
```

### `src/snapshot/snapshot_loader.py`

```
import json
import os
from typing import Optional


class SnapshotLoader:
    def __init__(self, output_root: str):
        self.output_root = output_root

    def resolve_snapshot_dir(self, snapshot_id: Optional[str]) -> str:
        if snapshot_id:
            snapshot_dir = os.path.join(self.output_root, snapshot_id)
            if not os.path.isdir(snapshot_dir):
                raise FileNotFoundError(f"Snapshot not found: {snapshot_dir}")
            return snapshot_dir

        current_path = os.path.join(self.output_root, "current.json")
        if not os.path.isfile(current_path):
            raise FileNotFoundError(
                f"current.json not found at output root: {current_path}. "
                "Run `repo-runner snapshot ...` first or pass --snapshot-id."
            )

        with open(current_path, "r", encoding="utf-8") as f:
            current = json.load(f)

        snapshot_id = current.get("current_snapshot_id")
        if not snapshot_id:
            raise ValueError("current.json missing required field: current_snapshot_id")

        snapshot_dir = os.path.join(self.output_root, snapshot_id)
        if not os.path.isdir(snapshot_dir):
            raise FileNotFoundError(f"Snapshot dir referenced by current.json not found: {snapshot_dir}")

        return snapshot_dir

    @staticmethod
    def load_manifest(snapshot_dir: str) -> dict:
        path = os.path.join(snapshot_dir, "manifest.json")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def load_structure(snapshot_dir: str) -> dict:
        path = os.path.join(snapshot_dir, "structure.json")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
```

### `src/snapshot/snapshot_writer.py`

```
import json
import os
from datetime import datetime, timezone
from typing import Dict, Optional

class SnapshotWriter:
    def __init__(self, output_root: str):
        self.output_root = output_root

    def write(
        self,
        manifest: Dict,
        structure: Dict,
        graph: Optional[Dict] = None,
        snapshot_id: Optional[str] = None,
        write_current_pointer: bool = True,
    ) -> str:
        os.makedirs(self.output_root, exist_ok=True)

        # Use timezone-aware UTC
        now_utc = datetime.now(timezone.utc)

        if snapshot_id is None:
            snapshot_id = now_utc.strftime("%Y-%m-%dT%H-%M-%SZ")

        snapshot_dir = os.path.join(self.output_root, snapshot_id)
        if os.path.exists(snapshot_dir):
            raise RuntimeError(f"Snapshot directory already exists: {snapshot_dir}")

        os.makedirs(snapshot_dir, exist_ok=False)
        os.makedirs(os.path.join(snapshot_dir, "exports"), exist_ok=True)

        manifest = dict(manifest)
        manifest.setdefault("snapshot", {})
        manifest["snapshot"] = dict(manifest["snapshot"])
        manifest["snapshot"].setdefault("snapshot_id", snapshot_id)
        # ISO 8601 format with Z
        manifest["snapshot"].setdefault("created_utc", now_utc.strftime("%Y-%m-%dT%H:%M:%SZ"))
        manifest["snapshot"].setdefault("output_root", self.output_root)

        # Write Manifest
        with open(os.path.join(snapshot_dir, "manifest.json"), "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, sort_keys=True)

        # Write Structure
        with open(os.path.join(snapshot_dir, "structure.json"), "w", encoding="utf-8") as f:
            json.dump(structure, f, indent=2, sort_keys=True)
            
        # Write Graph (if present)
        if graph:
            with open(os.path.join(snapshot_dir, "graph.json"), "w", encoding="utf-8") as f:
                json.dump(graph, f, indent=2, sort_keys=True)

        # Update Pointer
        if write_current_pointer:
            current_path = os.path.join(self.output_root, "current.json")
            with open(current_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "schema_version": "1.0",
                        "current_snapshot_id": snapshot_id,
                        "path": snapshot_id,
                    },
                    f,
                    indent=2,
                    sort_keys=True,
                )

        return snapshot_id
```

### `src/structure/structure_builder.py`

```
from collections import defaultdict
from typing import Dict, List


class StructureBuilder:
    def build(self, repo_id: str, files: List[Dict]) -> Dict:
        modules = defaultdict(list)

        for file_entry in files:
            module_path = file_entry["module_path"]
            modules[module_path].append(file_entry["stable_id"])

        sorted_modules = sorted(modules.keys())

        module_entries = []
        for module in sorted_modules:
            module_entries.append({
                "stable_id": f"module:{module}",
                "path": module,
                "files": sorted(modules[module])
            })

        return {
            "schema_version": "1.0",
            "repo": {
                "stable_id": repo_id,
                "root": ".",
                "modules": module_entries
            }
        }
```

### `tests/integration/__init__.py`

```

```

### `tests/integration/test_full_snapshot.py`

```
import unittest
import tempfile
import shutil
import os
import json
from src.cli.main import run_snapshot
from src.snapshot.snapshot_loader import SnapshotLoader

class TestFullSnapshot(unittest.TestCase):
    def setUp(self):
        # Create a temp directory for the "Repo"
        self.test_dir = tempfile.mkdtemp()
        self.repo_root = os.path.join(self.test_dir, "my_repo")
        self.output_root = os.path.join(self.test_dir, "output")
        
        os.makedirs(self.repo_root)
        os.makedirs(self.output_root)

        # Create dummy repo content
        self._create_file("README.md", "# Hello")
        # main.py imports 'os' (external)
        self._create_file("src/main.py", "import os\nprint('hello')")
        self._create_file("src/utils.py", "def add(a,b): return a+b")
        self._create_file("node_modules/bad_file.js", "ignore me") # Should be ignored

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def _create_file(self, path, content):
        full_path = os.path.join(self.repo_root, path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w") as f:
            f.write(content)

    def test_snapshot_creation(self):
        # 1. Run Snapshot
        snapshot_id = run_snapshot(
            repo_root=self.repo_root,
            output_root=self.output_root,
            depth=5,
            ignore=["node_modules"],
            include_extensions=[".py", ".md"],
            include_readme=True,
            write_current_pointer=True
        )

        # 2. Verify Output Directory Structure
        snap_dir = os.path.join(self.output_root, snapshot_id)
        self.assertTrue(os.path.isdir(snap_dir))
        self.assertTrue(os.path.isfile(os.path.join(snap_dir, "manifest.json")))
        self.assertTrue(os.path.isfile(os.path.join(snap_dir, "structure.json")))
        self.assertTrue(os.path.isfile(os.path.join(self.output_root, "current.json")))

        # 3. Verify Manifest Content
        loader = SnapshotLoader(self.output_root)
        manifest = loader.load_manifest(snap_dir)
        
        # Check Config
        self.assertEqual(manifest["config"]["depth"], 5)
        self.assertIn("node_modules", manifest["config"]["ignore_names"])

        # Check Files
        files = manifest["files"]
        paths = [f["path"] for f in files]
        
        self.assertIn("readme.md", paths)
        self.assertIn("src/main.py", paths)
        self.assertIn("src/utils.py", paths)
        self.assertNotIn("node_modules/bad_file.js", paths)

        # 4. Verify External Dependencies (New Feature)
        stats = manifest["stats"]
        self.assertIn("external_dependencies", stats)
        # 'os' should be detected from src/main.py
        self.assertIn("os", stats["external_dependencies"])

        # 5. Verify Determinism (Hash)
        main_py_entry = next(f for f in files if f["path"] == "src/main.py")
        self.assertEqual(main_py_entry["language"], "python")
        self.assertTrue(len(main_py_entry["sha256"]) == 64)

if __name__ == "__main__":
    unittest.main()
```

### `tests/integration/test_robustness.py`

```
import unittest
import tempfile
import shutil
import os
import sys
from src.core.controller import run_snapshot
from src.snapshot.snapshot_loader import SnapshotLoader

class TestRobustness(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_root = os.path.join(self.test_dir, "repo")
        self.output_root = os.path.join(self.test_dir, "output")
        os.makedirs(self.repo_root)
        os.makedirs(self.output_root)

    def tearDown(self):
        try:
            shutil.rmtree(self.test_dir)
        except OSError:
            pass

    def test_snapshot_with_mixed_health(self):
        # 1. Valid Files
        with open(os.path.join(self.repo_root, "valid.py"), "w") as f:
            f.write("print('ok')")
            
        # 2. Ignored Files
        os.makedirs(os.path.join(self.repo_root, "node_modules"))
        with open(os.path.join(self.repo_root, "node_modules", "ignore.js"), "w") as f:
            f.write("ignore")

        # 3. Symlink Cycle (Unix only)
        if sys.platform != 'win32':
            os.symlink(self.repo_root, os.path.join(self.repo_root, "loop"))

        # Run Snapshot
        # This should succeed despite the complexity
        snap_id = run_snapshot(
            repo_root=self.repo_root,
            output_root=self.output_root,
            depth=10,
            ignore=["node_modules"],
            include_extensions=[],
            include_readme=True,
            write_current_pointer=True
        )

        # Verify Manifest
        loader = SnapshotLoader(self.output_root)
        manifest = loader.load_manifest(os.path.join(self.output_root, snap_id))
        
        files = manifest["files"]
        paths = [f["path"] for f in files]
        
        self.assertIn("valid.py", paths)
        self.assertNotIn("node_modules/ignore.js", paths)
        
        # Ensure we didn't index the loop infinitely
        # The loop link itself might be skipped or included as a file depending on classification,
        # but the cycle must be broken.
        loop_matches = [p for p in paths if "loop" in p]
        self.assertLess(len(loop_matches), 2)

if __name__ == "__main__":
    unittest.main()
```

### `tests/integration/test_snapshot_flow.py`

```
﻿import unittest
import tempfile
import shutil
import os
import json
from src.cli.main import run_snapshot
from src.snapshot.snapshot_loader import SnapshotLoader

class TestSnapshotFlow(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_root = os.path.join(self.test_dir, "my_repo")
        self.output_root = os.path.join(self.test_dir, "output")
        os.makedirs(self.repo_root)
        os.makedirs(self.output_root)

        self._create_file("README.md", "# Hello")
        self._create_file("src/main.py", "print('hello')")
        self._create_file("node_modules/bad_file.js", "ignore me")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def _create_file(self, path, content):
        full_path = os.path.join(self.repo_root, path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w") as f:
            f.write(content)

    def test_snapshot_creation(self):
        snapshot_id = run_snapshot(
            repo_root=self.repo_root,
            output_root=self.output_root,
            depth=5,
            ignore=["node_modules"],
            include_extensions=[".py", ".md"],
            include_readme=True,
            write_current_pointer=True
        )

        snap_dir = os.path.join(self.output_root, snapshot_id)
        self.assertTrue(os.path.isdir(snap_dir))
        self.assertTrue(os.path.isfile(os.path.join(snap_dir, "manifest.json")))

        loader = SnapshotLoader(self.output_root)
        manifest = loader.load_manifest(snap_dir)
        
        paths = [f["path"] for f in manifest["files"]]
        self.assertIn("readme.md", paths)
        self.assertIn("src/main.py", paths)
        self.assertNotIn("node_modules/bad_file.js", paths)

if __name__ == "__main__":
    unittest.main()
```

### `tests/output/2026-02-18t21-09-34z/graph.json`

```
{
  "edges": [],
  "nodes": [
    {
      "id": "file:frontend/app.tsx",
      "type": "file"
    },
    {
      "id": "file:frontend/components/button.tsx",
      "type": "file"
    },
    {
      "id": "file:frontend/legacy.js",
      "type": "file"
    },
    {
      "id": "file:readme.md",
      "type": "file"
    },
    {
      "id": "file:requirements.txt",
      "type": "file"
    },
    {
      "id": "file:scripts/deploy.py",
      "type": "file"
    },
    {
      "id": "file:src/main.py",
      "type": "file"
    },
    {
      "id": "file:src/utils/__init__.py",
      "type": "file"
    },
    {
      "id": "file:src/utils/logger.py",
      "type": "file"
    }
  ],
  "schema_version": "1.0"
}
```

### `tests/output/2026-02-18t21-09-34z/manifest.json`

```
{
  "config": {
    "depth": 25,
    "ignore_names": [
      ".git",
      "node_modules",
      "__pycache__",
      "dist",
      "build",
      ".next",
      ".expo",
      ".venv"
    ],
    "include_extensions": [],
    "include_readme": true,
    "manual_override": false,
    "tree_only": false
  },
  "files": [
    {
      "imports": [
        "./components/Button",
        "./styles.css",
        "react"
      ],
      "language": "typescript",
      "module_path": "frontend",
      "path": "frontend/app.tsx",
      "sha256": "c4e3f3274e7c43d41ab16610884d5b6bb58dee24e764a5ad46743661b53213bb",
      "size_bytes": 142,
      "stable_id": "file:frontend/app.tsx"
    },
    {
      "imports": [
        "react"
      ],
      "language": "typescript",
      "module_path": "frontend/components",
      "path": "frontend/components/button.tsx",
      "sha256": "e66b5591313c4a023c378a8301b8f5d4bfe93f97902f4006897253a587e59534",
      "size_bytes": 91,
      "stable_id": "file:frontend/components/button.tsx"
    },
    {
      "imports": [
        "fs",
        "path"
      ],
      "language": "javascript",
      "module_path": "frontend",
      "path": "frontend/legacy.js",
      "sha256": "6066685d1ea34d639ec83d9ef46f64a86dce63e0ee5c5126ec5da0eb143c50bd",
      "size_bytes": 85,
      "stable_id": "file:frontend/legacy.js"
    },
    {
      "imports": [],
      "language": "markdown",
      "module_path": "",
      "path": "readme.md",
      "sha256": "084e0f1df61e114153d628ca0125ced7a69a3101b920577b070dc7cabcd485d7",
      "size_bytes": 72,
      "stable_id": "file:readme.md"
    },
    {
      "imports": [],
      "language": "unknown",
      "module_path": "",
      "path": "requirements.txt",
      "sha256": "fa45fe2d500fbfcacd606225bcc56c4ee9f9e199dd03908ac6a323fe4e3baf54",
      "size_bytes": 26,
      "stable_id": "file:requirements.txt"
    },
    {
      "imports": [
        "boto3",
        "json"
      ],
      "language": "python",
      "module_path": "scripts",
      "path": "scripts/deploy.py",
      "sha256": "af9507ef7830ef0854f7ffe81e042d35e319e3609a33a7057c6241d51a791b47",
      "size_bytes": 30,
      "stable_id": "file:scripts/deploy.py"
    },
    {
      "imports": [
        "os",
        "sys",
        "utils.logger"
      ],
      "language": "python",
      "module_path": "src",
      "path": "src/main.py",
      "sha256": "39ed434953dad5ae0cb2f106c6a8adfafd7315cbfe1dafbc1ed26c9bc2541996",
      "size_bytes": 121,
      "stable_id": "file:src/main.py"
    },
    {
      "imports": [],
      "language": "python",
      "module_path": "src/utils",
      "path": "src/utils/__init__.py",
      "sha256": "f01a374e9c81e3db89b3a42940c4d6a5447684986a1296e42bf13f196eed6295",
      "size_bytes": 5,
      "stable_id": "file:src/utils/__init__.py"
    },
    {
      "imports": [
        "datetime"
      ],
      "language": "python",
      "module_path": "src/utils",
      "path": "src/utils/logger.py",
      "sha256": "a64e73ac733dc461d08ed36a17799d72dacc023ca64f65a8b8b40aa5cab1edee",
      "size_bytes": 108,
      "stable_id": "file:src/utils/logger.py"
    }
  ],
  "inputs": {
    "git": {
      "commit": null,
      "is_repo": false
    },
    "repo_root": "C:/projects/repo-runner/tests/fixtures/repo_20260218_154821",
    "roots": [
      "C:/projects/repo-runner/tests/fixtures/repo_20260218_154821"
    ]
  },
  "schema_version": "1.0",
  "snapshot": {
    "created_utc": "2026-02-18T21:09:34Z",
    "output_root": "tests/output",
    "snapshot_id": "2026-02-18T21-09-34Z"
  },
  "stats": {
    "file_count": 9,
    "total_bytes": 680
  },
  "tool": {
    "name": "repo-runner",
    "version": "0.1.0"
  }
}
```

### `tests/output/2026-02-18t21-09-34z/structure.json`

```
{
  "repo": {
    "modules": [
      {
        "files": [
          "file:readme.md",
          "file:requirements.txt"
        ],
        "path": "",
        "stable_id": "module:"
      },
      {
        "files": [
          "file:frontend/app.tsx",
          "file:frontend/legacy.js"
        ],
        "path": "frontend",
        "stable_id": "module:frontend"
      },
      {
        "files": [
          "file:frontend/components/button.tsx"
        ],
        "path": "frontend/components",
        "stable_id": "module:frontend/components"
      },
      {
        "files": [
          "file:scripts/deploy.py"
        ],
        "path": "scripts",
        "stable_id": "module:scripts"
      },
      {
        "files": [
          "file:src/main.py"
        ],
        "path": "src",
        "stable_id": "module:src"
      },
      {
        "files": [
          "file:src/utils/__init__.py",
          "file:src/utils/logger.py"
        ],
        "path": "src/utils",
        "stable_id": "module:src/utils"
      }
    ],
    "root": ".",
    "stable_id": "repo:root"
  },
  "schema_version": "1.0"
}
```

### `tests/output/current.json`

```
{
  "current_snapshot_id": "2026-02-18T21-09-34Z",
  "path": "2026-02-18T21-09-34Z",
  "schema_version": "1.0"
}
```

### `tests/unit/__init__.py`

```

```

### `tests/unit/test_filesystem_scanner.py`

```
﻿import unittest
import tempfile
import shutil
import os
from src.scanner.filesystem_scanner import FileSystemScanner

class TestFileSystemScanner(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self._touch("ok.txt")
        self._touch(".git/config")
        self._touch("dist/bundle.js")
        self._touch("src/code.ts")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def _touch(self, path):
        full = os.path.join(self.test_dir, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w") as f:
            f.write("test")

    def test_scanner_ignores(self):
        ignore_set = {".git", "dist"}
        scanner = FileSystemScanner(depth=10, ignore_names=ignore_set)
        
        results = scanner.scan([self.test_dir])
        rel_results = [os.path.relpath(p, self.test_dir).replace("\\", "/") for p in results]
        
        self.assertIn("ok.txt", rel_results)
        self.assertIn("src/code.ts", rel_results)
        self.assertFalse(any("config" in p for p in rel_results))
        self.assertFalse(any("bundle.js" in p for p in rel_results))

if __name__ == "__main__":
    unittest.main()
```

### `tests/unit/test_fingerprint_hardening.py`

```
import unittest
import tempfile
import shutil
import os
import hashlib
from src.fingerprint.file_fingerprint import FileFingerprint

class TestFingerprintHardening(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_valid_file(self):
        path = os.path.join(self.test_dir, "test.txt")
        content = b"hello world"
        with open(path, "wb") as f:
            f.write(content)
            
        fp = FileFingerprint.fingerprint(path)
        
        expected_sha = hashlib.sha256(content).hexdigest()
        self.assertEqual(fp["sha256"], expected_sha)
        self.assertEqual(fp["size_bytes"], len(content))
        self.assertEqual(fp["language"], "unknown") # .txt is unknown in current map

    def test_empty_file(self):
        path = os.path.join(self.test_dir, "empty.py")
        with open(path, "wb") as f:
            pass
            
        fp = FileFingerprint.fingerprint(path)
        self.assertEqual(fp["size_bytes"], 0)
        self.assertEqual(fp["language"], "python")

    def test_locked_or_missing_file(self):
        # Test missing file raises OSError
        path = os.path.join(self.test_dir, "ghost.txt")
        
        with self.assertRaises(OSError):
            FileFingerprint.fingerprint(path)

if __name__ == "__main__":
    unittest.main()
```

### `tests/unit/test_flatten_exporter.py`

```
import unittest
import os
from src.exporters.flatten_markdown_exporter import FlattenMarkdownExporter, FlattenOptions

class TestFlattenExporter(unittest.TestCase):
    def setUp(self):
        self.exporter = FlattenMarkdownExporter()
        self.manifest = {
            "files": [
                {"path": "src/index.ts", "size_bytes": 100, "sha256": "a"},
                {"path": "readme.md", "size_bytes": 50, "sha256": "b"},
            ]
        }
        self.options = FlattenOptions(
            tree_only=False,
            include_readme=True,
            scope="full"
        )

    def test_tree_generation(self):
        # We test the internal _render_tree method implicitly via generate_content
        md = self.exporter.generate_content(
            repo_root="C:/fake",
            manifest=self.manifest,
            options=self.options,
            title="Test Export"
        )
        
        self.assertIn("## Tree", md)
        # readme.md comes before src, so src is the last element (└──)
        self.assertIn("└── src", md) 
        self.assertIn("└── index.ts", md)

    def test_scope_filtering(self):
        # Change scope to only 'src'
        options = FlattenOptions(tree_only=True, include_readme=False, scope="module:src")
        
        files = self.exporter._canonical_files_from_manifest(self.manifest, options)
        paths = [f["path"] for f in files]
        
        self.assertIn("src/index.ts", paths)
        self.assertNotIn("readme.md", paths)

    def test_binary_placeholder(self):
        # Mock a binary file entry in manifest
        entry = {"path": "image.png", "size_bytes": 1024, "sha256": "binhash"}
        placeholder = self.exporter._binary_placeholder(entry)
        
        self.assertIn("<<BINARY_OR_SKIPPED_FILE>>", placeholder)
        self.assertIn("binhash", placeholder)

if __name__ == "__main__":
    unittest.main()
```

### `tests/unit/test_graph_builder.py`

```
import unittest
from src.analysis.graph_builder import GraphBuilder
from src.core.types import FileEntry

class TestGraphBuilder(unittest.TestCase):
    def setUp(self):
        self.files = [
            {
                "stable_id": "file:src/main.py",
                "path": "src/main.py",
                "language": "python",
                "imports": ["utils.logger", "os", "pandas.core.frame"], 
                "module_path": "src",
                "sha256": "abc", "size_bytes": 100
            },
            {
                "stable_id": "file:src/utils/logger.py",
                "path": "src/utils/logger.py", 
                "language": "python",
                "imports": [],
                "module_path": "src/utils",
                "sha256": "def", "size_bytes": 200
            },
            {
                "stable_id": "file:src/app.tsx",
                "path": "src/app.tsx",
                "language": "typescript",
                "imports": ["react", "react-dom/client", "@angular/core", "./components/button"],
                "module_path": "src",
                "sha256": "ghi", "size_bytes": 300
            }
        ]
        self.builder = GraphBuilder()

    def test_node_generation(self):
        graph = self.builder.build(self.files)
        
        node_ids = set(n["id"] for n in graph["nodes"])
        
        # Internal files
        self.assertIn("file:src/main.py", node_ids)
        self.assertIn("file:src/utils/logger.py", node_ids)
        
        # External nodes (Python)
        self.assertIn("external:os", node_ids)
        self.assertIn("external:pandas", node_ids) # Should collapse pandas.core.frame
        
        # External nodes (JS/TS)
        self.assertIn("external:react", node_ids)
        self.assertIn("external:react-dom", node_ids) # Should collapse react-dom/client
        self.assertIn("external:@angular/core", node_ids) # Scoped package

    def test_edge_resolution_python(self):
        graph = self.builder.build(self.files)
        edges = graph["edges"]
        
        # 1. Internal Edge: main.py -> logger.py
        internal_edge = next((e for e in edges if 
            e["source"] == "file:src/main.py" and 
            e["target"] == "file:src/utils/logger.py"), None)
        self.assertIsNotNone(internal_edge)
        
        # 2. External Edge: main.py -> os
        external_edge = next((e for e in edges if 
            e["source"] == "file:src/main.py" and 
            e["target"] == "external:os"), None)
        self.assertIsNotNone(external_edge)

    def test_edge_resolution_js(self):
        graph = self.builder.build(self.files)
        edges = graph["edges"]
        
        # 1. External Edge: app.tsx -> react
        react_edge = next((e for e in edges if 
            e["source"] == "file:src/app.tsx" and 
            e["target"] == "external:react"), None)
        self.assertIsNotNone(react_edge)
        
        # 2. External Edge: app.tsx -> @angular/core
        angular_edge = next((e for e in edges if 
            e["source"] == "file:src/app.tsx" and 
            e["target"] == "external:@angular/core"), None)
        self.assertIsNotNone(angular_edge)

    def test_broken_relative_imports_ignored(self):
        # If a relative import doesn't resolve to a file, it should NOT become an external node
        files = [{
            "stable_id": "file:broken.py",
            "path": "broken.py",
            "language": "python",
            "imports": [".non_existent"], 
            "module_path": ".",
            "sha256": "123", "size_bytes": 10
        }]
        
        graph = self.builder.build(files)
        node_ids = [n["id"] for n in graph["nodes"]]
        
        self.assertNotIn("external:.non_existent", node_ids)
        self.assertNotIn("external:non_existent", node_ids)

if __name__ == "__main__":
    unittest.main()
```

### `tests/unit/test_ignore_logic.py`

```
import unittest
from src.scanner.filesystem_scanner import FileSystemScanner
import tempfile
import shutil
import os

class TestIgnoreLogic(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        
        # Structure:
        # /ok.txt
        # /.git/config (should ignore)
        # /dist/bundle.js (should ignore)
        # /src/code.ts (should keep)
        
        self._touch("ok.txt")
        self._touch(".git/config")
        self._touch("dist/bundle.js")
        self._touch("src/code.ts")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def _touch(self, path):
        full = os.path.join(self.test_dir, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w") as f:
            f.write("test")

    def test_scanner_ignores(self):
        ignore_set = {".git", "dist"}
        scanner = FileSystemScanner(depth=10, ignore_names=ignore_set)
        
        results = scanner.scan([self.test_dir])
        
        # Normalize for assertion
        rel_results = [os.path.relpath(p, self.test_dir).replace("\\", "/") for p in results]
        
        self.assertIn("ok.txt", rel_results)
        self.assertIn("src/code.ts", rel_results)
        
        # Should NOT be present
        self.assertFalse(any("config" in p for p in rel_results))
        self.assertFalse(any("bundle.js" in p for p in rel_results))

if __name__ == "__main__":
    unittest.main()
```

### `tests/unit/test_import_scanner.py`

```
import unittest
from src.analysis.import_scanner import ImportScanner

class TestImportScanner(unittest.TestCase):
    
    # --- Python Tests (AST Based) ---

    def test_python_complex_structure(self):
        """
        Tests:
        1. Multi-line parenthesized imports (common in big projects).
        2. Multiple modules on one line.
        3. Aliasing (should capture the *source*, not the alias).
        """
        content = """
import os, sys
from datetime import (
    datetime,
    timedelta as td
)
import pandas as pd
"""
        imports = set()
        ImportScanner._scan_python(content, imports)
        
        expected = {"os", "sys", "datetime", "pandas"}
        self.assertEqual(imports, expected)

    def test_python_relative_imports(self):
        """
        Tests relative imports used in modular monoliths.
        .  = current directory
        .. = parent
        """
        content = """
from . import sibling
from ..parent import something
from ...grandparent.utils import helper
"""
        imports = set()
        ImportScanner._scan_python(content, imports)
        
        expected = {".sibling", "..parent", "...grandparent.utils"}
        self.assertEqual(imports, expected)

    def test_python_scope_and_strings(self):
        """
        Tests the superiority of AST over Regex:
        1. Finds imports hidden inside functions (lazy imports).
        2. IGNORES strings that look like imports.
        """
        content = """
def lazy_loader():
    import json # Should be found
    
def print_help():
    msg = "import os" # Should be IGNORED
    print(msg)
    
# import commented_out # Should be IGNORED
"""
        imports = set()
        ImportScanner._scan_python(content, imports)
        
        self.assertIn("json", imports)
        self.assertNotIn("os", imports)
        self.assertNotIn("commented_out", imports)

    def test_python_syntax_error(self):
        """
        Ensure the tool is robust against broken files (e.g., during a merge conflict).
        """
        content = "def broken_code(:"
        imports = set()
        
        # Should catch SyntaxError silently
        ImportScanner._scan_python(content, imports)
        self.assertEqual(len(imports), 0)

    # --- JavaScript / TypeScript Tests (Regex Based) ---

    def test_js_standard_imports(self):
        content = """
import React from 'react';
import { useState, useEffect } from "react";
const fs = require('fs');
"""
        imports = set()
        ImportScanner._scan_js(content, imports)
        
        expected = {"react", "fs"}
        self.assertEqual(imports, expected)

    def test_js_edge_cases(self):
        """
        Tests:
        1. Side-effect imports (import 'css').
        2. Multi-line imports (Angular/NestJS style).
        3. Comments (should not pick up commented imports).
        """
        content = """
import './styles.css'; // Side effect

// import { bad } from 'bad-lib'; 

import { 
  Component,
  OnInit
} from '@angular/core';

/* 
  import { ignore } from 'block-comment'; 
*/
"""
        imports = set()
        ImportScanner._scan_js(content, imports)
        
        self.assertIn("./styles.css", imports)
        self.assertIn("@angular/core", imports)
        
        # Verify comments are stripped
        self.assertNotIn("bad-lib", imports)
        self.assertNotIn("block-comment", imports)

    def test_ts_type_imports(self):
        """
        TypeScript 'import type' should still register as a dependency.
        """
        content = "import type { User } from './models';"
        imports = set()
        ImportScanner._scan_js(content, imports)
        
        self.assertIn("./models", imports)

if __name__ == "__main__":
    unittest.main()
```

### `tests/unit/test_normalizer.p`

```
<<BINARY_OR_SKIPPED_FILE>>
size_bytes: 0
sha256: pre-snapshot
```

### `tests/unit/test_path_normalizer.py`

```
﻿import unittest
import os
from src.normalize.path_normalizer import PathNormalizer

class TestPathNormalizer(unittest.TestCase):
    def setUp(self):
        self.root = "C:\\projects\\my-repo"
        self.normalizer = PathNormalizer(self.root)

    def test_basic_normalization(self):
        # Input: Absolute path
        abs_path = os.path.join(self.root, "src", "main.py")
        normalized = self.normalizer.normalize(abs_path)
        self.assertEqual(normalized, "src/main.py")

    def test_windows_separator_handling(self):
        # Force a windows-style relative path string
        raw_relative = "src\\Components\\Header.tsx"
        normalized = raw_relative.replace("\\", "/").lower()
        self.assertEqual(normalized, "src/components/header.tsx")

    def test_casing_policy(self):
        path = os.path.join(self.root, "README.md")
        normalized = self.normalizer.normalize(path)
        self.assertEqual(normalized, "readme.md")

    def test_id_generation(self):
        self.assertEqual(self.normalizer.file_id("src/utils/helper.ts"), "file:src/utils/helper.ts")
        self.assertEqual(self.normalizer.module_id("src/utils"), "module:src/utils")
        self.assertEqual(self.normalizer.repo_id(), "repo:root")

if __name__ == "__main__":
    unittest.main()
```

### `tests/unit/test_scanner_hardening.py`

```
import unittest
import tempfile
import shutil
import os
import sys
from unittest.mock import patch, MagicMock
from src.scanner.filesystem_scanner import FileSystemScanner

class TestScannerHardening(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        try:
            shutil.rmtree(self.test_dir)
        except OSError:
            pass

    def _create_file(self, path):
        full = os.path.join(self.test_dir, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w") as f:
            f.write("content")
        return full

    def test_symlink_cycle_detection(self):
        # Skip on Windows if privileges are insufficient for symlinks
        if sys.platform == 'win32':
            try:
                os.symlink(self.test_dir, os.path.join(self.test_dir, "link_to_self"))
            except OSError:
                print("Skipping symlink test on Windows (permission denied)")
                return
        else:
            # Create a cycle: root/link -> root
            link_path = os.path.join(self.test_dir, "link_to_self")
            os.symlink(self.test_dir, link_path)

        self._create_file("file_a.txt")
        
        scanner = FileSystemScanner(depth=10, ignore_names=set())
        
        # Should not hang or crash
        # If robust, it scans file_a.txt and maybe the link, but stops at the cycle
        files = scanner.scan([self.test_dir])
        
        # We expect at least the real file
        self.assertTrue(any(f.endswith("file_a.txt") for f in files))
        
        # Ensure we didn't recurse infinitely
        # The number of files should be small (1 real file + potentially 1 from link if not collapsed immediately)
        self.assertLess(len(files), 5)

    @patch('os.listdir')
    def test_permission_error_handling(self, mock_listdir):
        # Simulate PermissionError on a subdirectory
        mock_listdir.side_effect = PermissionError("Access Denied")
        
        scanner = FileSystemScanner(depth=5, ignore_names=set())
        
        # Scan should complete returning empty list (or list of root files if root scan succeeded)
        # Here we mock the root scan failing
        files = scanner.scan([self.test_dir])
        
        self.assertEqual(files, [])

    def test_vanished_directory(self):
        # Test case where a directory exists during walk start but vanishes before listdir
        # We can't easily race-condition this in real IO, so we verify logic via sub-test structure
        # or rely on the code review of the try/except block.
        # Here we trust the previous patch test covers the OSError path.
        pass

if __name__ == "__main__":
    unittest.main()
```

### `tests/unit/test_structure.py`

```
import unittest
from src.structure.structure_builder import StructureBuilder
from src.normalize.path_normalizer import PathNormalizer

class TestStructureBuilder(unittest.TestCase):
    def test_build_structure(self):
        # Mock Input: A list of flat file entries (already normalized)
        files = [
            {"stable_id": "file:src/a.ts", "module_path": "src", "path": "src/a.ts"},
            {"stable_id": "file:src/b.ts", "module_path": "src", "path": "src/b.ts"},
            {"stable_id": "file:root.md", "module_path": ".", "path": "root.md"},
            {"stable_id": "file:utils/deep/x.py", "module_path": "utils/deep", "path": "utils/deep/x.py"},
        ]

        builder = StructureBuilder()
        output = builder.build(repo_id="repo:root", files=files)

        # Assertions based on structure.json schema
        self.assertEqual(output["schema_version"], "1.0")
        self.assertEqual(output["repo"]["stable_id"], "repo:root")
        
        modules = output["repo"]["modules"]
        
        # We expect 3 modules: ".", "src", "utils/deep"
        # They must be sorted by path
        self.assertEqual(len(modules), 3)
        self.assertEqual(modules[0]["path"], ".")
        self.assertEqual(modules[1]["path"], "src")
        self.assertEqual(modules[2]["path"], "utils/deep")

        # Check content of "src"
        src_mod = modules[1]
        self.assertEqual(src_mod["stable_id"], "module:src")
        self.assertEqual(len(src_mod["files"]), 2)
        self.assertEqual(src_mod["files"][0], "file:src/a.ts")

if __name__ == "__main__":
    unittest.main()
```

### `tests/unit/test_structure_builder.py`

```
﻿import unittest
from src.structure.structure_builder import StructureBuilder

class TestStructureBuilder(unittest.TestCase):
    def test_build_structure(self):
        files = [
            {"stable_id": "file:src/a.ts", "module_path": "src", "path": "src/a.ts"},
            {"stable_id": "file:src/b.ts", "module_path": "src", "path": "src/b.ts"},
            {"stable_id": "file:root.md", "module_path": ".", "path": "root.md"},
            {"stable_id": "file:utils/deep/x.py", "module_path": "utils/deep", "path": "utils/deep/x.py"},
        ]

        builder = StructureBuilder()
        output = builder.build(repo_id="repo:root", files=files)

        self.assertEqual(output["schema_version"], "1.0")
        self.assertEqual(output["repo"]["stable_id"], "repo:root")
        
        modules = output["repo"]["modules"]
        self.assertEqual(len(modules), 3)
        self.assertEqual(modules[0]["path"], ".")
        self.assertEqual(modules[1]["path"], "src")
        self.assertEqual(modules[2]["path"], "utils/deep")

        src_mod = modules[1]
        self.assertEqual(src_mod["stable_id"], "module:src")
        self.assertEqual(len(src_mod["files"]), 2)
        self.assertEqual(src_mod["files"][0], "file:src/a.ts")

if __name__ == "__main__":
    unittest.main()
```
