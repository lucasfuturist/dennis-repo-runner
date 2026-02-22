### `repo-runner` High-Resolution Interface Map

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
**Role:** Orchestrates the compilation of the Python source code into a single-file Windows executable using PyInstaller.
**Key Exports:**
- `Force-Delete(Path): void` - Safely removes build artifacts, falling back to CMD for deep-path issues.
- `$ExePath` - Configures the final destination path for the generated `repo-runner.exe`.
**Dependencies:** `PyInstaller` (External), `src/entry_point.py` (Internal)

### `scripts/export-signal.ps1`
**Role:** Generates a "signal" export consisting of a flattened Markdown file (containing all code) and a ZIP archive based on configurable glob patterns.
**Key Exports:**
- `RelPath(RepoRoot, AbsPath): string` - Calculates repository-relative paths for consistent mapping.
- `ToForwardSlashes(Path): string` - Normalizes path separators for cross-platform compatibility in exports.
- `$IncludeGlobs` - Configures the default set of file patterns to include in the context export.
- `$ExcludeDirs` / `$ExcludeExts` - Defines the architectural boundaries for what constitutes "noise" (e.g., `.git`, `node_modules`, images).
**Dependencies:** System.IO, System.Text.StringBuilder

### `scripts/generate_test_repo.ps1`
**Role:** Programmatically constructs a mock repository with Python, TypeScript, and config files to validate the runner's scanning and snapshotting capabilities.
**Key Exports:**
- `New-File(RelPath, Content): void` - Utility to simulate file creation within the generated fixture.
- `$AbsRepoPath` - State representing the location of the dynamically generated test repository.
- `$SkipSnapshot` - Config toggle to determine if the script should trigger the internal CLI after generation.
**Dependencies:** `src.cli.main` (Internal Python Module)

### `scripts/package-repo.ps1`
**Role:** Creates a clean, distribution-ready copy of the entire repository by mirroring the source to a target directory and zipping the results.
**Key Exports:**
- `Start-Heartbeat(Message): Job` - Manages a background process to provide visual feedback during long-running IO operations.
- `$ExcludeDirs` / `$ExcludeFiles` - Configures the blacklist for packaging (e.g., `__pycache__`, `dist`).
- `$CopyOut` / `$ZipOut` - Defines the destination paths for the mirrored folder and the final archive.
**Dependencies:** `robocopy` (External OS Utility)