"""Metric computation and aggregation."""

import statistics
from typing import Dict, List, Any

from .tasks.schema import BenchmarkMetrics, TaskResult


def compute_metrics(results: List[TaskResult]) -> BenchmarkMetrics:
    """Compute aggregate metrics from a list of task results."""
    
    total = len(results)
    if total == 0:
        return BenchmarkMetrics(
            total_tasks=0, attempted_tasks=0, passed_tasks=0,
            failed_tasks=0, skipped_tasks=0, pass_rate=0.0, avg_score=0.0,
            avg_execution_time=0.0, median_execution_time=0.0,
            p95_execution_time=0.0, total_wall_time=0.0,
            timeout_count=0, error_count=0,
            category_breakdown={}, difficulty_breakdown={},
            avg_iterations=0.0, avg_time_to_success=0.0,
            avg_llm_generation_time=0.0
        )
        
    attempted = [r for r in results if not r.skipped]
    skipped = len(results) - len(attempted)
    
    passed = sum(1 for r in attempted if r.success)
    failed = len(attempted) - passed
    pass_rate = passed / len(attempted) if attempted else 0.0
    
    scores = [r.score for r in attempted]
    avg_score = sum(scores) / len(scores) if scores else 0.0
    
    times = [r.execution_time for r in attempted if r.execution_time > 0]
    avg_time = sum(times) / len(times) if times else 0.0
    median_time = statistics.median(times) if times else 0.0
    
    p95_time = 0.0
    if len(times) >= 20:
        p95_time = statistics.quantiles(times, n=20)[18]  # 95th percentile
    elif times:
        p95_time = max(times)
        
    total_time = sum(times)
    
    # Agentic Metrics
    iterations = [getattr(r, "iterations", 1) for r in attempted if r.success]
    avg_iterations = sum(iterations) / len(iterations) if iterations else 0.0
    
    tts_times = [getattr(r, "total_time", r.execution_time) for r in attempted if r.success]
    avg_tts = sum(tts_times) / len(tts_times) if tts_times else 0.0
    
    llm_times = [getattr(r, "llm_generation_time", 0.0) for r in attempted if r.success]
    avg_llm_time = sum(llm_times) / len(llm_times) if llm_times else 0.0
    
    timeouts = sum(1 for r in attempted if "timeout" in (r.error or "").lower())
    errors = sum(1 for r in attempted if not r.success and r.error and "timeout" not in r.error.lower())
    
    # Breakdowns
    cats = {}
    for r in results:
        if r.category not in cats:
            cats[r.category] = {"total": 0, "attempted": 0, "passed": 0, "skipped": 0, "times": []}
        cats[r.category]["total"] += 1
        if r.skipped:
            cats[r.category]["skipped"] += 1
        else:
            cats[r.category]["attempted"] += 1
            if r.success:
                cats[r.category]["passed"] += 1
            cats[r.category]["times"].append(r.execution_time)
            
    for v in cats.values():
        v["pass_rate"] = v["passed"] / v["attempted"] if v["attempted"] else 0.0
        v["avg_time"] = sum(v["times"]) / len(v["times"]) if v["times"] else 0.0
        del v["times"]  # cleanup

    diffs = {}
    for r in results:
        if r.difficulty not in diffs:
            diffs[r.difficulty] = {"total": 0, "attempted": 0, "passed": 0, "skipped": 0, "times": []}
        diffs[r.difficulty]["total"] += 1
        if r.skipped:
            diffs[r.difficulty]["skipped"] += 1
        else:
            diffs[r.difficulty]["attempted"] += 1
            if r.success:
                diffs[r.difficulty]["passed"] += 1
            diffs[r.difficulty]["times"].append(r.execution_time)
            
    for v in diffs.values():
        v["pass_rate"] = v["passed"] / v["attempted"] if v["attempted"] else 0.0
        v["avg_time"] = sum(v["times"]) / len(v["times"]) if v["times"] else 0.0
        del v["times"]

    return BenchmarkMetrics(
        total_tasks=total,
        attempted_tasks=len(attempted),
        passed_tasks=passed,
        failed_tasks=failed,
        skipped_tasks=skipped,
        pass_rate=pass_rate,
        avg_score=avg_score,
        avg_execution_time=avg_time,
        median_execution_time=median_time,
        p95_execution_time=p95_time,
        total_wall_time=total_time,
        timeout_count=timeouts,
        error_count=errors,
        category_breakdown=cats,
        difficulty_breakdown=diffs,
        avg_iterations=avg_iterations,
        avg_time_to_success=avg_tts,
        avg_llm_generation_time=avg_llm_time
    )
