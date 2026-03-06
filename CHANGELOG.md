# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

## [0.1.6] - 2026-03-06

### Removed
- **Microsandbox, Monty, and Docker Backends** (simplified to single backend):
    - **Microsandbox**: Removed due to Python SDK v0.1.8 / server v0.2.6 incompatibility.
    - **Monty**: Removed due to limited Python support (only 9/19 compute tasks, no PTC support).
    - **Docker**: Removed in favor of OpenSandbox for unified architecture.
    - Removed `MicrosandboxExecutor`, `MontyExecutor`, and `DockerBaseline` from codebase.
    - Removed all three from task `supported_backends` lists across 7 categories (83 tasks).
    - Updated `benchmarks/runner.py`, `benchmarks/cli.py`, `client/__init__.py` to remove all three backends.

### Added
- **MCPRuntime Benchmark Suite (MRBS)** - Production-ready benchmark system:
    - **83 tasks across 7 categories**:
        - **PTC** (8): True Programmatic Tool Calling tasks requiring tool imports
        - **Compute** (19): Standalone algorithmic tasks
        - **Import-Heavy** (12): Package loading and data processing
        - **I/O** (12): Filesystem operations
        - **Memory** (10): Allocation patterns
        - **Concurrency** (10): Threading and async
        - **Enterprise** (16): Real-world workflow patterns
    - Single validated backend: **OpenSandbox** (recommended) with **Subprocess** for development.
    - Two evaluation modes:
        - **Baseline Mode** (`--llm-provider none`): Infrastructure verification with reference code (~100% expected).
        - **LLM Mode** (`--llm-provider azure_openai`): Real agent evaluation with LLM-generated code (~70-90% realistic).
    - Task difficulty levels: easy, medium, hard.
    - Validation types: exact match, fuzzy match, custom validators.
    - Metrics: Success Rate, Time-to-Success (TTS), LLM Generation Time, Execution Time, Iterations.
    - Documentation: `docs/benchmark_guide.md`, `docs/benchmark_analysis.md`.

#### OpenSandbox - The Single Backend
OpenSandbox is now the **only recommended backend** for MRBS:
- Runs all 83 tasks (100% pass rate on compute, 75% on PTC)
- Full PTC (Programmatic Tool Calling) support with proper file setup
- Docker container isolation
- ~3s per task execution time

#### PTC (Programmatic Tool Calling) Tasks - True PTC Benchmarking
The PTC category contains **real PTC tasks** where the agent must:
- Import tools: `from client.mock_mcp_client import call_mcp_tool`
- Call external tools with correct arguments
- Handle tool responses and compose multiple tools

**PTC Task Examples:**
- **PTC01** (easy): Calculator - Sum a list using `call_mcp_tool('calculator', 'add', ...)`
- **PTC03** (easy): Weather - Get temperature using `call_mcp_tool('weather', 'get_weather', ...)`
- **PTC04** (medium): Filesystem - Read file using `call_mcp_tool('filesystem', 'read_file', ...)`
- **PTC06** (medium): Multi-tool - Combine weather + calculator tools
- **PTC08** (hard): Chained tools - Weather forecast analysis with multiple tool calls

This distinguishes MRBS from standalone code execution benchmarks - it tests true **Programmatic Tool Calling** as defined by Anthropic/Cloudflare.

### Changed
- **Backend Simplified to OpenSandbox Only**:
    - **OpenSandbox** is now the sole recommended backend (100% tasks, ~3s/task, full PTC support).
    - **Subprocess** remains for development only (no isolation, fastest).
    - Removed Docker, Monty, and Microsandbox to simplify architecture.
- **CLI Backend Choices**: Now `[opensandbox|subprocess]` only.
- **Documentation Cleanup**: Removed `MRBS_PROJECT_PLAN.md`, `index.md`, `docs/README.md`.
- **OpenSandbox Executor Enhanced**: Added support for pushing arbitrary setup files (mock_mcp_client.py, data files) to container for PTC tasks.

## [0.1.4] - 2026-03-05

### Added
- Added `NOTICE` file complying with Apache 2.0 attribution for `microsandbox` and `OpenSandbox`.

### Changed
- Updated `LICENSE` and `README.md` to append third-party open-source legal notices.
- Expanded `README.md` to clearly contrast Programmatic Tool Calling (PTC) vs Recursive Language Models (RLM).

### Added
- **OpenSandbox Execution Backend** (`client/opensandbox_executor.py`):
    - New `OpenSandboxExecutor` — full drop-in replacement for `MicrosandboxExecutor` using [alibaba/OpenSandbox](https://github.com/alibaba/OpenSandbox) (local Docker, no cloud API key required).
    - Replicates microsandbox volume-mount behaviour via `sandbox.files.write_files()`, pushing workspace files (client/, servers/, skills/) into the container before execution.
    - Friendly startup check: if `opensandbox-server` is not running, surfaces a clear `❌ OpenSandbox server not reachable` error with exact fix commands instead of a cryptic connection error.
    - `_is_connection_error()` helper for reliable detection of server-not-running failures across httpx/aiohttp transports.
    - `tests/unit/test_opensandbox_executor.py`: unit tests (import guard, guardrails, mocked execution).
- **Configuration**:
    - Added `opensandbox_domain` and `opensandbox_image` fields to `ExecutionConfig`.
- **Docker Compose Profiles**:
    - Restructured `docker-compose.yml` into profiles: `mcpruntime` (OpenSandbox default), `microsandbox` (privileged), and `monty` fallback.
    - Simplified `Dockerfile` default build to `python-only` target, significantly reducing build time.
- **Streaming Execution Output**:
    - `StreamingExecutor` wrapper for yielding live execution text line-by-line.
    - `POST /execute/stream` Server-Sent Events (SSE) API endpoint in `server/http_server.py`.
    - Included `examples/18_streaming.py` client demo connecting via `httpx`.
- **Time-Travel Debugging & Replay**:
    - Automatic JSONL session logging via `mcpruntime/replay_log.py`.
    - Rewind and fork agent sessions via `AgentHelper.resume_from(session_id, step)`.
    - Added `replay.py` CLI utility to repo root for playing back sessions frame-by-frame.
    - Included `examples/19_replay.py` demo.

### Fixed
- **Monty Executor**:
    - Added `globals()` and `locals()` shims to `ext_funcs` so LLM-generated code that calls `globals()` to inspect injected variables (e.g. `CONTEXT_DATA`) no longer crashes.
- **Recursive Agent**:
    - Fixed RLM instruction pattern: replaced binary `'yes'` check with `FOUND: <answer>` / `NOT_FOUND` sentinel format so the LLM's answer is reliably propagated to output.
    - Explicitly warned generated code not to call `globals()` to access `CONTEXT_DATA` (it is a direct variable in scope).

### Changed
- **Default execution backend changed from `microsandbox` to `opensandbox`** across `config/schema.py`, `config/loader.py`, `mcpruntime/__init__.py`, and `config.example.yaml`.
- `create_agent()` factory now falls back to `OpenSandboxExecutor` for unknown sandbox types.
- README Quick Start completely rewritten with three clear backend options (A: OpenSandbox, B: Monty, C: Microsandbox), each with numbered copy-paste commands and error guidance.

---

## [0.1.2] - 2026-03-03

### Added
- **Skill Evolution (Self-Growing Tool Library)** (`client/skill_manager.py`, `examples/17_skill_evolution.py`):
    - Successful code actions are automatically extracted, typed, and saved as reusable skill modules in `skills/`.
    - `SkillManager` evaluates code quality (compilability, function structure, output quality) to determine if a skill is worth saving.
    - Skill Registry auto-injects available skill listings into the agent prompt so future executions can `from skills.my_tool import run`.
    - Skill Evolution is compatible with all backends: `MicrosandboxExecutor`, `MontyExecutor`, and `RecursiveAgent`.
    - `AgentHelper` extended with `auto_save_skills` flag and `_maybe_save_skill()` method.
    - `tests/unit/test_skill_evolution.py`: unit tests covering skill evaluation, extraction, and registry.
- **Recursive Language Models (RLM)**:
    - New `RecursiveAgent` capable of processing infinite context windows via "chunk-and-reason" loops.
    - `ask_llm(question, chunk)` callback injected into the execution context for recursive LLM querying.
    - Automatic tool inlining for Monty-based RLM agents (strips incompatible imports, inlines server and skill source).
- **Project Infrastructure**:
    - `Dockerfile` and `docker-compose.yml` for containerised deployment.
    - `Makefile` with `install-dev`, `env`, `test`, `test-e2e`, and `test-all` targets.
    - `CONTRIBUTING.md` with full local setup guide.
    - `LICENSE` (MIT).
    - `.github/workflows/tests.yml` CI pipeline.
    - GitHub Issue / PR templates (`.github/ISSUE_TEMPLATE/`, `PULL_REQUEST_TEMPLATE.md`).
    - `docs/README.md` and `scripts/` for verification and debugging utilities.
- **Testing Infrastructure**:
    - Centralized `tests/` directory with `unit/`, `integration/`, and `e2e/` suites.
    - `tests/conftest.py` fixtures for mocked and live LLM clients, temp workspaces.
    - `tests/e2e/test_live_rlm.py` and `tests/e2e/test_live_vanilla.py` for end-to-end validation against real LLMs.
    - `tests/integration/test_recursive_agent.py` integration tests.
- **Configuration**:
    - `.env.example` template with all supported environment variables.
    - `.env` support — `config/loader.py` auto-loads `.env` if `python-dotenv` is installed.

### Fixed
- **Monty Executor**:
    - Fixed `TypeError` and validation errors when executing code with empty inputs.
    - Improved handling of `pydantic-monty` edge cases (dummy input injection).
- **Recursive Agent**:
    - Fixed `UnboundLocalError` by only injecting `CONTEXT_DATA` instructions when context is provided.
- **Code Generator**:
    - Fixed crash when `required_tools` is `None`.
- **ToolSelector**:
    - Patched to handle broken `torch` / `torchvision` installations gracefully.

### Changed
- `create_agent()` now resolves `sandbox_type` via `SANDBOX_TYPE` environment variable (with YAML config taking precedence).
- README updated with RLM section, Skill Evolution section, architecture diagram, and references.
- `verify_setup.py` overhauled with comprehensive environment and backend checks.

---

## [0.1.1] - 2026-02-07

### Added
- **Monty Execution Backend**: Integrated `pydantic-monty` as an experimental high-performance execution runtime.
- **Pluggable Executor Architecture**: Refactored `AgentHelper` to support multiple backends via `CodeExecutor` interface.
- **OS Callbacks for Monty**: Implemented file system redirection for Monty to allow workspace access.
- **JSON Helpers for Monty**: Injected `json_loads` and `json_dumps` to Monty environment.
- **Versioning Support**: Added `--version` flag to MCP server CLI and a `get_version` tool.

### Changed
- Refactored `SandboxExecutor` to `MicrosandboxExecutor`.
- Updated `create_agent` factory to handle dynamic backend selection.
- Patched `ToolSelector` to handle broken `torch` installations gracefully.

---

## [0.1.0] - 2026-01-30

### Added
- Initial release of MCPRuntime.
- Support for Microsandbox execution.
- MCP tool discovery and selection using semantic search.
- Async middleware for background task execution.
- Programmatic Tool Calling (PTC) pattern implementation.
