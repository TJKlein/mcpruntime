"""Data schemas for the benchmark suite."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Task:
    """A benchmark task definition."""
    
    # Fields without Defaults (must come first in dataclasses)
    id: str
    difficulty: str
    name: str
    description: str
    validation_type: str
    
    # Fields with Defaults
    category: str = "uncategorized"
    reference_code: str = ""
    expected_output: Optional[str] = None
    custom_validator: Optional[str] = None
    
    # Dynamic LLM Evaluation Fields (Agent Loop)
    prompt: Optional[str] = None
    max_retries: int = 3
    
    setup_files: List[Dict[str, str]] = field(default_factory=list)
    supported_backends: List[str] = field(default_factory=list)
    timeout: int = 30
    tags: List[str] = field(default_factory=list)
    min_score: float = 1.0
    # RLM (Recursive Language Model): path to fixture file for CONTEXT_DATA (relative to category fixtures/)
    context_data_source: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """Create a Task from a dictionary."""
        # The provided from_dict snippet is a complete rewrite,
        # so we'll use it and adjust variable names and remove non-dataclass fields.
        # Also, ensure all dataclass fields are handled.
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            difficulty=data.get("difficulty", "medium"),
            tags=data.get("tags", []),
            timeout=data.get("timeout", 10),
            supported_backends=data.get("supported_backends", ["opensandbox", "microsandbox", "monty"]),
            min_score=data.get("min_score", 1.0),
            expected_output=data.get("expected_output", None),
            custom_validator=data.get("custom_validator", None), # Added: custom_validator
            validation_type=data.get("validation_type", "exact"),
            # validation_params is not a field in the dataclass, so it's removed.
            category=data.get("category", "uncategorized"),
            reference_code=data.get("reference_code", ""),
            prompt=data.get("prompt", None),
            max_retries=data.get("max_retries", 3),
            setup_files=data.get("setup_files", []),
            context_data_source=data.get("context_data_source", None),
        )


@dataclass
class TaskResult:
    """Result of a single benchmark task execution."""
    task_id: str
    task_name: str
    category: str
    difficulty: str
    success: bool
    score: float
    execution_time: float     # Substrate runtime ONLY
    output: str
    error: Optional[str]
    validation: Dict[str, Any]
    backend: str
    timestamp: float
    skipped: bool = False
    skip_reason: Optional[str] = None
    
    # Agentic Evaluation Metrics
    iterations: int = 1
    total_time: float = 0.0   # TTS (Time-To-Success including LLM latency)
    llm_generation_time: float = 0.0
    final_error: Optional[str] = None


@dataclass
class BenchmarkMetrics:
    """Aggregate metrics for a benchmark run."""
    
    # Overall
    total_tasks: int
    attempted_tasks: int
    passed_tasks: int
    failed_tasks: int
    skipped_tasks: int
    pass_rate: float
    avg_score: float
    
    # Performance
    avg_execution_time: float
    median_execution_time: float
    p95_execution_time: float
    total_wall_time: float
    
    # Reliability
    timeout_count: int
    error_count: int
    
    # Breakdowns
    category_breakdown: Dict[str, Dict[str, Any]]
    difficulty_breakdown: Dict[str, Dict[str, Any]]
    
    # Agentic Evaluation Metrics
    avg_iterations: float = 1.0
    avg_time_to_success: float = 0.0 # Total time including LLM
    avg_llm_generation_time: float = 0.0
