"""External baselines for MRBS comparison."""

import subprocess
import time
import uuid
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from client.base import ExecutionResult

class BaselineExecutor:
    """Base class for baseline executors."""
    
    def __init__(self, execution_config=None, guardrail_config=None, optimization_config=None, timeout: int = 30):
        self.timeout = timeout
        self.workspace = execution_config.workspace_dir if execution_config else "."
        
    def execute(self, code: str) -> Tuple[ExecutionResult, Optional[str], Optional[str]]:
        raise NotImplementedError

class SubprocessBaseline(BaselineExecutor):
    """Executes code via raw subprocess python3."""

    def execute(self, code: str, context: Optional[Dict[str, Any]] = None) -> Tuple[ExecutionResult, Optional[str], Optional[str]]:
        if context and (context.get("inputs") or {}).get("CONTEXT_DATA") is not None:
            preamble = "CONTEXT_DATA = {}\n\n".format(repr(context["inputs"]["CONTEXT_DATA"]))
            code = preamble + code
        script_path = Path(self.workspace) / f"script_{uuid.uuid4().hex[:8]}.py"
        script_path.write_text(code)
            
        try:
            result = subprocess.run(
                ["python3", script_path.name],
                cwd=self.workspace,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            output = result.stdout
            if result.stderr:
                output = output + "\n[STDERR]\n" + result.stderr if output else "[STDERR]\n" + result.stderr
                
            if result.returncode == 0:
                return ExecutionResult.SUCCESS, output, None
            else:
                return ExecutionResult.FAILURE, output, result.stderr
        except subprocess.TimeoutExpired:
            return ExecutionResult.TIMEOUT, None, f"Timeout after {self.timeout}s"
        except Exception as e:
            return ExecutionResult.FAILURE, None, str(e)
        finally:
            script_path.unlink(missing_ok=True)

class DockerBaseline(BaselineExecutor):
    """Executes code via bare docker run python:3.11."""
    
    def execute(self, code: str) -> Tuple[ExecutionResult, Optional[str], Optional[str]]:
        script_path = Path(self.workspace) / f"script_{uuid.uuid4().hex[:8]}.py"
        script_path.write_text(code)
            
        try:
            # Mount the entire workspace so fixtures are available
            workspace_abs = Path(self.workspace).absolute()
            result = subprocess.run(
                ["docker", "run", "--rm", "-v", f"{workspace_abs}:/app", "-w", "/app", "python:3.11-slim", "python3", script_path.name],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            output = result.stdout
            if result.stderr:
                output = output + "\n[STDERR]\n" + result.stderr if output else "[STDERR]\n" + result.stderr
                
            if result.returncode == 0:
                return ExecutionResult.SUCCESS, output, None
            else:
                return ExecutionResult.FAILURE, output, result.stderr
        except subprocess.TimeoutExpired:
            return ExecutionResult.TIMEOUT, None, f"Timeout after {self.timeout}s"
        except Exception as e:
            return ExecutionResult.FAILURE, None, str(e)
        finally:
            script_path.unlink(missing_ok=True)
