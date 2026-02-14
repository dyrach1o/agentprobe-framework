"""Fluent assertion API for validating agent outputs and tool calls.

Provides ``expect()`` and ``expect_tool_calls()`` entry points that
return chainable expectation objects.
"""

from __future__ import annotations

import json
import re
from collections.abc import Sequence

from agentprobe.core.exceptions import AssertionFailedError
from agentprobe.core.models import AssertionResult, ToolCall


class OutputExpectation:
    """Fluent expectation chain for validating string output.

    Each assertion method returns ``self`` for chaining. Results
    accumulate in ``results`` and can be checked with ``all_passed()``.

    Example:
        ```python
        expect(output).to_contain("hello").to_not_contain("error")
        ```
    """

    def __init__(self, output: str) -> None:
        self._output = output
        self.results: list[AssertionResult] = []

    def _record(
        self,
        assertion_type: str,
        passed: bool,
        expected: object,
        actual: object,
        message: str = "",
    ) -> OutputExpectation:
        self.results.append(
            AssertionResult(
                assertion_type=assertion_type,
                passed=passed,
                expected=expected,
                actual=actual,
                message=message,
            )
        )
        if not passed:
            raise AssertionFailedError(
                assertion_type=assertion_type,
                expected=expected,
                actual=actual,
                message=message or None,
            )
        return self

    def to_contain(self, substring: str) -> OutputExpectation:
        """Assert that the output contains the given substring.

        Args:
            substring: The substring to search for.

        Returns:
            Self for chaining.
        """
        found = substring in self._output
        return self._record(
            "contain",
            found,
            substring,
            self._output[:200],
            f"Expected output to contain '{substring}'" if not found else "",
        )

    def to_not_contain(self, substring: str) -> OutputExpectation:
        """Assert that the output does NOT contain the given substring.

        Args:
            substring: The substring that should not appear.

        Returns:
            Self for chaining.
        """
        found = substring not in self._output
        return self._record(
            "not_contain",
            found,
            substring,
            self._output[:200],
            f"Expected output to not contain '{substring}'" if not found else "",
        )

    def to_match(self, pattern: str) -> OutputExpectation:
        """Assert that the output matches a regex pattern.

        Args:
            pattern: Regular expression pattern.

        Returns:
            Self for chaining.
        """
        matched = re.search(pattern, self._output) is not None
        return self._record(
            "match",
            matched,
            pattern,
            self._output[:200],
            f"Expected output to match pattern '{pattern}'" if not matched else "",
        )

    def to_have_length_less_than(self, max_length: int) -> OutputExpectation:
        """Assert that the output length is less than the given value.

        Args:
            max_length: Maximum allowed length.

        Returns:
            Self for chaining.
        """
        actual_len = len(self._output)
        passed = actual_len < max_length
        return self._record(
            "length_less_than",
            passed,
            max_length,
            actual_len,
            f"Expected length < {max_length}, got {actual_len}" if not passed else "",
        )

    def to_be_valid_json(self) -> OutputExpectation:
        """Assert that the output is valid JSON.

        Returns:
            Self for chaining.
        """
        try:
            json.loads(self._output)
            valid = True
        except (json.JSONDecodeError, TypeError):
            valid = False
        return self._record(
            "valid_json",
            valid,
            "valid JSON",
            self._output[:200],
            "Expected output to be valid JSON" if not valid else "",
        )

    def to_contain_any_of(self, substrings: Sequence[str]) -> OutputExpectation:
        """Assert that the output contains at least one of the substrings.

        Args:
            substrings: Substrings to check for.

        Returns:
            Self for chaining.
        """
        found = any(s in self._output for s in substrings)
        return self._record(
            "contain_any_of",
            found,
            list(substrings),
            self._output[:200],
            f"Expected output to contain one of {list(substrings)}" if not found else "",
        )

    def all_passed(self) -> bool:
        """Return True if all recorded assertions passed."""
        return all(r.passed for r in self.results)


class ToolCallExpectation:
    """Fluent expectation chain for validating tool call sequences.

    Example:
        ```python
        expect_tool_calls(trace.tool_calls).to_contain("search").to_have_count(2)
        ```
    """

    def __init__(self, tool_calls: Sequence[ToolCall]) -> None:
        self._tool_calls = list(tool_calls)
        self._names = [tc.tool_name for tc in self._tool_calls]
        self.results: list[AssertionResult] = []

    def _record(
        self,
        assertion_type: str,
        passed: bool,
        expected: object,
        actual: object,
        message: str = "",
    ) -> ToolCallExpectation:
        self.results.append(
            AssertionResult(
                assertion_type=assertion_type,
                passed=passed,
                expected=expected,
                actual=actual,
                message=message,
            )
        )
        if not passed:
            raise AssertionFailedError(
                assertion_type=assertion_type,
                expected=expected,
                actual=actual,
                message=message or None,
            )
        return self

    def to_contain(self, tool_name: str) -> ToolCallExpectation:
        """Assert that a tool with the given name was called.

        Args:
            tool_name: The expected tool name.

        Returns:
            Self for chaining.
        """
        found = tool_name in self._names
        return self._record(
            "tool_contain",
            found,
            tool_name,
            self._names,
            f"Expected tool '{tool_name}' in calls {self._names}" if not found else "",
        )

    def to_have_sequence(self, expected_sequence: Sequence[str]) -> ToolCallExpectation:
        """Assert that tools were called in the given order.

        The expected sequence must appear as a contiguous subsequence
        in the actual tool call names.

        Args:
            expected_sequence: Ordered tool names to match.

        Returns:
            Self for chaining.
        """
        expected = list(expected_sequence)
        seq_len = len(expected)
        found = (
            any(
                self._names[i : i + seq_len] == expected
                for i in range(len(self._names) - seq_len + 1)
            )
            if seq_len <= len(self._names)
            else False
        )
        return self._record(
            "tool_sequence",
            found,
            expected,
            self._names,
            f"Expected sequence {expected} in calls {self._names}" if not found else "",
        )

    def to_have_count(self, count: int) -> ToolCallExpectation:
        """Assert the total number of tool calls.

        Args:
            count: Expected number of tool calls.

        Returns:
            Self for chaining.
        """
        actual = len(self._tool_calls)
        passed = actual == count
        return self._record(
            "tool_count",
            passed,
            count,
            actual,
            f"Expected {count} tool calls, got {actual}" if not passed else "",
        )

    def all_passed(self) -> bool:
        """Return True if all recorded assertions passed."""
        return all(r.passed for r in self.results)


def expect(output: str) -> OutputExpectation:
    """Create a fluent output expectation.

    Args:
        output: The agent output string to validate.

    Returns:
        An OutputExpectation for chaining assertions.
    """
    return OutputExpectation(output)


def expect_tool_calls(tool_calls: Sequence[ToolCall]) -> ToolCallExpectation:
    """Create a fluent tool call expectation.

    Args:
        tool_calls: The sequence of tool calls to validate.

    Returns:
        A ToolCallExpectation for chaining assertions.
    """
    return ToolCallExpectation(tool_calls)
