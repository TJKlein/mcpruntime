"""Custom validators for import_heavy tasks."""

import re
from typing import Any, Dict, Tuple
from ..schema import Task

def check_merge(task: Task, output: str) -> Tuple[bool, float, Dict[str, Any]]:
    """Validate that the pandas merge output is correct."""
    if not output:
        return False, 0.0, {"error": "Empty output"}
        
    try:
        # Expected from our synthetic data:
        # Merged rows: 1000
        # Missing prices: 0
        # Total Value: <some float>
        
        rows_match = re.search(r'Merged rows:\s*(\d+)', output)
        missing_match = re.search(r'Missing prices:\s*(\d+)', output)
        value_match = re.search(r'Total Value:\s*([0-9.]+)', output)
        
        if not rows_match or not missing_match or not value_match:
            return False, 0.0, {"error": "Could not parse expected metrics from output"}
            
        rows = int(rows_match.group(1))
        missing = int(missing_match.group(1))
        value = float(value_match.group(1))
        
        if rows == 1000 and missing == 0 and value > 0:
            return True, 1.0, {"status": "merge_successful"}
        else:
            return False, 0.0, {
                "error": "Merge data mismatch",
                "rows": rows,
                "missing": missing,
                "value": value
            }
            
    except Exception as e:
        return False, 0.0, {"error": f"Parse error: {str(e)}"}
