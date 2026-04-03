# EXECUTIVE MANIFEST: DENNIS C2 & AJA INFRASTRUCTURE
**Classification:** SECURE / LOCAL-SOVEREIGN
**Date Validated:** 2026-03-07
**Hardware Baseline:** Windows 11 Pro / WSL2 (Ubuntu 24.04) / Dual RTX 4090 (48GB VRAM) / 128GB RAM / Core i9

## 1. STRATEGIC OVERVIEW
This environment constitutes the localized command-and-control (C2) infrastructure for "Dennis" (CEO/Orchestrator) and "AJA" (Autonomous Job Agent / Mercenary). The system is fully sovereign, executing multi-agent graph flows, deterministic Python execution, reverse engineering, and browser infiltration without relying on external corporate APIs for primary intelligence.

---

## 2. NEURAL ARMORY (Ollama / Local Weights)
These are the localized brains of the operation. Dennis allocates VRAM dynamically via Ray to hot-swap these models based on task requirements.

| Model ID | Tactical Role | VRAM Footprint | Description |
| :--- | :--- | :--- | :--- |
| `deepseek-r1:70b` | The Heavy Reasoner | ~42.5 GB | Dennis's primary logic engine. Used for strategic planning, multi-step bounty analysis, and final code review. |
| `qwen2.5-coder:32b` | The Pure Coder | ~24.5 GB | AJA's primary execution muscle. Handles complex AST parsing, Python logic generation, and deterministic regex. |
| `llama3.2-vision:11b` | The Vision Extractor | ~9.5 GB | Multimodal infiltration. Defeats UI captchas, parses obfuscated DOMs visually, and maps screen coordinates. |
| `nous-hermes2:latest` | The JSON Router | ~8.5 GB | Blistering fast tool-caller. Routes API webhooks, parses structured corporate payloads. |
| `qwen2.5-coder:1.5b` | The Speed Multiplier | ~1.5 GB | Speculative Drafter. Runs concurrently with 70B/32B models to 3x token generation speed. |
| *(Pending HF Pull)* | BGE-M3 (Embeddings) | ~1.2 GB | Topography mapper. Multi-lingual dense/sparse vector embedding model. |
| *(Pending HF Pull)* | Command R (35B) | ~22.0 GB | The RAG Architect. Hallucination-resistant context synthesis for massive codebase queries. |

---

## 3. EXECUTIVE INFRASTRUCTURE (Docker C2)
Dennis manages state, memory, and telemetry via these containerized microservices running on the Docker-WSL2 bridge.

*   **Langfuse** (`localhost:3000`)
    *   *Role:* The Panopticon. Tracks AJA's token usage, API costs, LLM execution traces, and cyclical workflow states.
*   **Memgraph** (`localhost:7687`, UI: `3001`)
    *   *Role:* The War Room. High-speed Graph Database tracking relationships (e.g., Client -> Tech Stack -> Vulnerability).
*   **PostgreSQL + pgvector** (`localhost:5432`)
    *   *Role:* The Corporate Ledger. Hardened relational state tracking for bounty ROI, historical proposals, and application metrics.
*   **Qdrant** (`localhost:6333`)
    *   *Role:* The Synaptic Vault. Rust-based Vector DB for sub-second semantic retrieval of AST "book titles" and code snippets.
*   **NATS.io** (`localhost:4222`)
    *   *Role:* The Comms Relay. Sub-millisecond event bus. Dennis broadcasts orders to AJA nodes via pub/sub topics.
*   **Temporal** (`localhost:7233`, UI: `8233`)
    *   *Role:* Mission Scheduler. Ensures invincible, stateful execution. If WSL2 crashes, AJA resumes the bounty hunt exactly where it left off.
*   **FlareSolverr** (`localhost:8191`)
    *   *Role:* Proxy Infiltrator. Bypasses Cloudflare / DDoS-Guard blocks on Upwork and Greenhouse job boards.

---

## 4. TACTICAL EXECUTION ENVIRONMENT (`~/aja_env`)
The isolated Python virtual environment containing AJA's execution scaffolding and weaponry.

### Compute & Orchestration
*   `vllm` / `sglang`: High-throughput PagedAttention local inference engines (Enables Speculative Decoding).
*   `ray[default]`: Distributed compute cluster manager for dual-GPU load balancing.
*   `langgraph`: Stateful multi-agent cyclical routing (The core "brain loop" of AJA).
*   `litellm`: Universal proxy translating all local models into a standard OpenAI-compatible API format.

### Infiltration & Extraction
*   `browser-use`: Allows the 11B Vision model to physically take over a headless browser via DOM mapping and coordinate clicking.
*   `crawl4ai`: Advanced asynchronous web crawler that renders JS and outputs LLM-optimized Markdown.
*   `mitmproxy`: Intercepts and decrypts backend corporate API traffic from job boards.
*   `faster-whisper`: Audio interceptor to transcribe video bug reports and Zoom meeting bounties.

### Codebase Manipulation (`repo-runner` Integrations)
*   `tree-sitter` (+ Python/JS/TS bindings): Sub-millisecond AST generators for flawless codebase topography mapping.
*   `aider-chat` (Headless): Splicing engine. Takes AJA's generated code and safely applies it to massive, multi-file repos using Universal Diffing.

---

## 5. FORENSIC SUITE (Standalone)
*   **Ghidra** (`~/ghidra`)
    *   *Role:* NSA Reverse Engineering framework. Used headlessly by AJA to decompile proprietary C++/Rust/Go binaries into pseudo-code for vulnerability bounties.

---

## 6. OPERATIONAL HIERARCHY DIRECTIVE
1. **Dennis (CEO)** sits at the orchestration layer, monitoring `Langfuse`, managing the `Postgres` ledger, and allocating GPUs via `Ray`.
2. **Dennis** issues a target bounty via the `NATS` event bus.
3. **AJA (Mercenary)** spins up inside `~/aja_env`, utilizes `Crawl4AI` / `Browser-use` to breach the target site, and `repo-runner` (via `tree-sitter`) to map the codebase.
4. **AJA** generates the payload using `Qwen-32B` and applies it via `Aider`.
5. **AJA** reports success/failure back to Dennis via `NATS` for Temporal workflow resolution.