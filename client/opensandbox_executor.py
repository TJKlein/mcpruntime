"""OpenSandbox executor implementation.

This executor uses alibaba/OpenSandbox as the execution backend.
OpenSandbox runs locally via Docker (no cloud API key required).

Prerequisites:
    pip install opensandbox opensandbox-server
    opensandbox-server init-config ~/.sandbox.toml --example docker
    opensandbox-server start

RLM (Recursive Language Model) support: when execution context provides
inputs (e.g. CONTEXT_DATA) and functions (e.g. ask_llm), the executor
injects them so that sandboxed code can use them. ask_llm is exposed
via a small HTTP server on the host that the container calls.
"""

import asyncio
import json
import logging
import os
import socketserver
import threading
from datetime import timedelta
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

try:
    from opensandbox.sandbox import Sandbox
    from opensandbox.config import ConnectionConfig
    from opensandbox.models import WriteEntry
except ImportError:
    Sandbox = None  # type: ignore
    ConnectionConfig = None  # type: ignore
    WriteEntry = None  # type: ignore

from client.base_executor import BaseExecutor
from client.base import ExecutionResult
from config.schema import ExecutionConfig, GuardrailConfig, OptimizationConfig

logger = logging.getLogger(__name__)


def _build_rlm_preamble(context: Optional[Dict[str, Any]], rlm_port: Optional[int]) -> str:
    """Build code preamble to inject CONTEXT_DATA and ask_llm for RLM (OpenSandbox)."""
    if not context:
        return ""
    lines = []
    # Inject inputs (e.g. CONTEXT_DATA)
    inputs = context.get("inputs") or {}
    for name, value in inputs.items():
        if isinstance(value, str):
            # Safe injection: use repr so quotes and newlines are escaped
            lines.append(f"{name} = {repr(value)}")
    # Inject ask_llm as HTTP client when RLM server port is provided
    if rlm_port is not None and (context.get("functions") or {}).get("ask_llm") is not None:
        lines.append("")
        lines.append("def ask_llm(prompt, data):")
        lines.append("    import urllib.request")
        lines.append("    import json")
        # host.docker.internal works from Docker containers to reach the host
        lines.append(f"    url = 'http://host.docker.internal:{rlm_port}/ask_llm'")
        lines.append("    body = json.dumps({'prompt': prompt, 'data': data}).encode('utf-8')")
        lines.append("    req = urllib.request.Request(url, data=body, headers={'Content-Type': 'application/json'}, method='POST')")
        lines.append("    with urllib.request.urlopen(req, timeout=60) as r:")
        lines.append("        out = json.loads(r.read().decode('utf-8'))")
        lines.append("    return out.get('result', '')")
    if not lines:
        return ""
    return "\n".join(lines)


def _start_rlm_server(ask_llm_callback: Callable[[str, str], str]) -> tuple[socketserver.TCPServer, int]:
    """Start a small HTTP server that exposes ask_llm to the sandbox. Returns (server, port)."""
    class RLMHandler(BaseHTTPRequestHandler):
        def do_POST(self):
            if self.path != "/ask_llm":
                self.send_response(404)
                self.end_headers()
                return
            callback = getattr(self.server, "rlm_ask_llm", None)
            if not callback:
                self.send_response(500)
                self.end_headers()
                return
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length)
                payload = json.loads(body.decode("utf-8"))
                prompt = payload.get("prompt", "")
                data = payload.get("data", "")
                result = callback(prompt, data)
                response = json.dumps({"result": result}).encode("utf-8")
            except Exception as e:
                logger.warning(f"RLM server ask_llm error: {e}")
                response = json.dumps({"result": f"Error: {e}"}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(response)))
            self.end_headers()
            self.wfile.write(response)

        def log_message(self, format, *args):
            logger.debug(f"RLM server: {format % args}")

    server = socketserver.TCPServer(("", 0), RLMHandler)
    server.rlm_ask_llm = ask_llm_callback
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, port


def _is_connection_error(exc: Exception) -> bool:
    """Return True if the exception looks like a connection/server-not-running error."""
    import errno
    error_str = str(exc).lower()
    connection_keywords = (
        "connection refused",
        "connection error",
        "connect call failed",
        "cannot connect",
        "network is unreachable",
        "name or service not known",
        "nodename nor servname provided",
        "failed to establish",
        "remote end closed connection",
        "server not reachable",
    )
    if any(kw in error_str for kw in connection_keywords):
        return True
    # httpx / aiohttp errno-based checks
    cause = getattr(exc, "__cause__", None) or getattr(exc, "__context__", None)
    if cause is not None:
        cause_str = str(cause).lower()
        if any(kw in cause_str for kw in connection_keywords):
            return True
    return False

class OpenSandboxExecutor(BaseExecutor):
    """Execution backend using Alibaba OpenSandbox (local Docker-based).

    Compatible drop-in replacement for MicrosandboxExecutor.
    Files are pushed into the sandbox container via the OpenSandbox file API,
    replicating the volume-mount behaviour of microsandbox.
    """

    def __init__(
        self,
        execution_config: ExecutionConfig,
        guardrail_config: Optional[GuardrailConfig] = None,
        optimization_config: Optional[OptimizationConfig] = None,
    ):
        """Initialize OpenSandbox executor."""
        super().__init__(execution_config, guardrail_config, optimization_config)

    def execute(self, code: str, context: Optional[Dict[str, Any]] = None) -> tuple[ExecutionResult, Any, Optional[str]]:
        """Execute code inside an OpenSandbox container.

        If context is provided with inputs (e.g. CONTEXT_DATA) and/or functions (e.g. ask_llm),
        they are injected so RLM (Recursive Language Model) tasks work: CONTEXT_DATA is
        inlined, and ask_llm is exposed via a small HTTP server on the host that the
        container calls at http://host.docker.internal:PORT/ask_llm.
        """
        if Sandbox is None:
            raise ImportError(
                "opensandbox is not installed. Install it with: pip install opensandbox"
            )

        # Build RLM preamble and optionally start ask_llm HTTP server
        rlm_server = None
        rlm_port = None
        if context and (context.get("inputs") or context.get("functions")):
            functions = context.get("functions") or {}
            if functions.get("ask_llm"):
                ask_llm_cb = functions["ask_llm"]
                rlm_server, rlm_port = _start_rlm_server(ask_llm_cb)
                logger.debug(f"RLM server started on port {rlm_port}")
            preamble = _build_rlm_preamble(context, rlm_port)
            if preamble:
                code = preamble + "\n\n" + code

        # Pre-execution guardrail validation
        validation_result = self.validate_code(code)
        if not validation_result.valid:
            error_msg = "; ".join(validation_result.errors)
            logger.error(f"Code validation failed: {error_msg}")
            if rlm_server:
                rlm_server.shutdown()
            return ExecutionResult.FAILURE, None, error_msg

        try:
            try:
                result = asyncio.run(self._execute_async(code))
                output, error = result

                if error:
                    logger.error(f"Code execution error: {error}")
                    return ExecutionResult.FAILURE, None, error

                # Post-execution guardrail validation
                if output is not None:
                    output_result = self.guardrail_validator.validate_output(output, {})
                    if not output_result.valid and self.guardrail_config.strict_mode:
                        error_msg = "; ".join(output_result.errors)
                        logger.error(f"Output validation failed: {error_msg}")
                        return ExecutionResult.BLOCKED, None, error_msg

                return ExecutionResult.SUCCESS, output, None

            except asyncio.TimeoutError:
                logger.error("Code execution timed out")
                return ExecutionResult.TIMEOUT, None, "Execution timeout"
            except Exception as e:
                error_msg = str(e)
                # Detect connection failures and give an actionable message
                if _is_connection_error(e):
                    domain = (
                        self.execution_config.opensandbox_domain
                        or "localhost:8080"
                    )
                    friendly = (
                        f"❌ OpenSandbox server not reachable at {domain}.\n"
                        f"   Start it with:  opensandbox-server start\n"
                        f"   Install with:   pip install opensandbox-server\n"
                        f"   Then configure: opensandbox-server init-config ~/.sandbox.toml --example docker\n"
                        f"   (Docker must be running)\n"
                    )
                    logger.error(friendly)
                    return ExecutionResult.FAILURE, None, friendly
                logger.error(f"Code execution failed: {e}")
                return ExecutionResult.FAILURE, None, error_msg
        finally:
            if rlm_server is not None:
                rlm_server.shutdown()


    async def _execute_async(self, code: str) -> tuple[Any, Optional[str]]:
        """Execute code asynchronously inside an OpenSandbox container.

        Mirrors the MicrosandboxExecutor pattern:
        1. Write workspace files (client/, servers/, skills/) into the container
           via sandbox.files.write_files(), replicating volume-mount behaviour.
        2. Write the task code to /workspace/_execute_task.py.
        3. Run it via sandbox.commands.run("python3 /workspace/_execute_task.py").
        4. Collect stdout + stderr, kill sandbox.
        """
        try:
            # Resolve paths (same as MicrosandboxExecutor)
            project_root = self._find_project_root()
            workspace_path = (project_root / self.execution_config.workspace_dir.lstrip("./")).resolve()
            servers_path = (project_root / self.execution_config.servers_dir.lstrip("./")).resolve()
            skills_path = (project_root / self.execution_config.skills_dir.lstrip("./")).resolve()
            client_path = (project_root / "client").resolve()

            workspace_path.mkdir(parents=True, exist_ok=True)

            # Build OpenSandbox connection config (local server, no auth needed)
            domain = (
                self.execution_config.opensandbox_domain
                or os.environ.get("OPENSANDBOX_DOMAIN", "localhost:8080")
            )
            image = self.execution_config.opensandbox_image

            conn_config = ConnectionConfig(
                domain=domain,
                protocol="http",
            )

            logger.debug(f"Connecting to OpenSandbox at {domain}, image={image}")

            # Collect all files to push into the container
            file_entries = self._build_file_entries(
                workspace_path=workspace_path,
                servers_path=servers_path,
                client_path=client_path,
                skills_path=skills_path,
                code=code,
            )

            sandbox = await Sandbox.create(
                image,
                connection_config=conn_config,
                timeout=timedelta(seconds=120),
            )
            async with sandbox:
                # Push all workspace files into the container
                if file_entries:
                    await sandbox.files.write_files(file_entries)
                    logger.debug(f"Pushed {len(file_entries)} files into OpenSandbox container")

                # Verify /workspace exists and is accessible
                setup_cmd = (
                    "python3 -c \""
                    "import sys; sys.path.insert(0, '/workspace'); "
                    "import os; print('/workspace exists:', os.path.exists('/workspace')); "
                    "contents = os.listdir('/workspace') if os.path.exists('/workspace') else []; "
                    "print('/workspace contents:', contents)"
                    "\""
                )
                setup_exec = await asyncio.wait_for(
                    sandbox.commands.run(setup_cmd), timeout=30.0
                )
                setup_stdout = self._extract_stdout(setup_exec)
                if setup_stdout:
                    logger.debug(f"Setup output: {setup_stdout}")

                # Execute the task script
                script_path = "/workspace/_execute_task.py"
                exec_cmd = f"python3 {script_path}"

                exec_result = await asyncio.wait_for(
                    sandbox.commands.run(exec_cmd), timeout=60.0
                )

                output = self._extract_stdout(exec_result)
                stderr = self._extract_stderr(exec_result)

                logger.debug(f"Execution completed. Output length: {len(output) if output else 0} chars")
                if output:
                    logger.debug(f"Output first 1000 chars:\n{output[:1000]}")

                # Log stderr for debugging but don't append to output (breaks validation)
                if stderr:
                    logger.debug(f"Stderr: {stderr[:500]}")

                error = None
                # Detect fatal errors in stderr
                if stderr and "Traceback (most recent call last)" in stderr:
                    error = stderr

                await sandbox.kill()
                return output, error

        except asyncio.TimeoutError:
            logger.error("OpenSandbox execution timed out")
            return None, "Execution timed out"
        except Exception as e:
            logger.error(f"OpenSandbox execution error: {e}", exc_info=True)
            return None, str(e)

    def _build_file_entries(
        self,
        workspace_path: Path,
        servers_path: Path,
        client_path: Path,
        skills_path: Path,
        code: str,
    ) -> List[Any]:
        """Build a list of WriteEntry objects for all workspace files.

        Replicates the volume-mount behaviour of MicrosandboxExecutor:
        every file that would be present at /workspace is pushed into
        the OpenSandbox container via the file API.
        """
        entries = []

        def _add_entry(container_path: str, content: str) -> None:
            entries.append(WriteEntry(path=container_path, data=content, mode=644))

        # client/__init__.py
        _add_entry("/workspace/client/__init__.py", '"""Client module for sandbox execution."""\n')

        # client/mcp_client.py  (prefer mock for examples, real for production)
        mock_client_file = client_path / "mock_mcp_client.py"
        real_client_file = client_path / "mcp_client.py"

        if mock_client_file.exists():
            _add_entry("/workspace/client/mcp_client.py", mock_client_file.read_text(encoding="utf-8"))
        elif real_client_file.exists():
            _add_entry("/workspace/client/mcp_client.py", real_client_file.read_text(encoding="utf-8"))

        # servers/
        if servers_path.exists():
            for server_dir in sorted(servers_path.iterdir()):
                if server_dir.is_dir():
                    server_name = server_dir.name
                    # Tool files first (before __init__.py which imports them)
                    for tool_file in sorted(server_dir.glob("*.py")):
                        if tool_file.name != "__init__.py":
                            _add_entry(
                                f"/workspace/servers/{server_name}/{tool_file.name}",
                                tool_file.read_text(encoding="utf-8"),
                            )
                    # __init__.py last
                    init_file = server_dir / "__init__.py"
                    if init_file.exists():
                        _add_entry(
                            f"/workspace/servers/{server_name}/__init__.py",
                            init_file.read_text(encoding="utf-8"),
                        )

        # skills/
        for skill_file in skills_path.glob("*.py") if skills_path.exists() else []:
            _add_entry(
                f"/workspace/skills/{skill_file.name}",
                skill_file.read_text(encoding="utf-8"),
            )

        # Setup files from workspace (e.g., mock_mcp_client.py for PTC tasks)
        # These are files created by the runner's setup_workspace method
        for setup_file in workspace_path.glob("*.py"):
            if setup_file.name not in ["_execute_task.py"]:
                _add_entry(
                    f"/workspace/{setup_file.name}",
                    setup_file.read_text(encoding="utf-8"),
                )

        # data/ directory and other fixture directories
        for data_dir in workspace_path.glob("data"):
            if data_dir.is_dir():
                for data_file in data_dir.rglob("*"):
                    if data_file.is_file():
                        relative_path = data_file.relative_to(workspace_path)
                        _add_entry(
                            f"/workspace/{relative_path}",
                            data_file.read_text(encoding="utf-8"),
                        )

        # The task script itself — mirrors microsandbox's _execute_task.py pattern
        task_script = self._build_task_script(code)
        _add_entry("/workspace/_execute_task.py", task_script)

        return entries

    def _build_task_script(self, code: str) -> str:
        """Build the wrapper script that sets up sys.path then runs the task code.

        Mirrors the setup code used by MicrosandboxExecutor to ensure imports,
        path configuration, and (optionally) mcp_client are all available.
        Setup debug output goes to stderr to avoid polluting task stdout.
        """
        setup = "\n".join([
            "import os",
            "import sys",
            "",
            "# Add /workspace to Python path for imports",
            "if '/workspace' not in sys.path:",
            "    sys.path.insert(0, '/workspace')",
            "",
            "# Verify /workspace is mounted (debug to stderr)",
            "if os.path.exists('/workspace'):",
            "    print('✅ /workspace is available', flush=True, file=sys.stderr)",
            "    mcp_client_exists = os.path.exists('/workspace/client/mcp_client.py')",
            "    if mcp_client_exists:",
            "        try:",
            "            from client.mcp_client import call_mcp_tool",
            "            print('✅ client.mcp_client imported', flush=True, file=sys.stderr)",
            "        except Exception as e:",
            "            print(f'⚠️ mcp_client import failed: {e}', flush=True, file=sys.stderr)",
            "else:",
            "    print('❌ /workspace not available', flush=True, file=sys.stderr)",
            "",
            "# === Execute task code ===",
        ])
        return setup + "\n\n" + code

    @staticmethod
    def _extract_stdout(execution: Any) -> str:
        """Extract stdout text from an OpenSandbox execution result."""
        try:
            lines = execution.logs.stdout
            if lines:
                # Join with newlines and add trailing newline to match expected format
                result = "\n".join(line.text for line in lines)
                # Ensure trailing newline if the original output had one
                if result and not result.endswith("\n"):
                    result += "\n"
                return result
        except Exception as e:
            logger.debug(f"Could not extract stdout: {e}")
        return ""

    @staticmethod
    def _extract_stderr(execution: Any) -> str:
        """Extract stderr text from an OpenSandbox execution result."""
        try:
            lines = execution.logs.stderr
            if lines:
                return "\n".join(line.text for line in lines)
        except Exception as e:
            logger.debug(f"Could not extract stderr: {e}")
        return ""
