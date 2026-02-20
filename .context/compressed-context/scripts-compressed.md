## 1. The Tree

```
└── scripts
    ├── build_exe.ps1
    ├── export-signal.ps1
    ├── generate_test_repo.ps1
    └── package-repo.ps1
```

## 2. File Summaries

### `scripts/build_exe.ps1`
**Role:** Automates the compilation of the `repo-runner` Python application into a standalone Windows executable using PyInstaller.
**Key Exports:**
- `Force-Delete($Path)` - Recursively removes stubborn build/dist directories using standard PowerShell or `cmd.exe` fallbacks.
- `python -m PyInstaller` - Triggers the build process with configurations for a single-file console app including all `src` modules.
**Dependencies:** `PyInstaller`, `src/entry_point.py`.

### `scripts/export-signal.ps1`
**Role:** Generates a deterministic flattened markdown export and a compressed ZIP archive of the repository source for external analysis.
**Key Exports:**
- `$FlattenOut` - Defines the path for the generated `flatten-signal.md` containing the full file list and UTF8 contents.
- `$ZipOut` - Defines the path for the `signal.zip` archive containing the same filtered file set.
- `ToForwardSlashes($Path)` - Ensures path strings in the export use canonical forward-slash separators.
**Dependencies:** `System.Text.StringBuilder`, `Compress-Archive`.

### `scripts/generate_test_repo.ps1`
**Role:** Scaffolds a multi-language (Python, TS, JS) temporary repository to provide a realistic target for integration testing.
**Key Exports:**
- `New-File($RelPath, $Content)` - Creates directory structures and writes UTF8-encoded files (with BOM) to the test path.
- `python -m src.cli.main snapshot` - Optionally executes the core snapshot pipeline on the newly generated test data.
**Dependencies:** `src.cli.main`.

### `scripts/package-repo.ps1`
**Role:** Creates a sanitized "clean" distribution copy of the repository by stripping build artifacts, git metadata, and cache files.
**Key Exports:**
- `robocopy` - Performs a deterministic, multi-threaded folder clone excluding specified directories like `.git` and `dist`.
- `Compress-Archive` - Packages the filtered file set into a project ZIP file.
- `Start-Heartbeat($Message)` - Spawns a background job to provide progress signals during long-running copy operations.
**Dependencies:** `robocopy`, `Compress-Archive`.