"""Report generation for benchmark results."""

from typing import Dict, List, Any
import json
from pathlib import Path

from .tasks.schema import BenchmarkMetrics, TaskResult

class ReportGenerator:
    """Generates visual and persistent reports for benchmarks."""
    
    @staticmethod
    def markdown_report(metrics: BenchmarkMetrics, backend: str, results: List[TaskResult]) -> str:
        """Generate an agent-focused markdown report for a single backend."""
        lines = []
        lines.append(f"# MRBS Agent Benchmark Report: {backend.upper()}")
        lines.append("")
        lines.append("*Evaluating how well this runtime supports LLM-generated agent code*")
        lines.append("")
        
        # Agent-Focused Summary
        lines.append("## Agent Performance Summary")
        lines.append(f"- **Task Success Rate**: {metrics.pass_rate*100:.1f}% ({metrics.passed_tasks}/{metrics.attempted_tasks} attempted, {metrics.skipped_tasks} skipped)")
        lines.append(f"- **Avg Time-to-Success**: {metrics.avg_time_to_success:.2f}s (includes LLM generation)")
        lines.append(f"- **Avg Iterations Needed**: {metrics.avg_iterations:.1f}")
        if metrics.avg_llm_generation_time > 0:
            lines.append(f"- **Avg LLM Generation Time**: {metrics.avg_llm_generation_time:.2f}s")
        lines.append(f"- **Execution Time (substrate)**: {metrics.avg_execution_time:.2f}s")
        lines.append(f"- **P95 Execution Time**: {metrics.p95_execution_time:.2f}s")
        if metrics.error_count > 0 or metrics.timeout_count > 0:
            lines.append(f"- **Errors/Timeouts**: {metrics.error_count} / {metrics.timeout_count}")
        lines.append("")
        
        # Category Breakdown (Agent-focused)
        lines.append("## Category Breakdown (Agent Success Rates)")
        lines.append("| Category | Tasks | Success | Skipped | Success Rate | Avg TTS |")
        lines.append("|----------|-------|---------|---------|--------------|---------|")
        for cat, data in metrics.category_breakdown.items():
            rate = data['pass_rate'] * 100
            lines.append(f"| {cat} | {data['total']} | {data['passed']} | {data['skipped']} | {rate:.1f}% | {data['avg_time']:.2f}s |")
        lines.append("")
        lines.append("*Success Rate = % of tasks where agent-generated code passed validation*")
        lines.append("")
        
        # Difficulty Breakdown
        lines.append("## Difficulty Breakdown")
        lines.append("| Difficulty | Total | Passed | Skipped | Pass Rate | Avg Time |")
        lines.append("|------------|-------|--------|---------|-----------|----------|")
        for diff, data in metrics.difficulty_breakdown.items():
            rate = data['pass_rate'] * 100
            lines.append(f"| {diff} | {data['total']} | {data['passed']} | {data['skipped']} | {rate:.1f}% | {data['avg_time']:.2f}s |")
        lines.append("")
        
        # Failed/Skipped Details (Agent-focused)
        failures = [r for r in results if not r.success and not r.skipped]
        if failures:
            lines.append("## Agent Task Failures")
            lines.append("")
            lines.append("Tasks where the LLM-generated code failed validation or execution:")
            lines.append("")
            for f in failures[:10]: # limit to 10
                reason = f.error if f.error else f.validation.get("error", "Unknown")
                error_type = "Execution" if "runtime" in str(reason).lower() else "Validation"
                lines.append(f"- **{f.task_id}** ({f.category}): [{error_type}] {str(reason)[:60]}...")
            if len(failures) > 10:
                lines.append(f"- *...and {len(failures) - 10} more.*")
            lines.append("")
                
        return "\n".join(lines)
        
    @staticmethod
    def save_report(report_str: str, path: str):
        """Save a report to a file."""
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(report_str, encoding="utf-8")

    @staticmethod
    def comparison_matrix(control_metrics: BenchmarkMetrics, control_name: str, test_metrics: BenchmarkMetrics, test_name: str, format: str = "markdown") -> str:
        """Generate a comparison matrix between two backends."""
        lines = []
        
        # Calculate deltas
        speedup = control_metrics.avg_execution_time / test_metrics.avg_execution_time if test_metrics.avg_execution_time > 0 else 0
        pass_diff = test_metrics.pass_rate - control_metrics.pass_rate
        
        if format == "latex":
            lines.append(f"% Benchmark Comparison: {control_name.upper()} vs {test_name.upper()}")
            lines.append(r"\begin{table}[h]")
            lines.append(r"\centering")
            lines.append(r"\begin{tabular}{l c c c}")
            lines.append(r"\toprule")
            lines.append(f"\\textbf{{Metric}} & \\textbf{{{control_name.title()}}} & \\textbf{{{test_name.title()}}} & \\textbf{{Delta}} \\\\")
            lines.append(r"\midrule")
            lines.append(f"Pass Rate & {control_metrics.pass_rate*100:.1f}\\% & {test_metrics.pass_rate*100:.1f}\\% & {pass_diff*100:+.1f} ppt \\\\")
            lines.append(f"Avg Time & {control_metrics.avg_execution_time:.3f}s & {test_metrics.avg_execution_time:.3f}s & {speedup:.2f}x speedup \\\\")
            lines.append(f"P95 Time & {control_metrics.p95_execution_time:.3f}s & {test_metrics.p95_execution_time:.3f}s & - \\\\")
            lines.append(r"\bottomrule")
            lines.append(r"\end{tabular}")
            lines.append(f"\\caption{{Performance comparison between {control_name} and {test_name}.}}")
            lines.append(r"\end{table}")
            
        elif format == "csv":
            lines.append("Metric,Control,Test,Delta")
            lines.append(f"Pass Rate,{control_metrics.pass_rate*100:.1f}%,{test_metrics.pass_rate*100:.1f}%,{pass_diff*100:+.1f} ppt")
            lines.append(f"Avg Time (s),{control_metrics.avg_execution_time:.3f},{test_metrics.avg_execution_time:.3f},{speedup:.2f}x speedup")
            lines.append(f"P95 Time (s),{control_metrics.p95_execution_time:.3f},{test_metrics.p95_execution_time:.3f},-")
            
            lines.append("")
            lines.append("Category,Control Pass,Test Pass,Control Time,Test Time")
            for cat in control_metrics.category_breakdown.keys():
                c_data = control_metrics.category_breakdown.get(cat, {'pass_rate': 0, 'avg_time': 0})
                t_data = test_metrics.category_breakdown.get(cat, {'pass_rate': 0, 'avg_time': 0})
                lines.append(f"{cat},{c_data['pass_rate']*100:.1f}%,{t_data['pass_rate']*100:.1f}%,{c_data['avg_time']:.3f},{t_data['avg_time']:.3f}")
                
        else:
            # Markdown
            lines.append(f"# Comparison Matrix: `{control_name}` vs `{test_name}`")
            lines.append("")
            lines.append(f"**Speedup:** `{speedup:.2f}x` | **Pass Rate Delta:** `{pass_diff*100:+.1f} ppt`")
            lines.append("")
            lines.append("| Metric | Control | Test | Delta |")
            lines.append("|---|---|---|---|")
            lines.append(f"| Pass Rate | {control_metrics.pass_rate*100:.1f}% | {test_metrics.pass_rate*100:.1f}% | {pass_diff*100:+.1f} ppt |")
            lines.append(f"| Avg Time  | {control_metrics.avg_execution_time:.3f}s | {test_metrics.avg_execution_time:.3f}s | {speedup:.2f}x speedup |")
            lines.append(f"| P95 Time  | {control_metrics.p95_execution_time:.3f}s | {test_metrics.p95_execution_time:.3f}s | - |")
            lines.append("")
            lines.append("### Category Breakdown Comparison")
            lines.append("| Category | Control Pass | Test Pass | Control Time | Test Time |")
            lines.append("|---|---|---|---|---|")
            for cat in control_metrics.category_breakdown.keys():
                c_data = control_metrics.category_breakdown.get(cat, {'pass_rate': 0, 'avg_time': 0})
                t_data = test_metrics.category_breakdown.get(cat, {'pass_rate': 0, 'avg_time': 0})
                lines.append(f"| {cat.title()} | {c_data['pass_rate']*100:.1f}% | {t_data['pass_rate']*100:.1f}% | {c_data['avg_time']:.3f}s | {t_data['avg_time']:.3f}s |")
                
        return "\n".join(lines)
