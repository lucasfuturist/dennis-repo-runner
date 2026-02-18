# Quick Export: repo-runner

- repo_root: `C:/projects/repo-runner`
- snapshot_id: `QUICK_EXPORT_PREVIEW`
- file_count: `33`
- tree_only: `False`
## Tree

```
├── .gitignore
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
│   └── package-repo.ps1
└── src
    ├── __init__.py
    ├── cli
    │   ├── __init__.py
    │   └── main.py
    ├── entry_point.py
    ├── exporters
    │   └── flatten_markdown_exporter.py
    ├── fingerprint
    │   └── file_fingerprint.py
    ├── gui
    │   ├── __init__.py
    │   ├── app.py
    │   └── components
    │       ├── config_tabs.py
    │       ├── export_preview.py
    │       ├── preview_pane.py
    │       └── tree_view.py
    ├── normalize
    │   └── path_normalizer.py
    ├── scanner
    │   └── filesystem_scanner.py
    ├── snapshot
    │   ├── snapshot_loader.py
    │   └── snapshot_writer.py
    └── structure
        └── structure_builder.py
```

## File Contents

### `.gitignore`

```
<<BINARY_OR_SKIPPED_FILE>>
size_bytes: 0
sha256: pre-snapshot
```

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
Good. This is the moment to formalize it properly.

Below is a clean, production-grade `README.md` for **repo-runner v0.1** reflecting:

* snapshot-first architecture
* deterministic guarantees
* flatten exporter (list_tree replacement)
* current snapshot defaulting
* strict separation from Dennis

You can drop this directly into the repo root.

---

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

### `src/cli/__init__.py`

```

```

### `src/cli/main.py`

```
﻿import argparse
import os
from typing import List, Optional

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
) -> str:
    """
    Creates a snapshot.
    If explicit_file_list is provided, it skips the directory scan and uses that exact list.
    """
    repo_root_abs = os.path.abspath(repo_root)

    if explicit_file_list is not None:
        # UI Override Mode: Use the list exactly as provided
        absolute_files = [os.path.abspath(f) for f in explicit_file_list]
    else:
        # CLI / Default Mode: Scan the disk
        scanner = FileSystemScanner(depth=depth, ignore_names=set(ignore))
        absolute_files = scanner.scan([repo_root_abs])
        absolute_files = _filter_by_extensions(absolute_files, include_extensions)

    normalizer = PathNormalizer(repo_root_abs)
    file_entries = []
    total_bytes = 0
    seen_ids = set()

    for abs_path in absolute_files:
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
        
        # Fingerprint might fail if file was deleted between scan and click
        try:
            fp = FileFingerprint.fingerprint(abs_path)
            total_bytes += fp["size_bytes"]
            
            file_entries.append(
                {
                    "stable_id": stable_id,
                    "path": normalized,
                    "module_path": module_path,
                    **fp,
                }
            )
        except OSError:
            # If a file is unreadable or deleted, we skip it
            continue

    file_entries = sorted(file_entries, key=lambda x: x["path"])

    structure = StructureBuilder().build(
        repo_id=PathNormalizer.repo_id(),
        files=file_entries,
    )

    manifest = {
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
        },
        "files": file_entries,
    }

    writer = SnapshotWriter(output_root)
    snapshot_id = writer.write(
        manifest,
        structure,
        write_current_pointer=write_current_pointer,
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
        sha = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha.update(chunk)

        size = os.path.getsize(path)
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
from src.cli.main import run_snapshot
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

class PreviewPanel(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        
        # Metadata Header
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
            fp = FileFingerprint.fingerprint(abs_path)
            self.lbl_meta.config(text=f" ID: {stable_id}  |  Size: {fp['size_bytes']}B  |  Lang: {fp['language']}  |  SHA: {fp['sha256'][:12]}")
            
            if fp['size_bytes'] > 250_000:
                self.text_preview.insert("1.0", "<< File too large for preview >>")
            else:
                with open(abs_path, 'r', encoding='utf-8', errors='replace') as f:
                    self.text_preview.insert("1.0", f.read())
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
            if vals[0] == "☑":
                tags = self.tree.item(item_id, "tags")
                if tags and tags[0] != "folder":
                    paths.append(tags[0])
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

        for root in root_paths:
            if os.path.isfile(root):
                all_files.append(os.path.abspath(root))
                continue

            root = os.path.abspath(root)
            all_files.extend(self._walk(root, current_depth=0))

        return sorted(all_files)

    def _walk(self, directory: str, current_depth: int) -> List[str]:
        if self.depth >= 0 and current_depth > self.depth:
            return []

        results = []

        try:
            entries = sorted(os.listdir(directory))
        except OSError:
            return []

        for entry in entries:
            if entry in self.ignore_names:
                continue

            full_path = os.path.join(directory, entry)

            if os.path.isdir(full_path):
                results.extend(self._walk(full_path, current_depth + 1))
            elif os.path.isfile(full_path):
                results.append(os.path.abspath(full_path))

        return results
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

        with open(os.path.join(snapshot_dir, "manifest.json"), "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, sort_keys=True)

        with open(os.path.join(snapshot_dir, "structure.json"), "w", encoding="utf-8") as f:
            json.dump(structure, f, indent=2, sort_keys=True)

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
