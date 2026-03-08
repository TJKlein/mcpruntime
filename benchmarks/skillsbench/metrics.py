"""
SkillsBench Extended Metrics

Extends standard benchmark metrics with skill-specific evaluations:
1. Skill reusability - how often skills are reused across tasks
2. Skill composability - how well skills compose together
3. Skill ecosystem health - overall quality of the skill library

These metrics address the research gap identified in SkillsBench:
"The field currently lacks metrics for skill reusability, composability,
and maintainability — what's needed is evaluation of skill ecosystems
rather than individual agent runs."
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from collections import defaultdict
import ast

logger = logging.getLogger(__name__)


@dataclass
class SkillQualityMetrics:
    """Metrics for evaluating individual skill quality."""
    skill_name: str
    
    # Code quality
    has_docstring: bool = False
    has_type_hints: bool = False
    num_functions: int = 0
    num_imports: int = 0
    lines_of_code: int = 0
    cyclomatic_complexity: float = 0.0
    
    # Runtime quality
    execution_success_rate: float = 0.0
    avg_execution_time: float = 0.0
    error_types: List[str] = field(default_factory=list)
    
    # Reuse quality
    times_reused: int = 0
    successful_reuses: int = 0
    reuse_success_rate: float = 0.0


@dataclass
class SkillEcosystemMetrics:
    """
    Metrics for evaluating the skill ecosystem as a whole.
    
    This addresses the gap in SkillsBench: measuring not just individual
    skill quality, but how skills work together as a reusable library.
    """
    
    # Ecosystem size
    total_skills: int = 0
    skills_by_category: Dict[str, int] = field(default_factory=dict)
    
    # Reusability metrics
    total_skill_reuses: int = 0
    skills_never_reused: int = 0
    skills_reused_3plus: int = 0
    avg_reuses_per_skill: float = 0.0
    reuse_rate: float = 0.0  # % of tasks that reuse at least one skill
    
    # Composability metrics
    skill_compositions: int = 0  # Tasks using 2+ skills together
    avg_skills_per_composition: float = 0.0
    composition_success_rate: float = 0.0
    
    # Dependency graph metrics
    skill_dependencies: Dict[str, List[str]] = field(default_factory=dict)
    dependency_depth_avg: float = 0.0
    circular_dependencies: int = 0
    
    # Ecosystem health
    skill_coverage: Dict[str, float] = field(default_factory=dict)  # Category coverage
    skill_redundancy: float = 0.0  # Duplicate/similar skills
    ecosystem_diversity: float = 0.0  # Shannon diversity index
    
    # Comparison metrics
    speedup_vs_no_skills: float = 0.0  # % faster than baseline
    cost_reduction_vs_no_skills: float = 0.0  # % cheaper than baseline
    llm_call_reduction_vs_no_skills: float = 0.0  # % fewer LLM calls


@dataclass
class SkillsBenchMetrics:
    """
    Extended metrics for SkillsBench evaluation with 4 conditions.
    
    Tracks standard SkillsBench metrics plus MCPRuntime-specific
    ecosystem metrics.
    """
    
    # Standard SkillsBench metrics (per condition)
    condition: str = ""
    pass_rate: float = 0.0
    avg_execution_time: float = 0.0
    avg_cost: float = 0.0
    avg_retries: float = 0.0
    
    # NEURIPS: Pass@k metrics (strict correctness)
    pass_at_1: float = 0.0  # Pass on first attempt
    pass_at_3: float = 0.0  # Pass in any of 3 attempts
    
    # NEURIPS: Statistical confidence
    pass_rate_ci_low: float = 0.0  # 95% CI lower bound
    pass_rate_ci_high: float = 0.0  # 95% CI upper bound
    n_samples: int = 0  # Total runs
    
    # Condition comparison
    delta_vs_no_skills: float = 0.0  # % point improvement
    delta_vs_curated: float = 0.0
    delta_vs_self_generated: float = 0.0
    
    # NEURIPS: Statistical significance (vs self-generated)
    p_value_vs_self_generated: Optional[float] = None  # Two-proportion z-test
    effect_size_vs_self_generated: Optional[float] = None  # Cohen's h
    
    # Skill provenance metrics
    skills_verified: int = 0  # Runtime-evolved: verified working
    skills_speculative: int = 0  # Self-generated: unverified
    skill_verification_rate: float = 0.0  # % of generated skills that work
    curated_skills_loaded: int = 0  # CURATED_SKILLS: how many tasks had curated skill content
    
    # NEURIPS: Stratified results (detect ordering effects)
    stratified_pass_rates: Optional[Dict[str, Any]] = None  # early/middle/late
    
    # Ecosystem metrics (RUNTIME_EVOLVED only)
    ecosystem: Optional[SkillEcosystemMetrics] = None
    
    # Task-level results
    task_results: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            "condition": self.condition,
            "pass_rate": self.pass_rate,
            "pass_at_1": self.pass_at_1,
            "pass_at_3": self.pass_at_3,
            "pass_rate_ci_95": [self.pass_rate_ci_low, self.pass_rate_ci_high],
            "n_samples": self.n_samples,
            "avg_execution_time": self.avg_execution_time,
            "avg_cost": self.avg_cost,
            "avg_retries": self.avg_retries,
            "delta_vs_no_skills": self.delta_vs_no_skills,
            "delta_vs_curated": self.delta_vs_curated,
            "delta_vs_self_generated": self.delta_vs_self_generated,
            "p_value_vs_self_generated": self.p_value_vs_self_generated,
            "effect_size_vs_self_generated": self.effect_size_vs_self_generated,
            "skills_verified": self.skills_verified,
            "skills_speculative": self.skills_speculative,
            "curated_skills_loaded": self.curated_skills_loaded,
            "skill_verification_rate": self.skill_verification_rate,
            "stratified_pass_rates": self.stratified_pass_rates,
            "task_results": self.task_results,
        }
        
        if self.ecosystem:
            result["ecosystem"] = {
                "total_skills": self.ecosystem.total_skills,
                "total_skill_reuses": self.ecosystem.total_skill_reuses,
                "reuse_rate": self.ecosystem.reuse_rate,
                "skill_compositions": self.ecosystem.skill_compositions,
                "avg_skills_per_composition": self.ecosystem.avg_skills_per_composition,
                "speedup_vs_no_skills": self.ecosystem.speedup_vs_no_skills,
                "cost_reduction_vs_no_skills": self.ecosystem.cost_reduction_vs_no_skills,
                "llm_call_reduction_vs_no_skills": self.ecosystem.llm_call_reduction_vs_no_skills,
            }
        
        return result


class SkillMetricsAnalyzer:
    """
    Analyzer for computing skill quality and ecosystem metrics.
    """
    
    def __init__(self):
        self.skill_quality: Dict[str, SkillQualityMetrics] = {}
        
    def analyze_skill_code(self, skill_name: str, code: str) -> SkillQualityMetrics:
        """Analyze static code quality of a skill."""
        metrics = SkillQualityMetrics(skill_name=skill_name)
        
        try:
            tree = ast.parse(code)
            
            # Count functions
            metrics.num_functions = len([
                node for node in ast.walk(tree)
                if isinstance(node, ast.FunctionDef)
            ])
            
            # Count imports
            metrics.num_imports = len([
                node for node in ast.walk(tree)
                if isinstance(node, (ast.Import, ast.ImportFrom))
            ])
            
            # Check for docstrings
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    if ast.get_docstring(node):
                        metrics.has_docstring = True
                        break
            
            # Check for type hints
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if node.returns or any(
                        arg.annotation for arg in node.args.args
                    ):
                        metrics.has_type_hints = True
                        break
            
            # Lines of code
            metrics.lines_of_code = len(code.splitlines())
            
            # Simple cyclomatic complexity estimate
            branches = len([
                node for node in ast.walk(tree)
                if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler))
            ])
            metrics.cyclomatic_complexity = 1 + branches
            
        except SyntaxError:
            logger.warning(f"Syntax error analyzing skill {skill_name}")
            
        return metrics
    
    def compute_ecosystem_metrics(
        self,
        skill_manager,
        task_results: List[Dict[str, Any]],
        baseline_results: Optional[List[Dict[str, Any]]] = None,
    ) -> SkillEcosystemMetrics:
        """
        Compute ecosystem-level metrics.
        
        Args:
            skill_manager: SkillManager instance
            task_results: Results from tasks run with skills
            baseline_results: Results from tasks run without skills (for comparison)
            
        Returns:
            SkillEcosystemMetrics
        """
        metrics = SkillEcosystemMetrics()
        
        if not skill_manager:
            return metrics
        
        # Get all skills
        skills = skill_manager.list_skills()
        metrics.total_skills = len(skills)
        
        # Category breakdown
        for skill in skills:
            # Try to determine category from tags or source_task
            category = "general"
            if skill.get("tags"):
                # Use first tag as category proxy
                category = skill["tags"][0] if isinstance(skill["tags"], list) else skill["tags"]
            metrics.skills_by_category[category] = metrics.skills_by_category.get(category, 0) + 1
        
        # Analyze reuse patterns from task results
        skill_usage = defaultdict(int)
        compositions = []
        
        for result in task_results:
            # Check if task reused skills
            reused_skills = result.get("skills_reused", [])
            if reused_skills:
                metrics.reuse_rate += 1
                for skill in reused_skills:
                    skill_usage[skill] += 1
                    metrics.total_skill_reuses += 1
                
                # Track compositions
                if len(reused_skills) >= 2:
                    compositions.append(reused_skills)
                    metrics.skill_compositions += 1
        
        if task_results:
            metrics.reuse_rate /= len(task_results)
        
        # Reuse statistics
        if skill_usage:
            usage_counts = list(skill_usage.values())
            metrics.skills_never_reused = len(skills) - len(skill_usage)
            metrics.skills_reused_3plus = sum(1 for c in usage_counts if c >= 3)
            metrics.avg_reuses_per_skill = sum(usage_counts) / len(usage_counts)
        
        # Composition metrics
        if compositions:
            metrics.avg_skills_per_composition = sum(
                len(c) for c in compositions
            ) / len(compositions)
            
            # Check composition success
            successful_compositions = sum(
                1 for i, c in enumerate(compositions)
                if task_results[i].get("success", False)
            )
            metrics.composition_success_rate = successful_compositions / len(compositions)
        
        # Diversity (Shannon index)
        if metrics.skills_by_category:
            total = sum(metrics.skills_by_category.values())
            proportions = [c / total for c in metrics.skills_by_category.values()]
            import math
            metrics.ecosystem_diversity = -sum(
                p * math.log(p) for p in proportions if p > 0
            )
        
        # Comparison with baseline
        if baseline_results and task_results:
            baseline_time = sum(r.get("total_time", 0) for r in baseline_results) / len(baseline_results)
            skill_time = sum(r.get("total_time", 0) for r in task_results) / len(task_results)
            
            if baseline_time > 0:
                metrics.speedup_vs_no_skills = ((baseline_time - skill_time) / baseline_time) * 100
            
            baseline_cost = sum(r.get("cost", 0) for r in baseline_results) / len(baseline_results)
            skill_cost = sum(r.get("cost", 0) for r in task_results) / len(task_results)
            
            if baseline_cost > 0:
                metrics.cost_reduction_vs_no_skills = ((baseline_cost - skill_cost) / baseline_cost) * 100
        
        return metrics
    
    def generate_comparison_report(
        self,
        no_skills_metrics: SkillsBenchMetrics,
        curated_metrics: SkillsBenchMetrics,
        self_gen_metrics: SkillsBenchMetrics,
        runtime_evolved_metrics: SkillsBenchMetrics,
    ) -> str:
        """
        Generate a markdown comparison report of all 4 conditions.
        
        This is the key research output: direct empirical comparison showing
        that runtime-evolved skills outperform speculation-based generation.
        """
        report = """# SkillsBench Evaluation: 4-Condition Comparison

## Research Question

Does execution-grounded skill evolution (MCPRuntime) outperform speculation-based
self-generation (SkillsBench baseline) on diverse real-world tasks?

## Conditions Tested

1. **No Skills (Baseline)**: Raw agent capability without skill augmentation
2. **Curated Skills**: Human-written skills provided with tasks
3. **Self-Generated Skills**: Model generates skills BEFORE task (speculation)
4. **Runtime-Evolved Skills**: Skills extracted AFTER successful execution (grounded)

## Key Findings

| Metric | No Skills | Curated | Self-Generated | Runtime-Evolved | Delta (vs Self-Gen) |
|--------|-----------|---------|----------------|-----------------|---------------------|
"""
        
        metrics_list = [
            no_skills_metrics,
            curated_metrics,
            self_gen_metrics,
            runtime_evolved_metrics,
        ]
        
        for metric_name in ["pass_rate", "avg_execution_time", "avg_cost"]:
            values = [getattr(m, metric_name, 0) for m in metrics_list]
            delta = runtime_evolved_metrics.pass_rate - self_gen_metrics.pass_rate
            
            report += f"| {metric_name} |"
            for v in values:
                if metric_name == "pass_rate":
                    report += f" {v*100:.1f}% |"
                elif metric_name == "avg_execution_time":
                    report += f" {v:.2f}s |"
                else:
                    report += f" ${v:.4f} |"
            
            if metric_name == "pass_rate":
                report += f" +{delta*100:.1f}pp |\n"
            else:
                report += f" {delta:.2f} |\n"
        
        report += """
## Ecosystem Metrics (Runtime-Evolved Only)

"""
        
        if runtime_evolved_metrics.ecosystem:
            eco = runtime_evolved_metrics.ecosystem
            report += f"""
- **Total Skills Created**: {eco.total_skills}
- **Total Skill Reuses**: {eco.total_skill_reuses}
- **Reuse Rate**: {eco.reuse_rate*100:.1f}% of tasks reused at least one skill
- **Skill Compositions**: {eco.skill_compositions} tasks used 2+ skills together
- **Avg Skills per Composition**: {eco.avg_skills_per_composition:.1f}
- **Speedup vs No Skills**: {eco.speedup_vs_no_skills:.1f}%
- **Cost Reduction**: {eco.cost_reduction_vs_no_skills:.1f}%

### Category Coverage

"""
            for cat, count in eco.skills_by_category.items():
                report += f"- {cat}: {count} skills\n"
        
        report += """
## Conclusion

Runtime-evolved skills (execution-grounded) demonstrate [significant/moderate/no] 
improvement over speculation-based self-generation, validating that:

1. Skills grounded in actual working code are [more/less] reliable than speculation
2. Execution verification acts as a quality filter for the skill library
3. The MCPRuntime approach addresses the failure mode identified in SkillsBench

## Citation

```bibtex
@article{mcpruntime_skillsbench_2026,
  title={Execution-Grounded Skill Evolution: Addressing the SkillsBench Failure Mode},
  author={[Authors]},
  journal={arXiv preprint},
  year={2026}
}
```
"""
        
        return report
