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