"""Unit tests for the Skill Evolution codebase (SkillWriter, AgentHelper hooks)."""

import os
import json
import ast
import tempfile
from pathlib import Path
import pytest

from client.skill_manager import SkillManager
from client.agent_helper import AgentHelper
from client.base import ExecutionResult
from config.schema import ExecutionConfig, OptimizationConfig, GuardrailConfig


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        yield temp_path


@pytest.fixture
def skill_manager(temp_workspace):
    """Create a SkillManager instance configured for the temp directory."""
    return SkillManager(workspace_dir=str(temp_workspace))


def test_is_worth_saving(skill_manager):
    """Test the heuristic for saving skills."""
    
    # 1. Snippet with no functions -> should not save
    simple_code = "print('hello')\nx = 5"
    assert not skill_manager.is_worth_saving(simple_code)

    # 2. Syntax error -> should not save
    bad_code = "def oops():\nprint(missing_indent"
    assert not skill_manager.is_worth_saving(bad_code)

    # 3. Simple function -> normally yes, but without interesting output it might fallback to True
    func_code = "def add(a, b):\n    return a + b\n"
    assert skill_manager.is_worth_saving(func_code)

    # 4. Function + interesting output
    assert skill_manager.is_worth_saving(func_code, output={"sum": 8})
    assert skill_manager.is_worth_saving(func_code, output=[1, 2, 3])


def test_extract_skill_from_code(skill_manager):
    """Test that bare code gets wrapped into a 'run' method properly."""
    raw_code = "x = 5\ny = 10\nresult = x + y"
    
    wrapped = skill_manager.extract_skill_from_code(
        raw_code, name="add_numbers", description="Adds two numbers"
    )
    
    # Check that it has a def run
    assert "def run(*args, **kwargs):" in wrapped
    assert "x = 5" in wrapped
    assert "return locals().get(\"result\", None)" in wrapped
    
    # Verify the code compiles
    tree = ast.parse(wrapped)
    assert any(isinstance(node, ast.FunctionDef) and node.name == 'run' for node in ast.walk(tree))


def test_extract_skill_from_code_with_existing_function(skill_manager):
    """Test extracting skill when it already defines a function."""
    raw_code = "def do_work(a):\n    return a * 2\n\nresult = do_work(5)"
    
    wrapped = skill_manager.extract_skill_from_code(
        raw_code, name="do_work_skill", description="Does work"
    )
    
    # Shouldn't wrap in another def run, but should add a run alias to the last func
    assert "def do_work(a):" in wrapped
    assert "\nrun = do_work\n" in wrapped


def test_update_skill_and_index(skill_manager, temp_workspace):
    """Test saving a skill, updating it, and checking the JSON index."""
    code = "def run():\n    return 'v1'\n"
    
    # 1. Save v1
    skill_manager.save_skill("test_skill", code, "Version 1")
    
    index_file = temp_workspace / "skills" / "skill_index.json"
    assert index_file.exists()
    
    with open(index_file, "r") as f:
        data = json.load(f)
        assert len(data) == 1
        assert data[0]["name"] == "test_skill"
        assert data[0]["description"] == "Version 1"

    # 2. Update to v2
    code_v2 = "def run():\n    return 'v2'\n"
    skill_manager.update_skill("test_skill", code_v2, "Version 2")
    
    with open(index_file, "r") as f:
        data = json.load(f)
        assert len(data) == 1  # Should still be 1, not duplicated!
        assert data[0]["name"] == "test_skill"
        assert data[0]["description"] == "Version 2"


def test_get_skill_listing(skill_manager):
    """Test generation of the prompt-injection listing string."""
    code1 = "def run(x: int) -> int:\n    return x*2\n"
    skill_manager.save_skill("double", code1, "Doubles a number")
    
    code2 = "def count_vowels(s: str):\n    pass\n\nrun = count_vowels\n"
    skill_manager.update_skill("vowels", code2, "Counts vowels")
    
    listing = skill_manager.get_skill_listing()
    
    assert "Available skills" in listing
    assert "double(x: int) -> int" in listing
    assert "Doubles a number" in listing
    # It parses the actual run signature from the AST or regex
    assert "vowels" in listing
    assert "Counts vowels" in listing


# A mock code executor that fakes success
class MockExecutor:
    def execute(self, code, context=None):
        from dataclasses import dataclass
        @dataclass
        class Res:
            value: str
        return Res(value="success"), "Fake output", None


def test_agent_helper_save_on_success(skill_manager):
    """Test that the agent helper auto-saves skills on success."""
    import sys
    from client.filesystem_helpers import FilesystemHelper
    
    fs_helper = FilesystemHelper(
        workspace_dir=str(skill_manager.workspace_dir),
        servers_dir=str(skill_manager.workspace_dir),
        skills_dir=str(skill_manager.skills_dir)
    )
    
    executor = MockExecutor()
    
    # Patch code generator to avoid LLM calls or filesystem dependencies during unit tests
    # Patch code generator to avoid LLM calls or filesystem dependencies during unit tests
    agent = AgentHelper(
        fs_helper=fs_helper,
        executor=executor,
        skill_manager=skill_manager,
        auto_save_skills=True
    )
    
    agent.code_generator.generate_complete_code = lambda **kwargs: "def my_cool_func():\n    return 42\n"
    
    # Run the execution wrapper
    agent.execute_task("Build a reliable weather parser", verbose=False)
    
    # Because MockExecutor returns "success" and it generates a function, it should be auto-saved.
    skills = skill_manager.list_skills()
    assert len(skills) >= 1
    
    # Name should be derived from prompt
    saved_name = skills[0]["name"]
    assert "weather" in saved_name or "build_a_reliable" in saved_name 
