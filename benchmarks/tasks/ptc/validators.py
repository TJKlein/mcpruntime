"""Custom validators for PTC (Programmatic Tool Calling) tasks."""

import re
from typing import Any, Dict, Tuple


def validate_weather_output(task, output: str) -> Tuple[bool, float, Dict[str, Any]]:
    """Validate weather tool output - allows for mock data variability."""
    # Expected pattern: Temperature in Berlin: 22°C
    pattern = r"Temperature in (\w+): (\d+)°C"
    match = re.search(pattern, output)

    if not match:
        return False, 0.0, {"error": "Output doesn't match expected weather format", "actual": output}

    location = match.group(1)
    temp = int(match.group(2))

    # Check location matches
    if location.lower() != "berlin":
        return False, 0.0, {"error": f"Expected location 'Berlin', got '{location}'"}

    # Temperature should be reasonable (mock returns 15-30°C)
    if not (15 <= temp <= 30):
        return False, 0.0, {"error": f"Temperature {temp}°C out of expected range (15-30°C)"}

    return True, 1.0, {"location": location, "temperature": temp}


def validate_database_output(task, output: str) -> Tuple[bool, float, Dict[str, Any]]:
    """Validate database query output - allows for approximate average."""
    # Expected: Average user age: 35.0
    pattern = r"Average user age: ([\d.]+)"
    match = re.search(pattern, output)

    if not match:
        return False, 0.0, {"error": "Output doesn't match expected database format", "actual": output}

    avg = float(match.group(1))

    # Mock database returns reasonable values around 30-40
    if 25 <= avg <= 45:
        return True, 1.0, {"average_age": avg}

    return False, 0.0, {"error": f"Average {avg} outside expected range (25-45)"}


def validate_multi_tool_output(task, output: str) -> Tuple[bool, float, Dict[str, Any]]:
    """Validate multi-tool weather + calculator output."""
    # Expected: Average temperature across 3 cities: 22.0°C
    pattern = r"Average temperature across (\d+) cities: ([\d.]+)°C"
    match = re.search(pattern, output)

    if not match:
        return False, 0.0, {"error": "Output doesn't match expected multi-tool format", "actual": output}

    num_cities = int(match.group(1))
    avg = float(match.group(2))

    # Should have 3 cities, avg around 15-30°C
    if num_cities != 3:
        return False, 0.0, {"error": f"Expected 3 cities, got {num_cities}"}

    if not (15 <= avg <= 30):
        return False, 0.0, {"error": f"Average {avg}°C out of expected range (15-30°C)"}

    return True, 1.0, {"num_cities": num_cities, "average": avg}


def validate_forecast_analysis(task, output: str) -> Tuple[bool, float, Dict[str, Any]]:
    """Validate forecast analysis output."""
    # Expected: 5-day forecast for Berlin: min=18°C, max=26°C, range=8°C, avg=22.0°C
    pattern = r"5-day forecast for (\w+): min=(\d+)°C, max=(\d+)°C, range=(\d+)°C, avg=([\d.]+)°C"
    match = re.search(pattern, output)

    if not match:
        return False, 0.0, {"error": "Output doesn't match expected forecast format", "actual": output}

    location = match.group(1)
    min_temp = int(match.group(2))
    max_temp = int(match.group(3))
    temp_range = int(match.group(4))
    avg = float(match.group(5))

    if location.lower() != "berlin":
        return False, 0.0, {"error": f"Expected location 'Berlin', got '{location}'"}

    # Validate the math: range should be max - min
    if temp_range != max_temp - min_temp:
        return False, 0.0, {"error": f"Range {temp_range} != max({max_temp}) - min({min_temp})"}

    # Avg should be roughly between min and max
    if not (min_temp <= avg <= max_temp):
        return False, 0.0, {"error": f"Average {avg} not between min({min_temp}) and max({max_temp})"}

    return True, 1.0, {
        "location": location,
        "min": min_temp,
        "max": max_temp,
        "range": temp_range,
        "average": avg
    }
