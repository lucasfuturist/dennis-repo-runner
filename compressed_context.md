# Codebase Architectural Context

> *This document contains high-resolution structural maps of the codebase, compressed to exclude implementation logic.*

## Directory Tree

```text
.
└── src/
    └── core/
        └── config_loader.py
```

---

### `src/core/config_loader.py`
**Role:** Responsible for locating, parsing, and validating the project configuration file into a typed domain model.
**Key Interfaces:**
- `ConfigLoader` - Class encapsulating the resolution and loading of the project configuration.
- `load_config(repo_root: str): RepoRunnerConfig` - Takes a repository root directory path and returns the resolved configuration object, providing a default if unavailable.
- `CONFIG_FILENAME` - Constant defining the target configuration file name (`repo-runner.json`).
**Dependencies:** `os`, `json`, `typing`, `src.core.types.RepoRunnerConfig`

---

