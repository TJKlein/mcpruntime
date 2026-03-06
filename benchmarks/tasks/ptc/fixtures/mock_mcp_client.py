"""Standalone mock MCP client for PTC tasks in isolated environments.

This module is copied to the workspace so PTC tasks can import it in Docker/subprocess.
"""

import random
from datetime import datetime
from typing import Any, Dict, Optional


def call_mcp_tool(tool_name: str, method: str, args: Optional[Dict] = None) -> Any:
    """Mock implementation of MCP tool calling for PTC tasks.

    Args:
        tool_name: Name of the tool ('calculator', 'weather', 'filesystem', 'database')
        method: Method to call on the tool
        args: Arguments for the method

    Returns:
        Mock result based on tool and method
    """
    args = args or {}

    if tool_name == 'calculator':
        return _handle_calculator(method, args)
    elif tool_name == 'weather':
        return _handle_weather(method, args)
    elif tool_name == 'filesystem':
        return _handle_filesystem(method, args)
    elif tool_name == 'database':
        return _handle_database(method, args)
    else:
        raise ValueError(f"Unknown tool: {tool_name}")


def _handle_calculator(method: str, args: Dict) -> Any:
    """Handle calculator tool methods."""
    if method == 'add':
        return args.get('a', 0) + args.get('b', 0)
    elif method == 'multiply':
        return args.get('a', 0) * args.get('b', 0)
    elif method == 'calculate':
        # Safe expression evaluator (no eval)
        expr = args.get('expression', '')
        return _safe_eval(expr)
    else:
        raise ValueError(f"Unknown calculator method: {method}")


def _safe_eval(expr: str) -> float:
    """Safely evaluate a mathematical expression without using eval()."""
    expr = expr.replace(' ', '')

    # Handle parentheses first
    while '(' in expr:
        # Find innermost parentheses
        start = expr.rfind('(')
        end = expr.find(')', start)
        if end == -1:
            raise ValueError("Mismatched parentheses")

        # Evaluate inside parentheses
        inner = expr[start + 1:end]
        inner_result = _safe_eval_simple(inner)

        # Replace parentheses with result
        expr = expr[:start] + str(inner_result) + expr[end + 1:]

    return _safe_eval_simple(expr)


def _safe_eval_simple(expr: str) -> float:
    """Evaluate expression without parentheses (order of operations)."""
    # Handle multiplication and division first
    tokens = _tokenize(expr)
    tokens = _apply_ops(tokens, ['*', '/'])
    # Then addition and subtraction
    tokens = _apply_ops(tokens, ['+', '-'])
    return float(tokens[0])


def _tokenize(expr: str) -> list:
    """Tokenize expression into numbers and operators."""
    tokens = []
    current = ''
    for char in expr:
        if char in '+-*/':
            if current:
                tokens.append(float(current))
                current = ''
            tokens.append(char)
        else:
            current += char
    if current:
        tokens.append(float(current))
    return tokens


def _apply_ops(tokens: list, ops: list) -> list:
    """Apply operations left to right."""
    result = [tokens[0]]
    i = 1
    while i < len(tokens):
        if tokens[i] in ops:
            left = result[-1]
            right = tokens[i + 1]
            if tokens[i] == '*':
                result[-1] = left * right
            elif tokens[i] == '/':
                result[-1] = left / right
            elif tokens[i] == '+':
                result[-1] = left + right
            elif tokens[i] == '-':
                result[-1] = left - right
            i += 2
        else:
            result.append(tokens[i])
            i += 1
    return result


def _handle_weather(method: str, args: Dict) -> Dict:
    """Handle weather tool methods."""
    location = args.get('location', 'Unknown')
    units = args.get('units', 'celsius')

    # Deterministic "random" based on location name
    loc_hash = sum(ord(c) for c in location) % 15

    if units == 'celsius':
        base_temp = 15 + loc_hash
    else:
        base_temp = 59 + (loc_hash * 9 // 5)

    conditions = ['sunny', 'cloudy', 'partly cloudy', 'rainy', 'windy']
    condition = conditions[loc_hash % len(conditions)]

    if method == 'get_weather':
        return {
            'location': location,
            'temperature': base_temp,
            'unit': units,
            'condition': condition,
            'humidity': 40 + (loc_hash * 2),
            'wind_speed': 5 + loc_hash,
            'timestamp': datetime.now().isoformat(),
        }
    elif method == 'get_forecast':
        days = args.get('days', 5)
        forecast = []
        for i in range(days):
            day_temp = base_temp + (i % 5) - 2
            forecast.append({
                'day': i + 1,
                'temperature': day_temp,
                'condition': conditions[(loc_hash + i) % len(conditions)],
            })
        return {
            'location': location,
            'unit': units,
            'forecast': forecast,
        }
    else:
        raise ValueError(f"Unknown weather method: {method}")


def _handle_filesystem(method: str, args: Dict) -> Any:
    """Handle filesystem tool methods."""
    import os

    path = args.get('path', '')

    if method == 'read_file':
        # Read from the actual filesystem (workspace is mounted)
        try:
            with open(path, 'r') as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {path}")
    elif method == 'list_directory':
        # List actual directory contents
        try:
            return os.listdir(path)
        except FileNotFoundError:
            raise FileNotFoundError(f"Directory not found: {path}")
    elif method == 'write_file':
        content = args.get('content', '')
        with open(path, 'w') as f:
            f.write(content)
        return True
    else:
        raise ValueError(f"Unknown filesystem method: {method}")


def _handle_database(method: str, args: Dict) -> Any:
    """Handle database tool methods."""
    table = args.get('table', '')
    columns = args.get('columns', [])

    if method == 'query':
        # Mock database with deterministic data
        if table == 'users':
            base_users = [
                {'id': 1, 'name': 'Alice', 'age': 25, 'email': 'alice@example.com'},
                {'id': 2, 'name': 'Bob', 'age': 30, 'email': 'bob@example.com'},
                {'id': 3, 'name': 'Carol', 'age': 35, 'email': 'carol@example.com'},
                {'id': 4, 'name': 'David', 'age': 40, 'email': 'david@example.com'},
                {'id': 5, 'name': 'Eve', 'age': 45, 'email': 'eve@example.com'},
            ]
            # Filter columns if specified
            if columns:
                return [{k: v for k, v in user.items() if k in columns} for user in base_users]
            return base_users
        elif table == 'products':
            return [
                {'id': 1, 'name': 'Widget', 'price': 9.99, 'stock': 100},
                {'id': 2, 'name': 'Gadget', 'price': 19.99, 'stock': 50},
                {'id': 3, 'name': 'Tool', 'price': 29.99, 'stock': 25},
            ]
        else:
            return []
    else:
        raise ValueError(f"Unknown database method: {method}")
