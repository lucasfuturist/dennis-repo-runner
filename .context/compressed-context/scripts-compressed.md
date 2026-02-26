# High-Resolution Interface Map: `repo-runner` (Scripts)

## 1. The Tree

```
└── scripts
    ├── build_exe.ps1
    ├── export-signal.ps1
    ├── package-repo.ps1
    └── verify.ps1
```

## 2. File Summaries

### `scripts/build_exe.ps1`
**Role:** Automates the PyInstaller compilation process to turn the Python source into a standalone Windows executable.
**Key Exports:**
- *Script Execution* - Cleans `dist/` folder, runs `python -m PyInstaller` against `src/entry_point.py`, and verifies the resulting `.exe`.
**Dependencies:** `PyInstaller`, `src/entry_point.py`

### `scripts/export-signal.ps1`
**Role:** Generates a filtered "signal" export (Markdown + ZIP) of the codebase for context sharing or documentation.
**Key Exports:**
- `Param($OutDir)` - Target directory for artifacts.
- `Param($IncludeGlobs)` - List of patterns to include (defaults to src, tests, docs).
- `Param($ExcludeDirs)` - List of patterns to ignore (defaults to .git, node_modules).
**Dependencies:** `PowerShell Core`

### `scripts/package-repo.ps1`
**Role:** Creates a clean distribution artifact of the repository by mirroring source files and excluding git/build metadata.
**Key Exports:**
- `Param($OutDir)` - Target root for the package.
- `Param($ZipFileName)` - Name of the compressed archive.
- `Param($ExcludeDirs)` - Directories to strip from the distribution.
**Dependencies:** `robocopy`, `Compress-Archive`

### `scripts/verify.ps1`
**Role:** The "Definition of Done" enforcement script that executes the full test suite.
**Key Exports:**
- *Script Execution* - Runs `python -m pytest` with strict error checking and verbose reporting.
**Dependencies:** `python`, `pytest`