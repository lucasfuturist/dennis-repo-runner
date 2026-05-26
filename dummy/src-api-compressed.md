# Module: src/api

> *Direct compressed architectural slice, excluding raw implementation code.*

## Module Directory Tree

```text
.
└── src/
    └── api/
        ├── init.py
        └── server.py
```

---

### `src/api/init.py`
**Role:** Initializes the API package and marks the directory as a Python module.
**Key Interfaces:** None
**Dependencies:** None

---

### src/api/server.py
**Role:** Acts as the primary HTTP REST controller that delegates repository ingestion, graph-based context slicing, and structural diffing to the core engine and analysis services.
**Key Interfaces:**
- `SnapshotRequest` - Pydantic model defining configuration parameters for triggering a repository scan and graph build.
- `SliceRequest` - Pydantic model defining parameters (focus, radius, token limits) to extract a sub-graph context slice.
- `CompareRequest` - Pydantic model specifying base and target snapshot identifiers for deterministic diffing.
- `create_snapshot(req: SnapshotRequest): dict` - API endpoint that accepts ingestion parameters and returns the newly generated snapshot ID and status.
- `slice_snapshot(snapshot_id: str, req: SliceRequest): dict` - API endpoint that returns a localized dependency graph slice along with formatted token telemetry.
- `compare_snapshots(req: CompareRequest): SnapshotDiffReport` - API endpoint that evaluates and returns the structural and dependency drift between two snapshots.
- `app / FastAPI` - The primary ASGI application instance exporting the registered routes.
**Dependencies:** os, json, fastapi, pydantic, typing, src.core.controller, src.snapshot.snapshot_loader, src.analysis.context_slicer, src.analysis.snapshot_comparator, src.observability.token_telemetry, src.core.types

---

