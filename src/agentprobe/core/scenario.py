"""Scenario decorator and registry for defining agent test cases.

The ``@scenario`` decorator marks functions as test scenarios and
registers them in a global registry for discovery by the test runner.
"""

from __future__ import annotations

import functools
from collections.abc import Callable
from typing import Any

from agentprobe.core.models import TestCase

# Global registry: module_path -> list of TestCase
_scenario_registry: dict[str, list[TestCase]] = {}


def scenario(
    name: str | None = None,
    *,
    input_text: str = "",
    expected_output: str | None = None,
    tags: list[str] | None = None,
    timeout: float = 30.0,
    evaluators: list[str] | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator that registers a function as a test scenario.

    The decorated function can optionally accept a ``TestCase`` argument
    and mutate it (e.g. setting dynamic input). If it returns a string,
    that string overrides ``input_text``.

    Args:
        name: Test name. Defaults to the function name.
        input_text: The input prompt to send to the agent.
        expected_output: Optional expected output for comparison.
        tags: Tags for filtering and grouping.
        timeout: Maximum execution time in seconds.
        evaluators: Names of evaluators to run.

    Returns:
        A decorator that registers the function.

    Example:
        ```python
        @scenario(name="greeting_test", input_text="Hello!")
        def test_greeting():
            pass
        ```
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        resolved_name = name or func.__name__
        test_case = TestCase(
            name=resolved_name,
            input_text=input_text,
            expected_output=expected_output,
            tags=tags or [],
            timeout_seconds=timeout,
            evaluators=evaluators or [],
            metadata={"source_function": func.__qualname__},
        )

        module = func.__module__
        _scenario_registry.setdefault(module, []).append(test_case)

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)

        wrapper._agentprobe_scenario = test_case  # type: ignore[attr-defined]
        return wrapper

    return decorator


def get_scenarios(module_name: str | None = None) -> list[TestCase]:
    """Retrieve registered scenarios.

    Args:
        module_name: If provided, return scenarios from this module only.
            If None, return all registered scenarios.

    Returns:
        A list of TestCase objects.
    """
    if module_name is not None:
        return list(_scenario_registry.get(module_name, []))
    return [tc for cases in _scenario_registry.values() for tc in cases]


def clear_registry() -> None:
    """Clear all registered scenarios. Primarily for testing."""
    _scenario_registry.clear()
