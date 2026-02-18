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