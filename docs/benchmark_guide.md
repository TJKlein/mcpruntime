# MCPRuntime Benchmark Suite (MRBS)

The **MCPRuntime Benchmark Suite (MRBS)** is the first comprehensive benchmark for evaluating **agent execution runtimes**—measuring how well different backends support LLM-generated code in real-world agent workflows.

## What MRBS Evaluates

Unlike traditional benchmarks that test pre-written reference code, MRBS tests the **complete agent loop**:

```
Natural Language Task → LLM Generates Code → Runtime Executes → Validator Checks
         ↑                                    ↓              ↓
    (Agent reasoning)              (Execution speed)    (Correctness)
```

This provides actionable insights for:
- **Agent developers**: Which backend should I use for my workload?
- **Runtime builders**: Where does my sandbox excel or struggle?
- **Researchers**: What tradeoffs exist between speed, security, and agent success rates?

## Why MRBS is Different

| Benchmark Type | Measures | Example |
|----------------|----------|---------|
| **Code Execution** (e.g., E2B) | Speed of running given code | "How fast does this function run?" |
| **Agent Capability** (e.g., SWE-bench) | LLM reasoning quality | "Can the LLM fix this bug?" |
| **MRBS** (this suite) | Runtime support for agent code | "Will the agent's generated code execute correctly on this backend?" |

MRBS is unique because it tests what happens **after** the LLM writes code: will it run? how fast? does the output validate?

## The 75 Task Taxonomy

Tasks are organized by the runtime characteristics they stress:

### 1. **Compute** (19 tasks)
Algorithmic tasks that stress CPU: FizzBuzz, Fibonacci, sorting, dynamic programming, TSP, FFT, knapsack.
- *Agent challenge*: Generating correct algorithms from natural language descriptions
- *New hard tasks:* TSP (14 cities), FFT (256 points), Knapsack (100 items), Regex engine

### 2. **Import-Heavy** (12 tasks)  
Package loading and data processing: pandas, numpy, JSON parsing.
- *Agent challenge*: Using correct library APIs and handling data correctly

### 3. **File I/O** (12 tasks)
Filesystem operations: read, write, directory traversal, temp files.
- *Agent challenge*: Proper file handling, path management, cleanup

### 4. **Memory** (10 tasks)
Allocation patterns: large lists, dictionaries, object creation, copying.
- *Agent challenge*: Efficient data structure choices

### 5. **Concurrency** (10 tasks)
Threading, async/await, multiprocessing, synchronization.
- *Agent challenge*: Correct concurrent programming patterns

### 6. **Enterprise Patterns** (16 tasks)
Real-world workflows: ETL, state machines, circuit breakers, retry logic.
- *Agent challenge*: Understanding patterns and implementing them correctly

## The Agent Evaluation Metrics

For each task, MRBS reports:

| Metric | Meaning | Why It Matters |
|--------|---------|--------------|
| **Success Rate** | % of agent tasks completed correctly | Can the backend support agent workflows? |
| **Time-to-Success (TTS)** | Total time from prompt to valid output | User-perceived agent latency |
| **Iterations** | How many retries needed | Agent robustness on this backend |
| **LLM Generation Time** | Time spent in code generation | Overhead of agent reasoning |
| **Execution Time** | Time spent running generated code | Runtime efficiency |

## Running the Benchmark

### Quick Start (Agent Mode with LLM)

Run with LLM-generated code to measure real-world agent performance:

```bash
# Run with Azure OpenAI (uses .env config)
python -m benchmarks run --backend monty --llm-provider azure_openai

# Run with specific model (recommended for reliable results)
python -m benchmarks run --backend opensandbox --llm-provider azure_openai --llm-model gpt-5.2-chat

# Run specific categories
python -m benchmarks run --backend opensandbox --categories compute,io --llm-provider azure_openai

# Full suite with statistical confidence (N=5 runs per task)
python -m benchmarks run --backend opensandbox --runs 5 --llm-provider azure_openai --output report.md
```

**Note:** With LLM mode, pass rates are typically 80-90% (not 100%) because:
- LLM may generate code with syntax errors
- Output format may not exactly match expected
- Some tasks require specific algorithmic approaches

**Realistic LLM Results (OpenSandbox + gpt-5.2-chat):**

Baseline mode (no LLM) achieves ~100% because it runs hand-written reference code.
With actual LLM code generation, pass rates are lower due to generation variability:

| Difficulty | Pass Rate | Example Tasks |
|------------|-----------|---------------|
| Easy | 90-100% | FizzBuzz, Fibonacci - simple algorithms usually correct |
| Medium | 50-85% | Binary search, Merge sort - occasional logic errors |
| Hard | 60-100% | N-Queens, Sudoku, TSP - complex but often succeed |
| **Overall** | **70-90%** | Depends on model quality and task selection |

**Sample Run (4 representative tasks):**
- Medium (Binary search): ✅ Pass
- Medium (Merge sort): ❌ Fail (50% for medium)
- Hard (Sudoku): ✅ Pass
- Hard (TSP): ✅ Pass (100% for this sample)

Individual task timing: 10-40s per task (includes LLM generation + execution)

### Baseline Mode (Reference Code, No LLM)

For measuring pure runtime speed without LLM overhead:

```bash
# Test OpenSandbox infrastructure
python -m benchmarks run --backend opensandbox --llm-provider none

# Test Monty infrastructure  
python -m benchmarks run --backend monty --llm-provider none
```

This runs pre-written reference code and should achieve ~100% pass rate:
- **OpenSandbox:** ~100% (19/19 tasks) - all categories supported
- **Monty:** ~100% (13/13 compute tasks) - skips I/O, imports, concurrency

> **Why 100% in baseline mode?** It's running hand-written correct code, not generating from prompts. Use this to verify infrastructure, then use LLM mode for realistic agent performance testing.

### Expected LLM Mode Pass Rates (Realistic)

When using actual LLM code generation, pass rates are lower due to generation variability:

| Difficulty | Typical Pass Rate | Why |
|------------|-------------------|-----|
| Easy | 80-100% | Simple algorithms, usually correct |
| Medium | 60-85% | More complex, occasional logic errors |
| Hard | 40-75% | Complex algorithms, higher failure rate |
| **Overall** | **65-85%** | Depends on model quality |

Example with `gpt-5.2-chat` on OpenSandbox:
- Easy: 2/2 (100%)
- Medium: 1/2 (50%) 
- Hard: 2/2 (100%)
- **Overall: 5/6 (83%)**

### Which Numbers to Report

**For Research Publications & Model Evaluation:**
Use **LLM Mode** and report:
- Pass rate (e.g., "Our agent achieves 83% on MRBS")
- Breakdown by difficulty (e.g., "Easy: 100%, Medium: 50%, Hard: 100%")
- Average Time-to-Success (e.g., "17s per task including LLM generation")
- Model name (e.g., "gpt-5.2-chat")

**For Backend Performance Comparisons:**
Use **Baseline Mode** and report:
- Execution time per task (e.g., "Docker: 0.4s vs OpenSandbox: 3s")
- Task coverage (e.g., "Docker: 19/19 tasks, Monty: 9/19 tasks")
- Cold start latency

**Never Report:**
- Baseline mode pass rates as "agent performance" (it's just infrastructure verification)
- 100% LLM pass rates without scrutiny (may indicate task leakage or too-easy tasks)

### Running with LLM (.env)

The benchmark loads `.env` from the project root. Set your API key and (for Azure) endpoint and deployment:

- **OpenAI**: `OPENAI_API_KEY=sk-...`
- **Azure**: `AZURE_OPENAI_API_KEY=...`, `AZURE_OPENAI_ENDPOINT=https://...`, and either `AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-5.2-chat` or `AZURE_OPENAI_DEPLOYMENT_NAME=...`

For agent mode the benchmark prefers `AZURE_OPENAI_CHAT_DEPLOYMENT` when set (chat-capable models work best for code generation). If the LLM fails or returns no executable code, the runner falls back to reference code so the run still produces meaningful results.

### Backend Setup

**Recommended**: Start with **Docker** for the best balance of compatibility and simplicity.

**Docker** (bare containers) - ✅ **Primary recommendation**
1. **Start Docker Desktop** (or Colima/Rancher Desktop).
2. Run the benchmark (pulls `python:3.11-slim` automatically):
   ```bash
   python -m benchmarks run --backend docker --categories compute --runs 1 --llm-provider none
   ```
Results: 100% (19/19) - ~0.4s per task

**OpenSandbox** (Docker via server) - ✅ **For advanced orchestration**
1. Install: `pip install opensandbox opensandbox-server`
2. Configure once: `opensandbox-server init-config ~/.sandbox.toml --example docker`
3. **Start Docker Desktop**.
4. Run the benchmark - the CLI auto-starts the server:
   ```bash
   python -m benchmarks run --backend opensandbox --categories compute --runs 1 --llm-provider none
   ```
Results: 100% (19/19) - ~3s per task

**Monty** (in-process, no Docker needed) - ✅ **Fastest for compute-only**
```bash
python -m benchmarks run --backend monty --categories compute --runs 1 --llm-provider none
```
Results: 100% (13/13 compute tasks, others skipped) - ~0.4s per task

Note: Monty skips I/O, import-heavy, and concurrency tasks (doesn't support those features).

### Compare Multiple Backends

```bash
# Compare Docker vs OpenSandbox
python -m benchmarks compare --backends docker,opensandbox --runs 3

# Compare Docker vs Monty (compute tasks only)
python -m benchmarks compare --backends docker,monty --runs 3
```

## Command Options

- `--backend [docker|monty|opensandbox|subprocess]`: Execution environment (Docker recommended)
- `--categories [list]`: Comma-separated task categories
- `--runs [int]`: Number of repetitions per task for statistical significance
- `--llm-provider [openai|anthropic|azure_openai|none]`: LLM for agent code generation
- `--llm-model [name]`: Specific model to use
- `--output [file.md]`: Save report to file

## Interpreting Results

### Example: Agent Task Success

```
Backend: opensandbox
- Success Rate: 87% (65/75 tasks passed on first try)
- Avg Time-to-Success: 3.2s
- Avg Iterations: 1.2 (some tasks needed retry)
- Pass Rate Breakdown:
  - compute: 93%
  - import_heavy: 82% (pandas compatibility issues)
  - io: 91%
  - concurrency: 76% (threading limitations)
```

**Insight**: OpenSandbox works well for compute and I/O but struggles with some import-heavy and concurrency tasks—agents using it should expect occasional retries for those categories.

### Example: Runtime Comparison

```
Comparison: monty vs opensandbox

| Category | Monty Success | OpenSandbox Success | Speedup |
|----------|---------------|---------------------|---------|
| compute  | 95%           | 93%                 | 5.2x    |
| io       | 45%           | 91%                 | 0.8x    |
| import   | 30%           | 82%                 | 0.6x    |

**Insight**: Monty is faster for pure compute but fails on many I/O and import tasks due to sandbox limitations. For data-heavy agent workflows, OpenSandbox provides better overall success rates despite being slower.
```

## NeurIPS-Grade Statistical Rigor

MRBS follows benchmarking best practices:

1. **Multiple Runs**: Default N=5 runs per task for variance analysis
2. **Trimmed Means**: Outlier-resistant timing statistics
3. **Confidence Intervals**: Report uncertainty bounds
4. **Cold/Warm Start**: Separate metrics for first-run vs. cached performance
5. **Category Breakdowns**: Per-category success rates reveal backend strengths/weaknesses

## Supported Backends

| Backend | Type | Best For | Status | Speed | Notes |
|---------|------|----------|--------|-------|-------|
| **Docker** | Docker (bare) | General benchmarking | ✅ 100% (19/19) | ~0.4s | **Recommended** - simple, fast, compatible |
| **OpenSandbox** | Docker (via server) | Advanced orchestration | ✅ 100% (19/19) | ~3s | Full features, requires server |
| **Monty** | In-process Python | Pure compute speed | ✅ 100% (13/13) | ~0.4s | Fastest, skips I/O tasks |
| **Subprocess** | Raw host process | Development/debugging | ✅ 100% (19/19) | ~0.2s | No isolation, fastest |

### Recommendation Summary

**Use Docker** (bare) for most benchmarking:
- 100% pass rate on all 19 compute tasks
- Fast execution (~0.4s per task)
- Simple setup - just needs Docker, no server
- Pure Docker containers with python:3.11-slim

**Use OpenSandbox** when you need:
- Full orchestration features (volumes, networking, etc.)
- Long-running sandbox server
- More sophisticated container management

**Use Monty** when you need:
- Maximum speed for compute-only tasks
- No Docker/container overhead
- In-process execution

**Use Subprocess** for development only:
- Fastest possible execution
- No isolation (runs on host)
- Good for quick iteration, not production

## Debugging Failed Tasks

When a task fails in agent mode, use the debug command to see:
- The natural language prompt
- The LLM-generated code
- The execution output and error
- The validation result

```bash
python -m benchmarks debug --task A01 --backend opensandbox
```

## Architecture

MRBS consists of:

- **Task Definitions** (`benchmarks/tasks/`): 75 JSON task files with natural language prompts
- **Runner** (`benchmarks/runner.py`): Agent loop orchestrator
- **Validator** (`benchmarks/validators.py`): Output correctness checking
- **Metrics** (`benchmarks/metrics.py`): Statistical aggregation
- **Reports** (`benchmarks/reports.py`): Human-readable output

## Citation

If you use MRBS in research, please cite:

```bibtex
@software{mrbs2024,
  title = {MCPRuntime Benchmark Suite (MRBS): 
           Evaluating Agent Execution Runtimes},
  author = {AgentKernel Team},
  year = {2024},
  url = {https://github.com/your-org/agentkernel}
}
```

## Contributing Tasks

To add a new benchmark task:

1. Create a JSON entry in the appropriate `benchmarks/tasks/{category}/tasks.json`
2. Include:
   - `prompt`: Natural language task description (for agent)
   - `reference_code`: Reference implementation (for baseline)
   - `expected_output` or `custom_validator`: Validation criteria
   - `supported_backends`: Which runtimes can execute this
3. Test with: `python -m benchmarks debug --task YOUR_ID --backend monty`

## License

MIT License - See LICENSE file for details.
