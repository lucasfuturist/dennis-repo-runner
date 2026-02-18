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