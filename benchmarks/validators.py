"""Validation framework for benchmark results."""

import importlib
import logging
import math
import re
from typing import Any, Callable, Dict, Optional, Tuple

from .tasks.schema import Task

logger = logging.getLogger(__name__)


class Validator:
    """Core validator that dispatches to specific validation strategies."""
    
    @classmethod
    def validate(cls, task: Task, output: str) -> Tuple[bool, float, Dict[str, Any]]:
        """Validate an output against a task's expectations.
        
        Args:
            task: The task definition
            output: The stdout from the execution
            
        Returns:
            Tuple of (passed, score, details)
        """
        output = output or ""
        
        try:
            if task.validation_type == "exact":
                return cls._exact_match(task.expected_output, output)
            elif task.validation_type == "fuzzy":
                return cls._fuzzy_match(task.expected_output, output)
            elif task.validation_type == "custom":
                if not task.custom_validator:
                    return False, 0.0, {"error": "Custom validation requested but no validator specified"}
                return cls._call_custom(task, output)
            else:
                return False, 0.0, {"error": f"Unknown validation type: {task.validation_type}"}
                
        except Exception as e:
            logger.error(f"Validation error for task {task.id}: {e}")
            return False, 0.0, {"error": str(e)}

    @staticmethod
    def _exact_match(expected: Optional[str], output: str) -> Tuple[bool, float, Dict[str, Any]]:
        if expected is None:
            return True, 1.0, {"note": "No expected output specified"}
            
        is_match = expected.strip() == output.strip()
        score = 1.0 if is_match else 0.0
        details = {
            "expected": expected.strip(),
            "actual": output.strip()
        }
        return is_match, score, details

    @staticmethod
    def _fuzzy_match(expected: Optional[str], output: str) -> Tuple[bool, float, Dict[str, Any]]:
        if expected is None:
            return True, 1.0, {"note": "No expected output specified"}
            
        def normalize(s: str) -> str:
            # Lowercase and normalize whitespace
            s = re.sub(r'\s+', ' ', s.lower().strip())
            return s
            
        norm_expected = normalize(expected)
        norm_output = normalize(output)
        
        # Fast path exact match after normalization
        if norm_expected == norm_output:
            return True, 1.0, {"strategy": "normalized_exact"}
            
        # Try to find floats and compare with tolerance
        def extract_floats(s: str) -> list[float]:
            floats = []
            for match in re.finditer(r'-?\d+\.\d+', s):
                try:
                    floats.append(float(match.group()))
                except ValueError:
                    pass
            return floats
            
        exp_floats = extract_floats(norm_expected)
        out_floats = extract_floats(norm_output)
        
        if exp_floats and out_floats and len(exp_floats) == len(out_floats):
            # If the only difference is float precision, consider it a match
            all_match = all(math.isclose(e, o, rel_tol=1e-5) for e, o in zip(exp_floats, out_floats))
            if all_match:
                # Remove floats from the strings and check if the rest matches
                for e, o in zip(exp_floats, out_floats):
                    norm_expected = norm_expected.replace(str(e), "FLOAT_VAL")
                    norm_output = norm_output.replace(str(o), "FLOAT_VAL")
                if norm_expected == norm_output:
                    return True, 1.0, {"strategy": "float_tolerance"}
                    
        return False, 0.0, {
            "expected_normalized": norm_expected,
            "actual_normalized": norm_output
        }

    @staticmethod
    def _call_custom(task: Task, output: str) -> Tuple[bool, float, Dict[str, Any]]:
        """Dynamically dispatch to a custom validator for the task's category."""
        module_path = f"benchmarks.tasks.{task.category}.validators"
        try:
            module = importlib.import_module(module_path)
            validator_func = getattr(module, task.custom_validator)
            return validator_func(task, output)
        except ImportError:
            return False, 0.0, {"error": f"Could not import {module_path}"}
        except AttributeError:
            return False, 0.0, {"error": f"Validator '{task.custom_validator}' not found in {module_path}"}
