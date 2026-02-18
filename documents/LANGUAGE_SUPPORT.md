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