# LANGUAGE_SUPPORT.md

# Language Support (v0.2)

In v0.2, language support includes extension-based detection and language-aware token estimation.

## Detection Rules

- language is derived from file extension.
- mapping is configured internally or via a simple mapping table.

Example mapping (illustrative):
- .ts, .tsx, .js, .jsx -> "typescript" or "javascript"
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
- .json -> "json"

## Token Weighting (New in v0.2)

To prevent context overflow in LLMs, `repo-runner` uses language-specific character-to-token ratios. Code is denser than prose, so it "costs" more characters per token.

| Language | Ratio (Chars/Token) |
| :--- | :--- |
| Python | 3.5 |
| JS/TS | 3.8 |
| Java/Go/Rust | 3.6 - 3.7 |
| HTML/CSS | 4.2 |
| Markdown | 4.5 |
| JSON | 4.0 |
| Unknown | 4.0 |

## Symbol Extraction

v0.2 supports regex/AST-based symbol extraction for:
- **Python:** Classes, Functions (AST)
- **JavaScript/TypeScript:** Classes, Functions, Const Arrows (Regex)

## Policy

- Unknown extensions should be labeled "unknown" and may still be included if allowed by include_extensions.
- README inclusion is controlled separately by include_readme.

## Future (v0.3+)

- Support for Rust/Go AST parsing.
- Support for complex symbol resolution (e.g., method vs function).