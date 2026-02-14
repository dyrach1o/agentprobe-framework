"""Pytest-native assertion helpers for agent trace validation.

Provides fluent ``assert_trace()`` chains, ``assert_score()`` for evaluator
thresholds, and ``assert_cost()`` for budget checks. All assertions raise
standard ``AssertionError`` for native pytest introspection.
"""

from __future__ import annotations

import json
import re

from agentprobe.core.models import CostSummary, EvalResult, Trace
from agentprobe.cost.calculator import CostCalculator
from agentprobe.eval.base import BaseEvaluator


class TraceAssertion:
    """Fluent assertion chain for validating a ``Trace``.

    All methods return ``self`` for chaining. Failed assertions raise
    ``AssertionError`` immediately.

    Example:
        ```python
        assert_trace(trace).has_output().contains("hello").not_contains("error")
        ```
    """

    def __init__(self, trace: Trace) -> None:
        """Initialize with a trace to validate.

        Args:
            trace: The execution trace to assert against.
        """
        self._trace = trace

    def has_output(self) -> TraceAssertion:
        """Assert the trace has non-empty output text.

        Returns:
            Self for chaining.

        Raises:
            AssertionError: If output_text is empty.
        """
        if not self._trace.output_text:
            msg = "Expected trace to have non-empty output, but output_text is empty"
            raise AssertionError(msg)
        return self

    def contains(self, substring: str) -> TraceAssertion:
        """Assert the output contains a substring.

        Args:
            substring: The substring to search for.

        Returns:
            Self for chaining.

        Raises:
            AssertionError: If the substring is not found.
        """
        if substring not in self._trace.output_text:
            msg = f"Expected output to contain {substring!r}, but got: {self._trace.output_text!r}"
            raise AssertionError(msg)
        return self

    def not_contains(self, substring: str) -> TraceAssertion:
        """Assert the output does NOT contain a substring.

        Args:
            substring: The substring that should be absent.

        Returns:
            Self for chaining.

        Raises:
            AssertionError: If the substring is found.
        """
        if substring in self._trace.output_text:
            msg = (
                f"Expected output to NOT contain {substring!r}, "
                f"but it was found in: {self._trace.output_text!r}"
            )
            raise AssertionError(msg)
        return self

    def matches(self, pattern: str) -> TraceAssertion:
        """Assert the output matches a regex pattern.

        Args:
            pattern: The regex pattern to match against.

        Returns:
            Self for chaining.

        Raises:
            AssertionError: If the pattern does not match.
        """
        if re.search(pattern, self._trace.output_text) is None:
            msg = (
                f"Expected output to match pattern {pattern!r}, "
                f"but got: {self._trace.output_text!r}"
            )
            raise AssertionError(msg)
        return self

    def has_tool_calls(self, min_count: int = 1) -> TraceAssertion:
        """Assert the trace has at least ``min_count`` tool calls.

        Args:
            min_count: Minimum number of tool calls expected.

        Returns:
            Self for chaining.

        Raises:
            AssertionError: If fewer tool calls than expected.
        """
        actual = len(self._trace.tool_calls)
        if actual < min_count:
            msg = f"Expected at least {min_count} tool call(s), but got {actual}"
            raise AssertionError(msg)
        return self

    def has_tool(self, name: str) -> TraceAssertion:
        """Assert the trace contains a tool call with the given name.

        Args:
            name: The tool name to look for.

        Returns:
            Self for chaining.

        Raises:
            AssertionError: If no tool call with that name exists.
        """
        tool_names = [tc.tool_name for tc in self._trace.tool_calls]
        if name not in tool_names:
            msg = f"Expected tool call {name!r}, but found: {tool_names}"
            raise AssertionError(msg)
        return self

    def has_llm_calls(self, min_count: int = 1) -> TraceAssertion:
        """Assert the trace has at least ``min_count`` LLM calls.

        Args:
            min_count: Minimum number of LLM calls expected.

        Returns:
            Self for chaining.

        Raises:
            AssertionError: If fewer LLM calls than expected.
        """
        actual = len(self._trace.llm_calls)
        if actual < min_count:
            msg = f"Expected at least {min_count} LLM call(s), but got {actual}"
            raise AssertionError(msg)
        return self

    def output_length_less_than(self, n: int) -> TraceAssertion:
        """Assert the output length is less than ``n`` characters.

        Args:
            n: Maximum allowed length (exclusive).

        Returns:
            Self for chaining.

        Raises:
            AssertionError: If output is too long.
        """
        actual = len(self._trace.output_text)
        if actual >= n:
            msg = f"Expected output length < {n}, but got {actual}"
            raise AssertionError(msg)
        return self

    def output_is_valid_json(self) -> TraceAssertion:
        """Assert the output is valid JSON.

        Returns:
            Self for chaining.

        Raises:
            AssertionError: If output is not valid JSON.
        """
        try:
            json.loads(self._trace.output_text)
        except (json.JSONDecodeError, TypeError) as exc:
            msg = f"Expected output to be valid JSON, but got error: {exc}"
            raise AssertionError(msg) from None
        return self


def assert_trace(trace: Trace) -> TraceAssertion:
    """Create a fluent assertion chain for a trace.

    Args:
        trace: The execution trace to validate.

    Returns:
        A TraceAssertion for chaining assertions.

    Example:
        ```python
        assert_trace(trace).has_output().contains("hello").has_tool("search")
        ```
    """
    return TraceAssertion(trace)


async def assert_score(
    trace: Trace,
    evaluator: BaseEvaluator,
    *,
    min_score: float = 0.7,
    input_text: str = "",
    test_name: str = "assert_score",
) -> EvalResult:
    """Run an evaluator and assert the score meets a threshold.

    Args:
        trace: The execution trace to evaluate.
        evaluator: The evaluator to run.
        min_score: Minimum acceptable score (0.0 to 1.0).
        input_text: Input text for the test case context.
        test_name: Name for the synthetic test case.

    Returns:
        The EvalResult from the evaluator.

    Raises:
        AssertionError: If the score is below the threshold.
    """
    from agentprobe.core.models import TestCase

    test_case = TestCase(name=test_name, input_text=input_text)
    result = await evaluator.evaluate(test_case, trace)

    if result.score < min_score:
        msg = (
            f"Expected score >= {min_score}, but {evaluator.name} "
            f"returned {result.score:.4f} ({result.verdict.value}): {result.reason}"
        )
        raise AssertionError(msg)

    return result


def assert_cost(
    trace: Trace,
    *,
    max_usd: float,
    calculator: CostCalculator | None = None,
) -> CostSummary:
    """Calculate trace cost and assert it is within budget.

    Args:
        trace: The execution trace to price.
        max_usd: Maximum allowed cost in USD.
        calculator: Optional cost calculator. Uses default pricing if None.

    Returns:
        The CostSummary from the calculator.

    Raises:
        AssertionError: If the cost exceeds the budget.
    """
    calc = calculator or CostCalculator()
    summary = calc.calculate_trace_cost(trace)

    if summary.total_cost_usd > max_usd:
        msg = f"Expected cost <= ${max_usd:.6f}, but actual cost is ${summary.total_cost_usd:.6f}"
        raise AssertionError(msg)

    return summary
