"""Recursive Agent implementation for infinite context tasks.

This module implements the Recursive Language Model (RLM) pattern, treating context
as a variable in the environment that can be programmatically inspected and
recursively queried by the LLM.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from client.agent_helper import AgentHelper
from client.code_generator import CodeGenerator, HAS_LITELLM
from config.schema import LLMConfig

if HAS_LITELLM:
    import litellm  # noqa: F401 - used in ask_llm callback

logger = logging.getLogger(__name__)

class RecursiveAgent(AgentHelper):
    """Agent that handles infinite context using recursive calls."""

    def __init__(self, *args, **kwargs):
        """Initialize recursive agent."""
        super().__init__(*args, **kwargs)
        self.context_data = None
        
        # Ensure we have an LLM client
        if self.llm_config and self.llm_config.enabled:
            # CodeGenerator already initializes connection, but we might need 
            # a direct client for the 'ask_llm' callback. 
            # We can reuse the one from CodeGenerator if accessible, or create new one.
            pass

    def execute_recursive_task(
        self, 
        task_description: str, 
        context_data: Union[str, Path],
        verbose: bool = True,
        required_tools: Optional[Dict[str, List[str]]] = None
    ) -> Any:
        """Execute a task with large context using RLM pattern.
        
        Args:
            task_description: The goal (e.g. "Find the error code")
            context_data: The large context (string or Path to file)
            verbose: Whether to print progress
            required_tools: Optional explicit tools to use
            
        Returns:
            Execution result
        """
        # Load context data
        if isinstance(context_data, Path) or (isinstance(context_data, str) and os.path.exists(context_data)):
            try:
                with open(context_data, "r", encoding="utf-8") as f:
                    self.context_data = f.read()
            except Exception as e:
                return None, None, f"Failed to load context file: {e}"
        else:
            self.context_data = context_data

        # Define the recursive callback
        def ask_llm(prompt: str, data: str) -> str:
            """Recursive callback to query LLM with a chunk of data."""
            if verbose:
                print(f"\n[RLM] ask_llm called with prompt: '{prompt}' and data length: {len(data)}")
            
            # Construct a prompt for the recursive call
            if not HAS_LITELLM:
                return "Error: litellm package not installed"
                
            full_prompt = f"Context:\n{data}\n\nQuestion: {prompt}\n\nAnswer:"
            
            try:
                # Use same config as main agent (credentials from code_generator or env)
                model_name = self.code_generator._model_name or ""
                api_key = getattr(self.code_generator, "_api_key", None) or (self.llm_config.api_key if self.llm_config else None) or os.environ.get("AZURE_OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY")
                api_base = getattr(self.code_generator, "_api_base", None) or (self.llm_config.azure_endpoint if self.llm_config else None) or os.environ.get("AZURE_OPENAI_ENDPOINT")
                api_version = getattr(self.code_generator, "_api_version", None) or (self.llm_config.azure_api_version if self.llm_config else None) or os.environ.get("AZURE_OPENAI_API_VERSION")

                completion_params = {
                    "model": model_name,
                    "messages": [
                        {"role": "system", "content": "You are a helpful assistant. Answer the question based on the context provided."},
                        {"role": "user", "content": full_prompt}
                    ],
                    "temperature": 1.0 if "gpt-5.2-chat" in model_name else 0.0,
                }
                if api_key:
                    completion_params["api_key"] = api_key
                if api_base:
                    completion_params["api_base"] = api_base
                if api_version:
                    completion_params["api_version"] = api_version

                # Litellm token limits (Azure gpt-5.2-chat uses max_completion_tokens only)
                val = getattr(self.llm_config, "max_completion_tokens", None) or self.llm_config.max_tokens if self.llm_config else 2000
                if "gpt-5" in model_name or "gpt-4o" in model_name or (self.llm_config and self.llm_config.provider == "azure_openai"):
                    completion_params["max_completion_tokens"] = val
                else:
                    completion_params["max_tokens"] = val

                response = litellm.completion(**completion_params)
                answer = response.choices[0].message.content.strip()
                if verbose:
                    print(f"[RLM] Answer: {answer[:100]}...")
                return answer
            except Exception as e:
                logger.error(f"ask_llm failed: {e}")
                return f"Error during LLM call: {e}"

        # Prepare context for execution
        # Prepare context for execution
        execution_context = {
            "inputs": {},
            "functions": {
                "ask_llm": ask_llm
            }
        }
        
        if self.context_data is not None:
             execution_context["inputs"]["CONTEXT_DATA"] = self.context_data
             
             # Modify task description to include RLM instructions
             rlm_instructions = (
                "\n\nIMPORTANT: The relevant context is loaded into the variable 'CONTEXT_DATA'. "
                "It is too large to read at once. "
                "Write Python code to inspect, slice, or search this variable. "
                "CONTEXT_DATA is a plain Python variable already in scope — access it directly, do NOT call globals(). "
                "To reason about a specific chunk, call 'ask_llm(question, chunk_string)'. "
                "Do NOT print the entire CONTEXT_DATA. "
                "When you find the answer, print it clearly so it appears in the output. "
                "Example pattern:\n"
                "chunk_size = 2000\n"
                "chunks = [CONTEXT_DATA[i:i+chunk_size] for i in range(0, len(CONTEXT_DATA), chunk_size)]\n"
                "found = None\n"
                "for chunk in chunks:\n"
                "    answer = ask_llm('If this chunk contains relevant information to answer the task, reply FOUND: <answer>. Otherwise reply NOT_FOUND.', chunk)\n"
                "    if 'FOUND:' in answer:\n"
                "        found = answer\n"
                "        break\n"
                "if found:\n"
                "    print(found)\n"
                "else:\n"
                "    print('No result found in CONTEXT_DATA.')\n"
            )
             full_task = task_description + rlm_instructions
        else:
            full_task = task_description
        
        # We need a way to tell code_generator NOT to generate imports for ask_llm
        # or CONTEXT_DATA, as they are injected.
        # Currently CodeGenerator generates tool imports.
        # We can pass empty required_tools if we only use RLM, or mix them.
        
        # For now, let's use the standard flow but with our augmented task.
        # The CodeGenerator might try to find tools.
        
        # Get available skills from skill manager if present
        skill_listing = None
        if self.skill_manager:
            skill_listing = self.skill_manager.get_skill_listing()
            
        # These variables are not defined in the original context, assuming they are meant to be empty or defined elsewhere.
        task_specific_calls = "" 
        extended_header = ""

        code = self.code_generator.generate_complete_code(
            required_tools=required_tools,
            task_description=full_task, # Use full_task here, not original task_description
            task_specific_calls=task_specific_calls,
            header_comment=extended_header,
            skill_listing=skill_listing,
        )
        
        # Post-process code for Monty (inline tools, remove incompatible imports)
        # This is a hack because Monty doesn't support file-based imports well yet
        if hasattr(self.executor, "execution_config") and self.executor.execution_config.sandbox_type == "monty":
             # 1. Inline required tools
            tool_code_prelude = ""
            lines = code.splitlines()
            new_lines = []
            
            for line in lines:
                # Remove traceback and mcp_client imports (not available/needed in Monty)
                if "import traceback" in line or "traceback.print_exc" in line:
                    continue
                if "client.mcp_client" in line:
                    indentation = line[:len(line) - len(line.lstrip())]
                    new_lines.append(f"{indentation}pass # {line.strip()} # INLINED")
                    continue
                
                # Check for tool or skill imports to inline
                # Pattern: from servers.{server}.{tool} import {func}
                # or from skills.{skill} import {func}
                if line.strip().startswith("from servers.") or line.strip().startswith("from skills."):
                    # Comment out the import and add pass to keep block valid, preserving indentation
                    indentation = line[:len(line) - len(line.lstrip())]
                    new_lines.append(f"{indentation}pass # {line.strip()} # INLINED")
                    
                    try:
                        # Extract module and name
                        parts = line.strip().split()
                        # parts[1] is 'servers.calculator.multiply' or 'skills.fetch_weather'
                        module_path = parts[1].split(".")
                        
                        if module_path[0] == "servers" and len(module_path) >= 2:
                            server_name = module_path[1]
                            tool_name = parts[3] # import {tool_name}
                            
                            # Read tool source
                            # Tool file is usually servers/{server}/{tool}.py
                            # But sometimes it's mapped differently. 
                            tool_source = self.fs_helper.read_tool_file(server_name, tool_name)
                            if tool_source:
                                tool_code_prelude += f"\n# Tool: {tool_name}\n{tool_source}\n"
                        
                        elif module_path[0] == "skills" and len(module_path) >= 2:
                            skill_name = module_path[1]
                            
                            # Read skill source from workspace/skills
                            skill_file = Path(self.execution_config.workspace_dir) / "skills" / f"{skill_name}.py"
                            if skill_file.exists():
                                skill_source = skill_file.read_text(encoding="utf-8")
                                tool_code_prelude += f"\n# Skill: {skill_name}\n{skill_source}\n"
                                
                    except Exception as e:
                        logger.warning(f"Failed to inline module from line '{line}': {e}")
                else:
                    new_lines.append(line)
            
            code = tool_code_prelude + "\n".join(new_lines)
        
        # Execute with context
        # We need to access self.context_data and ask_llm if not passed explicitly,
        # but better to pass them via the specialized execute_recursive_task method
        # which constructs 'execution_context'.
        
        # Execute using parent's execute_task with our context
        result, output, error = self.executor.execute(code, context=execution_context)
        
        # Save successful skills
        if result and result.value == "success" and getattr(self, "auto_save_skills", False) and self.skill_manager:
            self._maybe_save_skill(task_description, code, output, verbose)
            
        return result, output, error

