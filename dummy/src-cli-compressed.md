# Module: src/cli

> *Direct compressed architectural slice, excluding raw implementation code.*

## Module Directory Tree

```text
.
└── src/
    └── cli/
        ├── __init__.py
        └── main.py
```

---

### `src/cli/__init__.py`
**Role:** Serves as a Python package initialization marker for the command-line interface module, allowing its internal components to be imported across the application.
**Key Interfaces:**
- None
**Dependencies:** None

---

### `src/cli/main.py`
**Role:** Acts as the primary Command Line Interface router, mapping user CLI arguments to specific core business logic controllers.
**Key Interfaces:**
- `main(): None` - Parses system CLI arguments and triggers the corresponding core service operations (snapshot, diff, slice, diagram, export, ui).
**Dependencies:** argparse, os, sys, src.core.controller, src.core.config_loader, src.gui.app

---

