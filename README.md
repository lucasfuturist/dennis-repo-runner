# `README.md`

# repo-runner

**Deterministic repository structure compiler and context engineering substrate.**

`repo-runner` freezes dynamic codebases into immutable, topologically accurate snapshots. It is designed to provide a high-resolution structural substrate for AI Agents (like Dennis) to navigate, understand, and modify code without the overhead of raw filesystem scanning or the hallucinations of unstable file paths.

---

## 🚀 Core Capabilities

- **Deterministic Ingestion:** Byte-for-byte reproducible snapshots across Windows, macOS, and Linux.
- **Semantic Graph Layer:** AST-derived dependency mapping (Python) and Regex-based scanning (JS/TS).
- **Context Slicing:** BFS-driven graph traversal to isolate specific features and their dependencies within a strict token budget.
- **Stable ID System:** Canonical, lowercased, repo-relative identifiers for files, modules, and external packages.
- **Architectural Visualization:** One-command exports to Mermaid.js and Draw.io (Advanced CSV with auto-layout).
- **Agent-Ready SOPs:** Integrated telemetry and diffing tools to verify structural impact after code changes.

---

## 🛠️ Installation

```bash
# Clone the repository
git clone https://github.com/your-repo/repo-runner.git
cd repo-runner

# Install dependencies
pip install -r requirements.txt

# (Optional) Verify the environment
python -m pytest
```

---

## 🕹️ Usage

### 1. The GUI (Control Panel)
Launch the interactive dashboard to browse the repo, select files, and trigger snapshots or visual previews.
```bash
python -m src.entry_point ui
```

### 2. The CLI (SOPs)

#### **SOP A: Indexing (Snapshot)**
Create an immutable record of the repository structure and dependency graph.
```bash
python -m src.entry_point snapshot . --output-root ./snapshots --ignore node_modules .git
```

#### **SOP B: Targeted Context (Slicing)**
Generate a compressed Markdown context centered on a specific symbol (Class/Function) or file.
```bash
python -m src.entry_point slice --repo-root . --focus "symbol:GraphBuilder" --radius 1 --max-tokens 4000
```

#### **SOP C: Visualization (Diagram)**
Project the dependency graph into a Mermaid or Draw.io-compatible format.
```bash
# Generate Mermaid.js code
python -m src.entry_point diagram --repo-root . --format mermaid

# Generate Draw.io Auto-Layout CSV
python -m src.entry_point diagram --repo-root . --format drawio
```

#### **SOP D: Verification (Diff)**
Compare the structural drift between two snapshots to verify changes.
```bash
python -m src.entry_point diff --base current --target {new_snapshot_id}
```

---

## 🧠 Design Philosophy

### Determinism
Given the same repository state and configuration, `repo-runner` produces bit-for-byte identical `manifest.json` and `graph.json` files. It eliminates non-determinism caused by OS-specific file ordering, random UUIDs, or timestamps in exports.

### Stable IDs
`repo-runner` enforces a strict naming convention to prevent ID "shimmering":
*   **Files:** `file:src/core/controller.py` (Lowercase, forward-slash).
*   **Symbols:** `symbol:GraphBuilder` (Directly indexed in `symbols.json`).
*   **External:** `external:pandas` (Canonicalized root package names).

### Append-Only Snapshots
Snapshots are never overwritten. Every run produces a unique, timestamped folder. Only the `current.json` pointer is updated to reference the latest state.

---

## 📂 Snapshot Artifacts

Each snapshot folder contains the following JSON ground-truth artifacts:

1.  **`manifest.json`**: File fingerprints (SHA256), sizes, and raw import/symbol lists.
2.  **`graph.json`**: The topological map. Includes nodes, edges, and cycle detection flags.
3.  **`structure.json`**: The hierarchical directory tree representation.
4.  **`symbols.json`**: A global inverted index mapping symbols to their defining files.
5.  **`exports/`**: Derived projections like `flatten.md`, `graph.mmd`, or `graph.drawio.csv`.

---

## 📡 API Interface
`repo-runner` includes a FastAPI server for remote tool-calling by LLM agents.
```bash
# Start the server
uvicorn src.api.server:app --reload
```
**Endpoints:**
*   `POST /snapshots`: Ingest a repository.
*   `POST /snapshots/{id}/slice`: Request a context window.
*   `POST /snapshots/compare`: Diff structural states.

---

## 🗺️ Roadmap Status

- [x] **v0.1:** Deterministic scanning, fingerprinting, and flattened exports.
- [x] **v0.2:** Semantic graph layer, symbol indexing, and token telemetry.
- [x] **v0.3:** Hardened canonicalization, visual diagram exporters (Mermaid/Draw.io), and GUI.
- [ ] **v0.4:** Diagram Projection (Native `.drawio` XML engine).
- [ ] **v0.5:** Parallelized fingerprinting and scanning for ultra-large repos.

---

## ⚖️ License
Internal use only.

---
*Built for Dennis.*