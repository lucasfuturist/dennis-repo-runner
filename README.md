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
