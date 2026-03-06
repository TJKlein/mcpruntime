"""
MCPRuntime Benchmark Suite (MRBS)

A runtime-first benchmark that measures execution speed, sandbox overhead, 
and backend tradeoffs.
"""

# Re-export key components
from .tasks.schema import Task, TaskResult, BenchmarkMetrics

__version__ = "0.1.0"
__all__ = ["Task", "TaskResult", "BenchmarkMetrics"]
