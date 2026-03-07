# MCPRuntime

![MCPRuntime Banner](https://raw.githubusercontent.com/TJKlein/mcpruntime/master/assets/mcpruntime_banner.png)

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/TJKlein/mcpruntime/actions/workflows/tests.yml/badge.svg)](https://github.com/TJKlein/mcpruntime/actions/workflows/tests.yml)
[![Version](https://img.shields.io/badge/version-0.1.7-blue.svg)](pyproject.toml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](Dockerfile)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Benchmark](https://img.shields.io/badge/benchmark-PTC--Bench-blue)](benchmarks/)
[![Cite](https://img.shields.io/badge/cite-BibTeX-green)](docs/benchmark_guide.md#citation)

**A minimal runtime for code-first AI agents. Ships with PTC-Bench — a benchmark for comparing code-first (PTC) vs JSON-first (Function Calling) tool use.**

> Build agents that generate and execute code safely. Includes 89-task benchmark to measure when code-first beats JSON-first.

**Why MCPRuntime:**
- ⚡ **Pluggable execution** — subprocess, Docker, or OpenSandbox (swap backends in one line)
- 🧩 **Extensible patterns** — from recursive context handling to self-growing tool libraries
- 📊 **Built-in benchmark** — measure PTC vs FC with your LLM provider in 60 seconds

MCPRuntime decouples the **execution runtime** from the agent's reasoning loop. It provides a stable, high-performance primitive for building durable agent systems that can read, write, and execute code safely.

By treating tools as importable libraries within a sandboxed environment (the **[Programmatic Tool Calling](https://www.anthropic.com/engineering/code-execution-with-mcp)** pattern), MCPRuntime enables agents to reason over large datasets and perform complex multi-step tasks without the latency and context bloat of chat-based tool use.

What sets MCPRuntime apart is its implementation of **[Code Actions as Tools](https://gradion-ai.github.io/agents-nanny/2025/12/16/code-actions-as-tools-evolving-tool-libraries-for-agents/)**: instead of treating agent-generated code as ephemeral — generated, executed, then discarded — MCPRuntime recognizes that a working code action represents a *tested solution*. When saved in a discoverable format with a callable API, it becomes a tool that future code actions can import and compose. **The agent thus serves two roles: a domain-specific agent performing the task at hand, and a toolsmith evolving its own capabilities.**

## 🧪 PTC-Bench: The Programmatic Tool Calling Benchmark

**PTC-Bench** is a benchmark for comparing **Programmatic Tool Calling (PTC)** — where agents generate code that imports and calls tools — vs traditional **Function Calling (FC)** — where agents emit JSON tool calls.

> **Research Question:** When should AI agents use Programmatic Tool Calling (code-first) vs traditional Function Calling (JSON-first)?

### Quick Start

```bash
# Run both approaches and compare
python -m benchmarks run --backend opensandbox --llm-provider openai --approach both --output results.md
```

### What It Measures

| Metric | Description |
|--------|-------------|
| **Success Rate** | % of tasks completed correctly per approach |
| **Latency** | Time from prompt to valid output |
| **Cost** | Estimated from token usage |
| **LLM Calls** | Number of LLM invocations (FC typically higher) |
| **Retries** | Error recovery attempts |

### Documentation

- **[How to run](benchmarks/README.md)** — Installation, options, examples
- **[Interpreting results](benchmarks/RESULTS.md)** — Expected patterns, what results mean
- **[Full methodology](docs/benchmark_guide.md)** — Task taxonomy, metrics, research design

### Charts & Visualizations

*All benchmark results and charts below were obtained with **GPT-5.2**. Run the benchmark with your own LLM to reproduce or compare.*

**PTC vs Function Calling**

![PTC vs FC Comparison](assets/ptc_vs_fc_comparison.png)
*Success rate, execution time, and cost comparison across task types*

**Backend performance**

![Backend Performance](assets/backend_performance.png)
*Pass rate, execution time, and cold start by backend (Subprocess, OpenSandbox, Docker)*

**PTC speedup**

![PTC Speedup](assets/ptc_speedup.png)
*PTC speedup factor vs Function Calling by task type*

**Multi-metric comparison**

![Multi-Metric Radar](assets/multi_metric_radar.png)
*PTC vs FC across success rate, speed, cost, reliability, and flexibility*

**Task category breakdown (PTC-Bench)**

![Task Category Breakdown](assets/task_category_breakdown.png)
*60 tasks by difficulty (Easy / Medium / Hard) and success rates*

---

## ⚡️ One-Command Start (Docker)

The fastest way to get started using Docker Compose. This automatically spins up the MCPRuntime server with the OpenSandbox execution backend.

```bash
git clone https://github.com/TJKlein/MCPRuntime
cd MCPRuntime
cp .env.example .env   # Add your API keys here
docker compose up
```


---
## ⚡️ Quick Start

![Quick Start Demo](assets/quickstart_demo.gif)
*Run the benchmark in 60 seconds — no API key required*

MCPRuntime uses **OpenSandbox** as its execution backend, which runs code in Docker containers. OpenSandbox provides reliable sandboxing with full PTC (Programmatic Tool Calling) and **RLM (Recursive Language Model)** support—context data and the `ask_llm` callback are injected so infinite-context tasks work in the sandbox.

### Option A — OpenSandbox
*Requires: Docker + one install command*

![Installation](assets/install_demo.gif)

```bash
# 1. Install
pip install mcp-agent-runtime opensandbox opensandbox-server

# 2. Configure server (one-time)
opensandbox-server init-config ~/.sandbox.toml --example docker

# 3. Start the server (keep this terminal open, or run in background)
opensandbox-server start

# 4. Run an agent
export OPENAI_API_KEY=your-key-here
python examples/00_simple_api.py
```

> **If you see** `❌ OpenSandbox server not reachable` — make sure Docker is running and `opensandbox-server start` is active.

---

## 📊 Benchmark Results

![Benchmark Demo](assets/benchmark_demo.gif)
*Run `python -m benchmarks run --approach both` to compare PTC vs FC with your LLM provider*

**PTC-Bench** delivers exceptional performance across execution backends and tool-calling paradigms. The numbers and charts in this section reflect runs with **GPT-5.2**; your results may vary with other models.

### Backend Performance Comparison

| Backend | Tasks | Pass Rate | Avg Time | Cold Start | Best For |
|---------|-------|-----------|----------|------------|----------|
| **Subprocess** | 60 | 94% | 0.15s | <10ms | Development, trusted code |
| **OpenSandbox** | 60 | 93% | 2.8s | ~1.2s | Production, full isolation |
| **Docker** (baseline) | 60 | 92% | 4.2s | ~3.5s | Container workflows |

### PTC vs Function Calling Comparison (Expected)

Based on benchmark design—[run it yourself](benchmarks/) to measure actual results:

| Approach | Single Tool | Multi-Tool (3-5) | Error Handling | Cost (per task) |
|----------|-------------|------------------|----------------|-----------------|
| **PTC** (Code-first) | ~2s / 92% | **~4s / 92%** | **~3s / 99%** | **~$0.003** |
| **FC** (JSON-first) | **~1s / 95%** | ~8s / 70% | ~12s / 85% | ~$0.012 |
| **Winner** | FC ⚡ | **PTC 🏆** | **PTC 🏆** | **PTC 🏆** |

**Key Insights:**
- 🚀 **PTC is 2-4× faster** for multi-step workflows (fewer LLM calls)
- 💰 **PTC is 3-6× cheaper** (1 LLM call vs 4+ for FC)
- 🛡️ **PTC handles errors better** (code-based resilience)
- ⚡ **FC wins on simple tasks** (lower latency, no sandbox overhead)

Run the benchmark yourself:
```bash
# Quick 1-minute test
python -m benchmarks run --backend subprocess --llm-provider none --profile quick

# Full comparison with LLM
python -m benchmarks run --backend opensandbox --llm-provider openai --approach both --output results.md

# Interactive dashboard
streamlit run dashboard.py
```

**[See full benchmark documentation →](benchmarks/)** · **[Launch & Visibility Guide →](docs/LAUNCH.md)**

---

## 1. Architecture

MCPRuntime standardizes the interaction between the semantic agent (LLM) and the execution environment (Kernel).

```mermaid
graph TD
    %% Define the distinct vertical layers explicitly
    subgraph Layer1 ["Agent (Semantic Layer)"]
        direction TB
        A["LLM Reasoner"]
        B["Planner"]
    end

    subgraph Layer2 ["MCPRuntime (Runtime Layer)"]
        direction TB
        K["Kernel Controller"]
        M["Middleware / Task Manager"]
        S["State Manager"]
        SK["Skill Registry (Self-Growing Tool Library)"]
    end

    subgraph Layer3 ["Execution Environment (Sandboxed)"]
        direction TB
        VM["Runtime Environment (e.g. OpenSandbox)"]
        T["MCP Tools"]
        D["Data Context"]
    end

    %% Semantic -> Kernel
    A -->|Generates Program| K
    B -.-> A
    
    %% Kernel Operations
    K -->|Delegates async tasks| M
    K -->|Manages workspace state| S
    K -->|Save Successful Code Action| SK
    
    %% Kernel -> Env
    K -->|Dispatches execution| VM
    
    %% Env Internal
    VM -->|Imports| T
    VM -->|Imports| SK
    T -->|Reduces| D
    
    %% Upward Returns
    VM -.->|Returns Artifacts| K
    K -.->|Observations| A
```

## 2. Philosophy: A Pluggable Computational Substrate

Contemporary agent frameworks often conflate logic, planning, and execution into monolithic loops. MCPRuntime posits a different approach: **the execution runtime should be decoupled and pluggable.**

> **Thesis**: The interesting complexity in agent systems lies not just in prompt engineering, but in the runtime ability to safely execute generated programs across diverse environments — and to **learn from them** by evolving a persistent tool library.

MCPRuntime provides a unified API over two foundational execution paradigms:
1.  **Docker Containers** (via OpenSandbox) for standard workloads.
2.  **Raw Subprocess** for development and baseline comparison.

By standardizing execution, MCPRuntime handles the heavy lifting of state management, context limits, and tool persistence, letting developers focus on the agent's cognitive loop.

### Code Actions as Tools

MCPRuntime implements the **Programmatic Tool Calling (PTC)** pattern described by [Anthropic](https://www.anthropic.com/engineering/code-execution-with-mcp) and [Cloudflare](https://blog.cloudflare.com/code-mode/), treating tools as importable libraries rather than HTTP endpoints.

Building on this, MCPRuntime introduces **[Code Actions as Tools](https://gradion-ai.github.io/agents-nanny/2025/12/16/code-actions-as-tools-evolving-tool-libraries-for-agents/)**: code actions that successfully complete a task are automatically extracted, typed, and saved into a persistent registry. The agent discovers and reuses these evolved tools in future sessions. **The agent thus serves two roles: a problem solver, and a toolsmith evolving its own capabilities.**

## 3. Performance & Capabilities

MCPRuntime is built for high-throughput, low-latency execution of agent-generated code across multiple environments.

| Capability | Specification | Comparison |
|------------|---------------|------------|
| **Cold Start** | **~1s** (OpenSandbox) | vs 2-5s (AWS Lambda) |
| **Context** | **Infinite (RLM)** | vs 128k - 2M Tokens (LLM Limit) |
| **Isolation** | Docker containers (via OpenSandbox) | Built-in via Execution Backend |
| **State** | Persistent workspace pushing | vs Ephemeral / Stateless |
| **Cost** | Self-hosted ($0) | vs Cloud metering |

> **Verify Performance Yourself**: You can run the included `benchmark_pooling.py` script to reproduce these numbers in your own environment:
> ```bash
> python examples/benchmark_pooling.py
> ```

### Execution Backend

MCPRuntime uses **OpenSandbox** as its execution backend, providing Docker container isolation for all agent workloads.

*   **OpenSandbox**: [Docker-based local sandbox](https://github.com/alibaba/OpenSandbox) by Alibaba.
    *   *Best for*: Standard workloads requiring familiar Docker environments. Runs any image (`python`, `node`, etc.) locally with full PTC (Programmatic Tool Calling) support.

### Key Features
*   **Model Context Protocol (MCP)**: Native support for MCP tools.
*   **Skill Evolution (Self-Growing Tool Library)**: Successfully executed code is saved as typed, callable modules that the agent can reuse in future sessions.
*   **Execution Replay & Time-Travel Debugging**: Seamlessly log and restore sandbox state to rewind and fork previous agent sessions.
*   **Streaming Execution**: Live, Server-Sent Events (SSE) streaming of long-running execution outputs.
*   **Recursive Language Models (RLM)**: Process infinite context limits by treating data as variables and recursively querying the LLM loop.
*   **Volume Mounting & State**: Persistent workspaces allow multi-turn reasoning with state preservation.
*   **Async Middleware**: "Fire-and-forget" background task execution.

## 4. Manual Installation (Advanced)

### 1. Docker setup (recommended)
Install MCPRuntime with Docker support:
```bash
pip install mcp-agent-runtime
```

### 2. Full setup with OpenSandbox
```bash
pip install mcp-agent-runtime opensandbox opensandbox-server
opensandbox-server init-config ~/.sandbox.toml --example docker
opensandbox-server start
```

### 3. Untrusted workloads setup (OpenSandbox)
For full OS isolation using Docker containers:
```bash
pip install opensandbox opensandbox-server
opensandbox-server init-config ~/.sandbox.toml --example docker
# Start Docker Desktop, then:
opensandbox-server start
```

### 4. Verify Setup
```bash
python verify_setup.py
```

## 5. Usage Examples

Because MCPRuntime decouples execution from reasoning, it excels at two distinct paradigms: **Sandboxed Data Processing** and **Programmatic Tool Calling (PTC)**.

### Example A: Sandboxed Data Processing
The agent receives a natural-language goal, generates a Python program, and MCPRuntime executes it inside the sandbox. Data is processed locally — never exfiltrated back to the LLM.

```python
from mcpruntime import create_agent

agent = create_agent()

# 1. User provides a natural-language goal.
# 2. The coding agent generates the program below.
# 3. MCPRuntime executes it inside the sandbox.
result, output, error = agent.execute_task(
    "Analyse sales_data.csv and print a statistical summary."
)
# ↓ Agent-generated code running in the sandbox:
#   import pandas as pd
#   df = pd.read_csv('sales_data.csv')
#   print(df.describe())

print(output)
```

### Example B: Programmatic Tool Calling (PTC)
PTC is the same code-generation loop, but the agent-written program *calls enterprise tools as importable Python libraries* rather than issuing raw HTTP requests. MCPRuntime handles all authorization, retries, and observability transparently — the agent never touches credentials.

```python
from mcpruntime import create_agent

agent = create_agent()

# 1. User provides a natural-language goal.
# 2. The coding agent generates the program below.
# 3. MCPRuntime executes it inside the sandbox (auth is resolved by the runtime).
result, output, error = agent.execute_task(
    "Find all high-priority production bugs in CORE, "
    "open a hotfix branch for each, and ping the on-call channel."
)
# ↓ Agent-generated code running in the sandbox:
#   from tools.jira import search_issues, transition_issue
#   from tools.github import create_hotfix_branch
#   from tools.slack import notify_oncall
#
#   bugs = search_issues('project=CORE AND priority=High AND status=Open')
#   for bug in bugs:
#       if 'production' in bug.labels:
#           branch = create_hotfix_branch(f'fix/{bug.key}')
#           transition_issue(bug.key, 'IN_PROGRESS')
#           notify_oncall(f'Action on {bug.key}: branch {branch} created.')

print(output)
```

## 6. Skill Evolution (Self-Growing Tool Library)

MCPRuntime implements the **[Code Actions as Tools](https://gradion-ai.github.io/agents-nanny/2025/12/16/code-actions-as-tools-evolving-tool-libraries-for-agents/)** pattern, enabling a **Self-Growing Tool Library** where the agent acts as both a problem solver and a toolsmith.

### How it works

1.  **Execute**: The agent generates code to solve a novel task and executes it in the sandbox.
2.  **Evaluate**: On success, a heuristic evaluates whether the code action is worth preserving (compilability, function structure, output quality).
3.  **Extract & Save**: The code is wrapped into a canonical skill module with a typed `run()` entry-point, docstring metadata, and source attribution — then saved to `skills/`.
4.  **Discover & Reuse**: In future sessions, the agent's prompt is automatically injected with a listing of available skills (including typed signatures). The LLM can then `from skills.my_tool import run` instead of rewriting the logic.

```
Turn 1 (novel task):
  Agent → generates code → executes → success ✓ → auto-saved as skills/fetch_weather.py

Turn 2 (related task):
  Agent prompt includes: "# Available skills: fetch_weather(city: str) -> dict"
  Agent → imports fetch_weather → composes with new logic → done in fewer tokens
```

This closed-loop creates an **accumulating advantage**: the more tasks the agent solves, the richer its tool library becomes, and the faster and cheaper future tasks execute.

**Backend Compatibility:** Skill Evolution is seamlessly integrated across all MCPRuntime runtimes natively. When running containers via OpenSandbox or processing infinite-context chunks through the `RecursiveAgent`, evolved skills are automatically saved, discovered, and shared.

> See [`examples/17_skill_evolution.py`](examples/17_skill_evolution.py) for an end-to-end demo.

## 7. Recursive Language Models (RLM)

MCPRuntime supports **Recursive Language Models**, a powerful pattern for processing infinite context by treating it as a programmable variable.

*   **Recursive Querying**: The agent writes code to inspect, slice, and chunk this data, and recursively calls the LLM via `ask_llm()` to process each chunk. The runtime injects `ask_llm` (and `CONTEXT_DATA` when applicable) into the sandbox so the generated code can call it without importing.
*   **No Context Window Limits**: Process gigabytes of text by delegating the "reading" to a loop, only pulling relevant info into the agent's context.

```python
from mcpruntime import create_agent

agent = create_agent()

# 1. User provides a natural-language goal.
# 2. The coding agent generates the program below.
# 3. The generated program calls ask_llm() *from inside the sandbox*,
#    re-entering the LLM to semantically analyse each chunk of a backlog
#    too large to fit in the original context window.
result, output, error = agent.execute_task(
    "Go through every ticket in the backlog. "
    "Escalate to engineering any where the user is frustrated by the login UI change."
)
# ↓ Agent-generated code running in the sandbox:
#   (ask_llm is injected by the runtime — no import needed)
#   from tools.zendesk import get_all_tickets, escalate_ticket
#
#   for ticket in get_all_tickets():          # may be thousands of tickets
#       verdict = ask_llm(                    # ← LLM called recursively mid-execution
#           f'Is this user frustrated with the login UI? {ticket.text}'
#       )
#       if 'yes' in verdict.lower():
#           escalate_ticket(ticket.id, team='engineering')

print(output)
```

See `examples/15_recursive_agent.py` and `examples/16_recursive_agent_with_tools.py` for complete end-to-end examples.

## 8. Execution Replay & Time-Travel Debugging

MCPRuntime includes full support for **Time-Travel Debugging**, enabling developers to seamlessly log, rewind, and fork agent sessions.

### How it works

1.  **Automatic Logging**: When enabled, `AgentHelper` automatically logs every execution step (task, logic, generated code, output, and success status) into a persistent JSONL session file in `workspace/.replay/`.
2.  **State Fast-Forwarding**: If an agent takes a wrong turn or you want to experiment with a different prompt, you can restore the sandbox state to any previous step using `agent.resume_from(session_id, step)`.
3.  **CLI Playback**: The included `replay.py` CLI allows you to view past sessions and step through them frame-by-frame.

```bash
python replay.py list                 # View all past sessions
python replay.py <session-id> <step>  # View a specific session up to a step
```

> See [`examples/19_replay.py`](examples/19_replay.py) for a complete time-travel demonstration.

## 9. Streaming Execution Output

For long-running tasks, waiting for the final output can break the illusion of an active agent. MCPRuntime supports yielding execution outputs line-by-line via Server-Sent Events (SSE).

![Streaming Comparison](assets/streaming_comparison.png)
*Real-time streaming vs traditional blocking execution*

*   **`StreamingExecutor`**: A wrapper that intercepts executor stdout and yields real-time chunks.
*   **SSE API**: Exposed via `POST /execute/stream` on the MCPRuntime HTTP server.

```python
# Stream execution output in real-time
for event in agent.stream_execute(task):
    if event.type == "code_generated":
        print(f"📝 Generated: {event.code}")
    elif event.type == "output":
        print(f"📤 Output: {event.text}")
    elif event.type == "complete":
        print(f"✅ Complete in {event.time}s")
```

> See [`examples/18_streaming.py`](examples/18_streaming.py) for a client-side streaming demo.

## 10. MCPRuntime Benchmark Suite (MRBS)

The **MCPRuntime Benchmark Suite (MRBS)** is a benchmark for evaluating **agent execution runtimes**. Unlike traditional benchmarks that test pre-written code, MRBS tests the complete agent loop: LLM generates code from natural language tasks, the runtime executes it, and validators check correctness.

This provides actionable insights: *How well does OpenSandbox support my agent workload?*

### What MRBS Measures

| Metric | Why It Matters |
|--------|---------------|
| **Agent Success Rate** | % of tasks where LLM-generated code passes validation |
| **Time-to-Success (TTS)** | Total latency from prompt to working output |
| **Iterations Needed** | How many retries for agent to succeed |
| **Category Breakdown** | Per-category success rates reveal workload characteristics |

### Task Taxonomy

All tasks run **with or without** `--recursive`. Some tasks **favor RLM** (optional context + `ask_llm` when recursive).

*   **Programmatic Tool Calling (PTC)** (60): True PTC tasks requiring tool imports (calculator, weather, filesystem, database, HTTP, text, email, calendar, math, transforms, chained workflows)

### Running MRBS

MRBS has **evaluation modes** and an optional **RLM (recursive)** mode:

**1. LLM Mode (Realistic Agent Evaluation)**
```bash
# LLM generates code from natural language prompts
python -m benchmarks run --backend opensandbox --llm-provider azure_openai

# With --recursive: tasks that favor RLM get CONTEXT_DATA + ask_llm; others unchanged
python -m benchmarks run --backend opensandbox --llm-provider azure_openai --recursive
# Without --recursive: same tasks run with CONTEXT_DATA only (no ask_llm)

# Results: ~70-90% pass rate (realistic - LLMs make mistakes!)
```

**2. Baseline Mode (Infrastructure Verification)**
```bash
# Runs hand-written reference code (no LLM). Tasks with context get CONTEXT_DATA injected.
python -m benchmarks run --backend opensandbox --llm-provider none

# Results: ~75-80% pass rate on PTC easy tasks (expected with LLM)
```

**Backend:**
- **OpenSandbox** (Docker via server): ~75-80% pass rate on PTC easy tasks, ~3s per task. Full PTC support.

> See **[MRBS Guide](docs/benchmark_guide.md)** for statistical rigor, reporting guidelines, and detailed taxonomy.

## 11. Development and Testing

See **[CONTRIBUTING.md](CONTRIBUTING.md)** for setup and contribution guidelines.

```bash
make install-dev    # Install with dev deps
make env            # Copy .env.example → .env (add your API keys)
make test           # Unit + integration (no API key needed)
make test-e2e       # E2E with real LLM (requires .env)
make test-all       # Full suite
```

Without Make: `python -m pytest tests/ -v -m "not live"` for unit+integration; `python -m pytest tests/e2e/ -v` for live E2E (requires `.env`).

## 12. References & Inspiration

MCPRuntime stands on the shoulders of giants.

*   **[Code Actions as Tools: Evolving Tool Libraries for Agents](https://gradion-ai.github.io/agents-nanny/2025/12/16/code-actions-as-tools-evolving-tool-libraries-for-agents/)** — The conceptual foundation for the Skill Evolution / Self-Growing Tool Library feature. Introduces the idea that working code actions should be saved as typed, discoverable tools rather than discarded after execution.
*   **[Anthropic: Code Execution with MCP](https://www.anthropic.com/engineering/code-execution-with-mcp)** — The Programmatic Tool Calling pattern: tools as importable code, not JSON schemas.
*   **[Cloudflare: Code Mode](https://blog.cloudflare.com/code-mode/)** — Production-scale implementation of code-based tool calling.
*   **[Recursive Language Models](https://arxiv.org/abs/2512.24601)** — Research into infinite context processing via recursive querying.
*   ~~[Microsandbox](https://github.com/TJKlein/microsandbox)~~ — (Not currently integrated due to SDK compatibility issues)
*   **[OpenSandbox](https://github.com/alibaba/OpenSandbox)** — Docker/Kubernetes-based local sandbox platform by Alibaba.

## Supporting the Project

If you find MCPRuntime useful, please consider starring the repository on GitHub. Stars help others discover the project and signal interest to the maintainers.

### Citation

If you use MCPRuntime or PTC-Bench in your research, please cite:

```bibtex
@software{ptcbench2025,
  title = {PTC-Bench: The Programmatic Tool Calling Benchmark},
  author = {Klein, Tassilo},
  year = {2025},
  url = {https://github.com/TJKlein/mcpruntime}
}
```

## License

MIT &copy; 2026 MCPRuntime Team. Developed with the support of the **[Mantix](https://mantix.cloud)** AI Team.

*Please note: MCPRuntime relies on third-party open-source components such as OpenSandbox, which are licensed under the Apache License 2.0. See the `NOTICE` and `LICENSE` files for full details and attribution.*
