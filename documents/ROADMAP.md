# ROADMAP.md

# Roadmap

This roadmap is intentionally staged to preserve determinism and keep complexity layered.

## v0.1 — Structure + Fingerprints (Complete)

- [x] structure.json (repo/module/file containment)
- [x] manifest.json (config + file hashes)
- [x] append-only snapshots
- [x] optional exports (flatten.md)

## v0.1.5 — Schema Assurance & Graph Hardening (Complete)

- [x] **Migrate `src/core/types.py` to Pydantic**
  - Enforce strict typing for `FileEntry` and `Manifest` at the class level
  - Implement runtime validators for normalized paths (lowercase, forward-slash)
- [x] **Integration with "Dennis" Context Engine**
  - Verify structured output validation against AllSpice-style requirements
- [x] **Graph Hardening**
  - Formalized cycle detection (`has_cycles` flag)
  - Hardened JS/TS Regex against greedy matching

## v0.2 — Semantic Graph Layer (Complete)

- [x] **Basic AST-based import scanning (Python)**
  - `src/analysis/import_scanner.py`
- [x] **Regex-based import scanning (JS/TS)**
  - `src/analysis/import_scanner.py`
- [x] **Graph Construction** (`graph.json`)
  - `src/analysis/graph_builder.py`
- [x] **Symbol Extraction**
  - `symbols.json` global index
  - `symbols` list per file in manifest
- [x] **Context Slicing**
  - Slice by `symbol:{name}`
  - Language-aware token budgeting (Python ~3.5 chars/token vs MD ~4.5)

## v0.3 — Graph Canonicalization (Next Focus)

- [ ] stable external IDs (e.g., `external:pydantic` vs `external:src`)
- [ ] full determinism audit for graph edges across OS boundaries
- [ ] cycle handling policy (warn vs fail)
- [ ] support for `external_deps.json` (package usage stats)

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