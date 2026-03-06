"""Debug utility for running a single task."""

import json
from pathlib import Path
from pprint import pprint

from .runner import BenchmarkRunner
from .metrics import compute_metrics
from .reports import ReportGenerator
from .tasks.schema import Task

def debug_task(task_id: str, backend: str = "monty"):
    """Run a single task with verbose output."""
    
    print(f"==========================================")
    print(f"🐞 DEBUGGING TASK: {task_id} on {backend.upper()}")
    print(f"==========================================\n")
    
    # 1. Load task
    runner = BenchmarkRunner(backend=backend, cold_start=True)
    all_tasks = runner.load_tasks()
    task = next((t for t in all_tasks if t.id == task_id), None)
    
    if not task:
        print(f"❌ Task {task_id} not found.")
        print(f"Available tasks: {', '.join(t.id for t in all_tasks)}")
        return
        
    print(f"Task Name: {task.name}")
    print(f"Category: {task.category}")
    print(f"Difficulty: {task.difficulty}")
    print(f"Supported Backends: {', '.join(task.supported_backends)}")
    
    if backend not in task.supported_backends:
        print(f"\n⚠️ WARNING: {backend} is not listed in supported_backends for this task.")
        
    print("\n--- Setup Files ---")
    if task.setup_files:
        for f in task.setup_files:
            print(f"- {f['path']} ({'content' if 'content' in f else 'fixture: ' + f.get('source', 'unknown')})")
    else:
        print("None")
        
    print("\n--- Reference Code ---")
    print(task.reference_code)
    
    print("\n--- Expected Output ---")
    print(task.expected_output)
    
    print(f"\n--- Execution ({backend}) ---")
    # 2. Execute task
    result = runner.run_task(task)
    
    print(f"Status: {'✅ PASSED' if result.success else ('⏭️ SKIPPED' if result.skipped else '❌ FAILED')}")
    print(f"Score: {result.score:.2f} / 1.00 (min required: {task.min_score})")
    print(f"Time: {result.execution_time:.3f}s")
    
    if result.skipped:
        print(f"Reason: {result.skip_reason}")
    else:
        print("\n--- Actual Output ---")
        if result.output:
            print(result.output)
        else:
            print("<empty>")
            
        if result.error:
            print("\n--- Error ---")
            print(result.error)
            
        print("\n--- Validation Details ---")
        pprint(result.validation)

    print(f"\n==========================================")
