# MRBS: Detailed Benchmark Analysis

## Executive Summary

The **MCPRuntime Benchmark Suite (MRBS)** is a comprehensive evaluation framework for **agent execution runtimes**. Unlike traditional benchmarks that test pre-written code, MRBS tests the complete **agent loop**: LLM generates code from natural language prompts, the runtime executes it, and validators check correctness.

## What MRBS Measures

### Core Philosophy

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Natural Lang   │ --> │   LLM Generates  │ --> │ Runtime Executes│ --> │ Validate Output │
│  Task Prompt    │     │   Python Code    │     │   in Sandbox    │     │   vs Expected   │
└─────────────────┘     └──────────────────┘     └─────────────────┘     └─────────────────┘
         ↑                                                                            │
         └──────────────────── Agent Loop (retry on failure) ←────────────────────────┘
```

This tests what happens **after** the LLM writes code: Will it run? How fast? Does it produce correct output?

### Evaluation Metrics

| Metric | Definition | Why It Matters |
|--------|------------|----------------|
| **Success Rate** | % of tasks where generated code passes validation | Can the backend support agent workflows? |
| **Time-to-Success (TTS)** | Total time from prompt to valid output | User-perceived agent latency |
| **Iterations Needed** | How many LLM retries required | Agent robustness on this backend |
| **LLM Generation Time** | Time spent in LLM API calls | LLM overhead (varies by provider) |
| **Execution Time** | Time spent running generated code | Runtime efficiency |
| **Score** | 0.0-1.0 validation score | Partial credit for fuzzy matches |

### Two Evaluation Modes

**1. Baseline Mode (`--llm-provider none`)**
- Runs hand-written reference code
- Should achieve ~100% pass rate
- Measures pure runtime speed without LLM variability
- Used to verify benchmark infrastructure

**2. LLM Mode (`--llm-provider azure_openai`)**
- LLM generates code from natural language prompts
- Pass rates typically 70-90% (not 100%)
- Realistic agent performance measurement
- Shows actual agent capabilities

---

## Task Taxonomy

### Current Task Inventory: 75 Tasks Across 6 Categories

| Category | Count | Purpose | Example Tasks |
|----------|-------|---------|---------------|
| **Compute** | 19 | Algorithmic CPU-bound tasks | FizzBuzz, Sorting, DP, TSP |
| **Import-Heavy** | 12 | Package loading & data processing | pandas, numpy workflows |
| **I/O** | 12 | Filesystem operations | Read/write, temp files, directories |
| **Memory** | 10 | Allocation patterns | Large lists, dicts, object creation |
| **Concurrency** | 10 | Threading & async | Threads, async/await, multiprocessing |
| **Enterprise** | 16 | Real-world patterns | ETL, state machines, retry logic |

### Compute Tasks Deep Dive (19 Tasks)

The compute category is the most mature and tested. Tasks are organized by difficulty:

#### Easy Tasks (5 tasks) - Basic Algorithms

| ID | Name | Description | Validation |
|----|------|-------------|------------|
| A01 | FizzBuzz 1-1000 | Branch prediction, string formatting | Exact match |
| A02 | Fibonacci(30) | Iterative loops | Exact match |
| A03 | Palindrome batch | String operations (1000 strings) | Exact match |
| A04 | Sum of primes < 10,000 | Basic arithmetic | Exact match |
| A05 | List comprehension (100k) | Allocation and iteration | Exact match |

**Example A01 (FizzBuzz):**
```python
# Prompt: "Standard FizzBuzz to 1000. Make sure your script prints EXACTLY..."
# Expected output: 1\n2\nFizz\n4\nBuzz\n... (1000 lines)

def fizzbuzz(n):
    res = []
    for i in range(1, n + 1):
        if i % 15 == 0: res.append('FizzBuzz')
        elif i % 3 == 0: res.append('Fizz')
        elif i % 5 == 0: res.append('Buzz')
        else: res.append(str(i))
    return '\n'.join(res)

print(fizzbuzz(1000))
```

#### Medium Tasks (5 tasks) - Intermediate Algorithms

| ID | Name | Description | Key Concepts |
|----|------|-------------|--------------|
| A06 | Binary search (1M elements) | Divide-and-conquer search | O(log n) algorithms |
| A07 | Merge sort (10k elements) | Recursive sorting | Divide-and-conquer |
| A08 | Quicksort (10k elements) | In-place partitioning | Average-case O(n log n) |
| A09 | Sieve of Eratosthenes | Prime generation | Array marking |
| A10 | Matrix multiplication (500x500) | Dense linear algebra | Nested loops, arithmetic |

**Example A07 (Merge Sort):**
```python
# Tests: recursion, array manipulation, divide-and-conquer
# Prompt explicitly requests merge sort algorithm

def merge_sort(arr):
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    return merge(left, right)

def merge(left, right):
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result

arr = list(range(9999, -1, -1))  # Descending 0-9999
result = merge_sort(arr)
print(f'Sorted first 3: {result[:3]}')
print(f'Sorted last 3: {result[-3:]}')
# Expected: "Sorted first 3: [0, 1, 2]\nSorted last 3: [9997, 9998, 9999]\n"
```

#### Hard Tasks (9 tasks) - Advanced Algorithms

| ID | Name | Description | Complexity |
|----|------|-------------|------------|
| A11 | N-Queens (10x10) | Backtracking, constraint satisfaction | NP-hard |
| A12 | Sudoku solver | Constraint propagation, backtracking | NP-hard |
| A13 | Longest Common Subsequence | 2D dynamic programming | O(n²) time, O(n²) space |
| A14 | Edit Distance (Levenshtein) | DP with optimization | O(n²) |
| A15 | Matrix Chain Multiplication | DP with memoization | O(n³) |
| A16 | TSP (14 cities) | Greedy nearest neighbor | NP-hard approximation |
| A17 | Fast Fourier Transform | Complex arithmetic, recursion | O(n log n) |
| A18 | Knapsack 0/1 | DP with space optimization | O(n×W) |
| A19 | Regex engine | State machines, backtracking | Pattern matching |

**Example A16 (TSP - Traveling Salesman):**
```python
# Tests: graph traversal, greedy algorithms, optimization
# Note: Uses greedy nearest neighbor (not optimal Held-Karp)

def tsp_greedy(dist):
    n = len(dist)
    visited = [False] * n
    visited[0] = True
    total_cost = 0
    current = 0
    
    for _ in range(n - 1):
        nearest = None
        min_dist = float('inf')
        for i in range(n):
            if not visited[i] and dist[current][i] < min_dist:
                min_dist = dist[current][i]
                nearest = i
        visited[nearest] = True
        total_cost += min_dist
        current = nearest
    
    total_cost += dist[current][0]  # Return to start
    return total_cost

n = 14
dist = [[0] * n for _ in range(n)]
for i in range(n):
    for j in range(n):
        if i != j:
            dist[i][j] = abs(i - j) * 10 + (i * 7 + j * 3) % 17

result = tsp_greedy(dist)
print(f'TSP tour distance: {result}')
# Expected: "TSP tour distance: 354\n"
```

---

## Task Structure Definition

Each task is defined as a JSON object with the following schema:

```json
{
  "id": "A01",
  "name": "FizzBuzz 1–1000",
  "difficulty": "easy",
  "description": "Standard FizzBuzz to 1000. Tests branch prediction.",
  "supported_backends": ["monty", "opensandbox", "docker"],
  "validation_type": "exact",
  "tags": ["cpu", "branching"],
  "reference_code": "def fizzbuzz(n): ...",
  "expected_output": "1\n2\nFizz\n4\nBuzz\n...",
  "prompt": "Standard FizzBuzz to 1000. Make sure your script prints EXACTLY...",
  "timeout": 30,
  "min_score": 1.0
}
```

### Field Descriptions

| Field | Purpose | Example |
|-------|---------|---------|
| `id` | Unique identifier | A01, A02, ... |
| `name` | Human-readable name | "FizzBuzz 1-1000" |
| `difficulty` | easy/medium/hard | Classification for analysis |
| `description` | What the task tests | Technical justification |
| `supported_backends` | Which runtimes can execute | Backend compatibility |
| `validation_type` | How to check correctness | exact/fuzzy/custom |
| `tags` | Categorization keywords | cpu, dp, recursion |
| `reference_code` | Hand-written correct implementation | Baseline for `--llm-provider none` |
| `expected_output` | Correct stdout output | Exact match target |
| `prompt` | Natural language for LLM | Agent task description |
| `timeout` | Max execution seconds | 30 (default) |
| `min_score` | Minimum passing score | 1.0 = 100% exact |

---

## Validation Strategies

### 1. Exact Match (`validation_type: "exact"`)

Most compute tasks use exact string comparison:

```python
def _exact_match(expected, output):
    is_match = expected.strip() == output.strip()
    return is_match, 1.0 if is_match else 0.0, details
```

**Used by:** 18/19 compute tasks
**Why:** Deterministic algorithms produce exact outputs

### 2. Fuzzy Match (`validation_type: "fuzzy"`)

For outputs with floating-point values:

```python
def _fuzzy_match(expected, output):
    # 1. Normalize whitespace and case
    # 2. Try exact match after normalization
    # 3. Extract floats and compare with tolerance (1e-5)
    # 4. Return partial credit if close
```

**Used by:** Scientific computing tasks
**Why:** Floating point precision varies across systems

### 3. Custom Validators (`validation_type: "custom"`)

For complex validation logic:

```python
# Located in benchmarks/tasks/{category}/validators.py
def validate_matrix_result(task, output):
    # Parse output
    # Check matrix dimensions
    # Verify values within tolerance
    return passed, score, details
```

**Used by:** Import-heavy, I/O, Enterprise tasks
**Why:** Complex data structures need domain-specific validation

---

## Backend Support Matrix

### Compute Task Support (19 tasks)

| Backend | Tasks Passed | Tasks Skipped | Speed | Notes |
|---------|--------------|---------------|-------|-------|
| **Docker** | 19/19 (100%) | 0 | ~0.4s | ✅ Recommended |
| **OpenSandbox** | 19/19 (100%) | 0 | ~3s | Full orchestration |
| **Monty** | 9/9 (100%) | 10 | ~0.4s | Compute-only |
| **Subprocess** | 19/19 (100%) | 0 | ~0.2s | No isolation |
| **Microsandbox** | N/A | N/A | N/A | ❌ SDK blocked |

### Why Monty Skips Some Tasks

Monty is an in-process Python AST interpreter with limitations:

```python
# Monty CANNOT execute:
- Complex subscript assignments: a[0], a[1] = 1, 2
- Multiple assignments: a, b = b, a  
- Some list comprehensions with complex expressions
- I/O operations (file system access)
- Import statements (no package support)
```

Tasks A07, A09, A10, A11, A12, A15 are skipped for Monty because they use unsupported Python features.

---

## Realistic LLM Pass Rates

### Sample Run (gpt-5.2-chat on OpenSandbox)

| Difficulty | Tasks Tested | Passed | Pass Rate | Avg LLM Time |
|------------|--------------|--------|-----------|--------------|
| Easy | 2 | 2 | 100% | 7s |
| Medium | 2 | 1 | 50% | 25s |
| Hard | 2 | 2 | 100% | 20s |
| **Overall** | **6** | **5** | **83%** | **17s** |

### Expected Ranges

| Difficulty | Expected Pass Rate | Why |
|------------|---------------------|-----|
| Easy | 90-100% | Simple algorithms, usually correct |
| Medium | 50-85% | More complex, occasional logic errors |
| Hard | 60-100% | Complex but often succeed with good models |
| **Overall** | **70-90%** | Depends on model quality |

**Key Insight:** Lower pass rates in LLM mode are **expected and realistic** - they show genuine agent capabilities, not benchmark flaws.

---

## Benchmark Runner Architecture

### Execution Flow

```
1. Load tasks from benchmarks/tasks/{category}/tasks.json
2. Filter by --categories and --backend support
3. For each task:
   a. Generate LLM prompt (or use reference_code if --llm-provider none)
   b. Call LLM API (if enabled)
   c. Extract Python code from LLM response
   d. Execute in selected backend sandbox
   e. Capture stdout/stderr
   f. Validate output against expected_output
   g. If failed and retries < max_retries:
      - Add error to prompt context
      - Retry from step b
   h. Record TaskResult
4. Compute aggregate BenchmarkMetrics
5. Generate report (console or markdown)
```

### Retry Logic

```python
max_retries = 3
for attempt in range(max_retries):
    code = generate_code(task.prompt, context)
    output = execute(backend, code)
    passed, score, details = validate(task, output)
    
    if passed:
        break
    else:
        context += f"\nPrevious attempt failed: {details}"
        
iterations = attempt + 1  # Record for metrics
```

This mimics real agent behavior: retry with error context until success or max retries.

---

## Statistical Rigor

### Multiple Runs (`--runs N`)

For statistical significance, run each task multiple times:

```bash
python -m benchmarks run --backend docker --runs 5
```

This computes:
- Mean, median, P95 execution times
- Variance analysis
- Confidence intervals

### Cold vs Warm Start

| Mode | Behavior | Use Case |
|------|----------|----------|
| Cold start (default) | Fresh sandbox per task | Realistic agent latency |
| Warm start | Reuse sandboxes | Measure pure execution speed |

---

## Practical Usage Examples

### Quick Baseline Test (No LLM)

```bash
# Fastest - verify infrastructure works
python -m benchmarks run --backend docker --llm-provider none
# Result: 100% (19/19) in ~7 seconds
```

### Real LLM Evaluation

```bash
# Actual agent performance (takes longer)
python -m benchmarks run --backend docker --llm-provider azure_openai
# Result: ~70-90% pass rate, ~30-180 seconds
```

### Category-Specific Testing

```bash
# Test only compute tasks
python -m benchmarks run --backend docker --categories compute

# Skip slow/hard tasks for quick iteration
python -m benchmarks run --backend docker --categories compute --exclude A11,A12,A16
```

### Backend Comparison

```bash
# Compare Docker vs Monty
python -m benchmarks compare --backends docker,monty --runs 3
```

---

## Key Insights for Researchers

### 1. Baseline vs LLM Mode Difference

| Mode | Pass Rate | What It Measures |
|------|-----------|------------------|
| Baseline | ~100% | Runtime correctness, infrastructure health |
| LLM | 70-90% | Real-world agent capabilities |

**Don't confuse them!** 100% in baseline is expected. Lower in LLM mode is realistic.

### 2. Backend Selection Tradeoffs

| If You Need... | Use | Because |
|----------------|-----|---------|
| Fastest benchmark runs | Docker | 0.4s/task, 100% compatibility |
| Full agent orchestration | OpenSandbox | Volume mounts, networking, multi-step |
| Pure compute speed tests | Monty | In-process, no container overhead |
| No isolation concerns | Subprocess | Fastest, but unsafe |

### 3. Task Difficulty Calibration

The 19 compute tasks span a meaningful difficulty range:

- **Easy (A01-A05):** Any junior developer can solve
- **Medium (A06-A10):** Standard interview questions  
- **Hard (A11-A19):** Classic algorithms, NP-hard problems

This provides signal for distinguishing:
- Model quality (better models score higher)
- Backend suitability (some backends fail specific task types)
- Runtime performance (execution time varies by task complexity)

---

## Conclusion

MRBS is designed to answer: **"Which backend should I use for my agent workload?"**

It measures the complete agent loop end-to-end, from natural language prompt to validated execution. The 19 compute tasks provide a robust test of algorithmic code generation, while the 75 total tasks across 6 categories cover broader agent capabilities.

**For practical benchmarking:**
- Use **Docker** for most cases (fast, compatible, simple)
- Use **baseline mode** to verify infrastructure
- Use **LLM mode** for realistic agent evaluation
- Expect **70-90%** pass rates with LLMs (not 100% - that's normal!)
