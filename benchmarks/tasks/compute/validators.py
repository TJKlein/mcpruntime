"""Custom validators for compute tasks."""

import re
from typing import Any, Dict, Tuple
from ..schema import Task

def check_sorted(task: Task, output: str) -> Tuple[bool, float, Dict[str, Any]]:
    """Validate that the merge sort output actually shows a sorted list."""
    if not output:
        return False, 0.0, {"error": "Empty output"}
        
    try:
        # Looking for things like "Sorted first 5: [1, 2, 3, 4, 5]"
        first_match = re.search(r'Sorted first 5:\s*(\[.*?\])', output)
        last_match = re.search(r'Sorted last 5:\s*(\[.*?\])', output)
        
        if not first_match or not last_match:
            return False, 0.0, {"error": "Could not find expected output arrays"}
            
        import ast
        first_5 = ast.literal_eval(first_match.group(1))
        last_5 = ast.literal_eval(last_match.group(1))
        
        # Verify it's sorted 1 to 10000
        if first_5 == [1, 2, 3, 4, 5] and last_5 == [9996, 9997, 9998, 9999, 10000]:
            return True, 1.0, {"status": "correctly_sorted"}
        else:
            return False, 0.0, {
                "error": "Array not sorted correctly",
                "first_5": first_5,
                "last_5": last_5
            }
            
    except Exception as e:
        return False, 0.0, {"error": f"Parse error: {str(e)}"}
