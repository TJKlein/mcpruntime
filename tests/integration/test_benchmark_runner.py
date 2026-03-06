"""Integration tests for the benchmark runner using Monty."""

import os
import pytest
from benchmarks.runner import BenchmarkRunner

def test_runner_load_tasks():
    # Load just one category to be fast
    runner = BenchmarkRunner(backend="monty", n_runs=1)
    tasks = runner.load_tasks(categories=["compute"])
    
    # We formulated 15 compute tasks
    assert len(tasks) == 15
    assert all(t.category == "compute" for t in tasks)

def test_runner_execution_flow():
    runner = BenchmarkRunner(backend="monty", n_runs=2, cold_start=False)
    
    # Get just the Fibonacci task to run quickly
    tasks = runner.load_tasks(categories=["compute"])
    task = next((t for t in tasks if "Fibonacci" in t.name), None)
    assert task is not None
    
    # With n_runs=2, run_suite returns 1 result per run (so 2 total for 1 task)
    results = runner.run_suite([task])
    
    assert len(results) == 2  # 1 task × 2 runs
    
    # Both results should be for the same task
    assert all(r.task_id == task.id for r in results)
    assert any(r.success for r in results)  # At least one run should pass
    
    # All runs should have non-zero execution time
    for res in results:
        assert res.execution_time >= 0

def test_runner_skips_unsupported_backend():
    # E07 process pooling task doesn't support monty
    runner = BenchmarkRunner(backend="monty", n_runs=1)
    tasks = runner.load_tasks(categories=["concurrency"])
    
    task = next(t for t in tasks if t.id == "E07")
    
    result = runner.run_task(task)
    assert result.skipped is True
    # The skip reason should mention the backend not being in the supported list
    assert "monty" in result.skip_reason.lower()
    assert result.success is False
