### `repo-runner` Scripts Module: High-Resolution Interface Map

## The Tree
```
└── scripts
    ├── build_exe.ps1
    ├── export-signal.ps1
    ├── generate_test_repo.ps1
    └── package-repo.ps1
```

## File Summaries

### `scripts/build_exe.ps1`
**Role:** Orchestrates the compilation of the Python source code into a standalone Windows executable.
**Key Exports:**
- `dist/repo-runner.exe` - The primary production artifact containing the bundled application.
- `$ErrorActionPreference` - Set to `Stop` to ensure build pipeline termination on failure.
**Dependencies:** `pyinstaller` (external CLI), `src/entry_point.py` (internal entry).

### `scripts/export-signal.ps1`
**Role:** Aggregates repository source code and documentation into a single flattened Markdown file and a ZIP archive for LLM context or portability.
**Key Exports:**
- `$IncludeGlobs` - Defines the whitelist of architectural files (Markdown, Python, PowerShell, JSON, etc.).
- `$ExcludeDirs` / `$ExcludeExts` - Global blacklist for build artifacts (`dist`, `node_modules`, `.venv`) and binary assets.
- `flatten-signal.md` - A high-resolution text representation of the entire codebase.
- `signal.zip` - A compressed archive containing the filtered source tree.
**Dependencies:** None (Self-contained logic).

### `scripts/generate_test_repo.ps1` (Test File)
**Role:** Programmatically generates a mock polyglot repository (Python, TSX, JS) to serve as a fixture for integration testing and snapshot validation.
**Key Exports:**
- `$BasePath` - Default directory for test fixtures (`tests\fixtures`).
- `repo_[timestamp]` - A generated directory structure containing synthetic source files and imports.
- `output/` - Nested directory within the fixture containing the results of a test snapshot run.
**Dependencies:** `src.cli.main` (Invoked via Python to validate the generated repo).

### `scripts/package-repo.ps1`
**Role:** Creates a clean, distributable copy and ZIP archive of the repository using Robocopy for deterministic file handling.
**Key Exports:**
- `$CopyFolderName` - Name of the temporary clean directory (`repo-copy`).
- `$ZipFileName` - Name of the final distribution archive (`repo-runner.zip`).
- `$ExcludeDirs` - List of directories omitted from the package (`.git`, `dist`, `__pycache__`).
- `robocopy.log` - Detailed audit log of the packaging process.
**Dependencies:** `robocopy.exe` (System dependency).