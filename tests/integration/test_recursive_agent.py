"""Integration tests for RecursiveAgent using OpenSandbox.

RLM is supported with OpenSandbox: the executor injects CONTEXT_DATA and
exposes ask_llm via a small HTTP server on the host that the container calls.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Skip entire module if opensandbox not installed or server not running
import httpx
try:
    from opensandbox.sandbox import Sandbox as _Sandbox
    # Check if server is actually reachable
    _client = httpx.AsyncClient(timeout=2.0)
    _SERVER_AVAILABLE = False
    try:
        import asyncio
        resp = asyncio.get_event_loop().run_until_complete(
            _client.get("http://localhost:8080/api/v1/health")
        )
        _SERVER_AVAILABLE = resp.status_code == 200
    except Exception:
        _SERVER_AVAILABLE = False
except ImportError:
    _Sandbox = None
    _SERVER_AVAILABLE = False

from client.code_generator import HAS_LITELLM
from client.recursive_agent import RecursiveAgent
from client.opensandbox_executor import OpenSandboxExecutor
from client.filesystem_helpers import FilesystemHelper
from client.base import ExecutionResult


@pytest.mark.skipif(_Sandbox is None or not _SERVER_AVAILABLE, reason="opensandbox not installed or server not running")
class TestRecursiveAgentIntegration:

    @pytest.fixture
    def agent(self, mock_config, temp_workspace, temp_servers, mock_llm_client):
        """Create a RecursiveAgent instance with OpenSandbox executor."""
        fs_helper = FilesystemHelper(
            workspace_dir=str(temp_workspace),
            servers_dir=str(temp_servers),
            skills_dir="./skills",
        )

        executor = OpenSandboxExecutor(
            execution_config=mock_config.execution,
            guardrail_config=mock_config.guardrails,
            optimization_config=mock_config.optimizations,
        )

        agent = RecursiveAgent(
            fs_helper=fs_helper,
            executor=executor,
            optimization_config=mock_config.optimizations,
            llm_config=mock_config.llm,
        )

        agent.code_generator._llm_client = mock_llm_client
        agent.code_generator._model_name = "gpt-4"

        return agent

    @pytest.mark.skipif(not HAS_LITELLM, reason="litellm not installed")
    @patch("litellm.completion")
    def test_infinite_context_search(self, mock_litellm_completion, agent, tmp_path, mock_llm_client):
        """Test RLM infinite context search: CONTEXT_DATA and ask_llm are injected by OpenSandbox."""
        context_file = tmp_path / "large_log.txt"
        context_file.write_text("Log entry 1\nLog entry 2\nERROR: SYSTEM_FAILURE\nLog entry 4")

        def litellm_side_effect(*args, **kwargs):
            messages = kwargs.get("messages", [])
            user_content = messages[-1]["content"] if messages else ""
            if "SYSTEM_FAILURE" in user_content:
                return MagicMock(choices=[MagicMock(message=MagicMock(content="Yes, found SYSTEM_FAILURE"))])
            return MagicMock(choices=[MagicMock(message=MagicMock(content="No error found"))])

        mock_litellm_completion.side_effect = litellm_side_effect

        code = """
chunk_size = 50
for i in range(0, len(CONTEXT_DATA), chunk_size):
    chunk = CONTEXT_DATA[i:i+chunk_size]
    result = ask_llm('Find error', chunk)
    print(f"Result: {result}")
"""
        agent.code_generator.generate_complete_code = MagicMock(return_value=(code, False))

        result, output, error = agent.execute_recursive_task(
            task_description="Find the error in CONTEXT_DATA",
            context_data=context_file,
            verbose=False
        )

        assert error is None, f"Error: {error}"
        assert result == ExecutionResult.SUCCESS
        assert "Result: Yes, found SYSTEM_FAILURE" in output

    def test_rlm_with_tools(self, agent, tmp_path):
        """Test RLM with inline tool code (no server imports)."""
        code = """
def multiply(a, b): return a * b
val = 5
res = multiply(val, 10)
print(f"Result: {res}")
"""
        agent.code_generator.generate_complete_code = MagicMock(return_value=(code, False))

        result, output, error = agent.execute_recursive_task(
            task_description="Multiply 5 by 10",
            context_data=None,
            verbose=False
        )

        assert error is None, f"Error: {error}"
        assert result == ExecutionResult.SUCCESS
        assert "Result: 50" in output

    @pytest.mark.skipif(not HAS_LITELLM, reason="litellm not installed")
    @patch("litellm.completion")
    def test_context_limit_comparison(self, mock_litellm_completion, agent, tmp_path, mock_llm_client):
        """Verify RLM succeeds where standard approach fails due to context limits."""
        large_content = "A" * 2000 + "SECRET_CODE"
        context_file = tmp_path / "huge_file.txt"
        context_file.write_text(large_content)

        def limited_context_llm(*args, **kwargs):
            messages = kwargs.get("messages", [])
            full_prompt = " ".join([m["content"] for m in messages])
            if len(full_prompt) > 500:
                raise ValueError("ContextLimitExceeded: Prompt length > 500 bytes")
            if "SECRET_CODE" in full_prompt:
                return MagicMock(choices=[MagicMock(message=MagicMock(content="Found: SECRET_CODE"))])
            return MagicMock(choices=[MagicMock(message=MagicMock(content="Not found"))])

        mock_litellm_completion.side_effect = limited_context_llm

        print("\n[Test] Simulating Standard Agent...")
        try:
            content = context_file.read_text()
            mock_litellm_completion(
                model="gpt-4",
                messages=[{"role": "user", "content": f"Find code in: {content}"}]
            )
            pytest.fail("Standard agent should have failed due to context limit")
        except ValueError as e:
            assert "ContextLimitExceeded" in str(e)

        print("[Test] Executing RLM...")
        rlm_code = """
chunk_size = 200
found = False
for i in range(0, len(CONTEXT_DATA), chunk_size):
    chunk = CONTEXT_DATA[i:i+chunk_size]
    try:
        res = ask_llm("Find code", chunk)
        if "Found" in res:
            print(res)
            found = True
            break
    except Exception as e:
        print(f"Error on chunk {i}: {e}")
if not found:
    print("Code not found")
"""
        agent.code_generator.generate_complete_code = MagicMock(return_value=(rlm_code, False))

        result, output, error = agent.execute_recursive_task(
            task_description="Find secret code",
            context_data=context_file,
            verbose=False
        )

        assert error is None, f"Error: {error}"
        assert result == ExecutionResult.SUCCESS
        assert "Found: SECRET_CODE" in output
