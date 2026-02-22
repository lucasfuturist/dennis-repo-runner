# Quick Export: repo-runner

- repo_root: `C:/projects/repo-runner`
- snapshot_id: `QUICK_EXPORT_PREVIEW`
- file_count: `100`
- tree_only: `True`
## Tree

```
├── .context
│   ├── .dev-prompts
│   │   ├── .context-compressor-prompt.md
│   │   ├── commands.md
│   │   ├── compressed
│   │   │   ├── 00-compressed-codebase-ingest-prompt.md
│   │   │   ├── 01-next-steps-prompt.md
│   │   │   ├── 02-requested-files.md
│   │   │   └── 03-code-conventions-prompt.md
│   │   ├── raw
│   │   │   ├── 00-raw-codebase-ingest-prompt.md
│   │   │   ├── 01-next-steps-prompt.md
│   │   │   └── 02-code-conventions-prompt.md
│   │   └── repo-runner-flattened.md
│   ├── compressed-context
│   │   ├── all-documents.md
│   │   ├── full-tree.md
│   │   ├── scripts-compressed.md
│   │   ├── src-compressed.md
│   │   └── tests-compressed.md
│   └── repo-runner-flattened.md
├── .gitignore
├── clean_test.py
├── documents
│   ├── architecture.md
│   ├── config_spec.md
│   ├── contributing.md
│   ├── determinism_rules.md
│   ├── id_spec.md
│   ├── language_support.md
│   ├── repo_layout.md
│   ├── roadmap.md
│   ├── snapshot_spec.md
│   ├── testing_strategy.md
│   └── versioning_policy.md
├── drift_test.py
├── readme.md
├── repo-runner.code-workspace
├── repo-runner.spec
├── scripts
│   ├── build_exe.ps1
│   ├── export-signal.ps1
│   ├── generate_test_repo.ps1
│   └── package-repo.ps1
├── slice_preview.md
├── src
│   ├── __init__.py
│   ├── analysis
│   │   ├── __init__.py
│   │   ├── context_slicer.py
│   │   ├── graph_builder.py
│   │   ├── import_scanner.py
│   │   └── snapshot_comparator.py
│   ├── api
│   │   ├── init.py
│   │   └── server.py
│   ├── cli
│   │   ├── __init__.py
│   │   └── main.py
│   ├── core
│   │   ├── __init__.py
│   │   ├── config_loader.py
│   │   ├── controller.py
│   │   ├── repo-runner.code-workspace
│   │   └── types.py
│   ├── entry_point.py
│   ├── exporters
│   │   └── flatten_markdown_exporter.py
│   ├── fingerprint
│   │   └── file_fingerprint.py
│   ├── gui
│   │   ├── __init__.py
│   │   ├── app.py
│   │   └── components
│   │       ├── config_tabs.py
│   │       ├── export_preview.py
│   │       ├── preview_pane.py
│   │       ├── progress_window.py
│   │       └── tree_view.py
│   ├── normalize
│   │   └── path_normalizer.py
│   ├── observability
│   │   ├── init.py
│   │   └── token_telemetry.py
│   ├── scanner
│   │   └── filesystem_scanner.py
│   ├── snapshot
│   │   ├── snapshot_loader.py
│   │   └── snapshot_writer.py
│   └── structure
│       └── structure_builder.py
└── tests
    ├── __init__.py
    ├── integration
    │   ├── __init__.py
    │   ├── test_api.py
    │   ├── test_export_flow.py
    │   ├── test_full_snapshot.py
    │   ├── test_graph_snapshot.py
    │   ├── test_robustness.py
    │   └── test_snapshot_flow.py
    └── unit
        ├── __init__.py
        ├── test_cli_diff.py
        ├── test_cli_slice.py
        ├── test_config_loader.py
        ├── test_context_slicer.py
        ├── test_filesystem_scanner.py
        ├── test_fingerprint_hardening.py
        ├── test_flatten_exporter.py
        ├── test_graph_builder.py
        ├── test_graph_resolution.py
        ├── test_ignore_logic.py
        ├── test_import_scanner.py
        ├── test_import_scanner_logic.py
        ├── test_normalizer.py
        ├── test_path_normalizer.py
        ├── test_scanner_hardening.py
        ├── test_snapshot_comparator.py
        ├── test_snapshot_loader.py
        ├── test_structure.py
        ├── test_structure_builder.py
        ├── test_token_telemetry.py
        └── test_types.py
```

---
## Context Stats
- **Total Characters:** 3,571
- **Estimated Tokens:** ~892 (assuming ~4 chars/token)
- **Model Fit:** GPT-4 (8k)
