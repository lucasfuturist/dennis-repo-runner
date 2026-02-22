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