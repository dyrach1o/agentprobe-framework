"""Tests for the fluent assertion API."""

from __future__ import annotations

import pytest

from agentprobe.core.assertions import (
    expect,
    expect_tool_calls,
)
from agentprobe.core.exceptions import AssertionFailedError
from agentprobe.core.models import ToolCall


class TestOutputExpectation:
    """Tests for OutputExpectation assertions."""

    def test_to_contain_passes(self) -> None:
        result = expect("hello world").to_contain("hello")
        assert result.all_passed()

    def test_to_contain_fails(self) -> None:
        with pytest.raises(AssertionFailedError, match="contain"):
            expect("hello world").to_contain("goodbye")

    def test_to_not_contain_passes(self) -> None:
        result = expect("hello world").to_not_contain("goodbye")
        assert result.all_passed()

    def test_to_not_contain_fails(self) -> None:
        with pytest.raises(AssertionFailedError, match="not contain"):
            expect("hello world").to_not_contain("hello")

    def test_to_match_passes(self) -> None:
        result = expect("order #12345").to_match(r"#\d+")
        assert result.all_passed()

    def test_to_match_fails(self) -> None:
        with pytest.raises(AssertionFailedError, match="match"):
            expect("no numbers here").to_match(r"\d+")

    def test_to_have_length_less_than_passes(self) -> None:
        result = expect("short").to_have_length_less_than(100)
        assert result.all_passed()

    def test_to_have_length_less_than_fails(self) -> None:
        with pytest.raises(AssertionFailedError, match="length"):
            expect("hello").to_have_length_less_than(3)

    def test_to_be_valid_json_passes(self) -> None:
        result = expect('{"key": "value"}').to_be_valid_json()
        assert result.all_passed()

    def test_to_be_valid_json_fails(self) -> None:
        with pytest.raises(AssertionFailedError, match="valid JSON"):
            expect("not json").to_be_valid_json()

    def test_to_contain_any_of_passes(self) -> None:
        result = expect("hello world").to_contain_any_of(["foo", "hello", "bar"])
        assert result.all_passed()

    def test_to_contain_any_of_fails(self) -> None:
        with pytest.raises(AssertionFailedError, match="contain one of"):
            expect("hello world").to_contain_any_of(["foo", "bar", "baz"])

    def test_chaining_multiple_assertions(self) -> None:
        result = (
            expect("hello world 123")
            .to_contain("hello")
            .to_not_contain("goodbye")
            .to_match(r"\d+")
            .to_have_length_less_than(100)
        )
        assert result.all_passed()
        assert len(result.results) == 4

    def test_chaining_stops_on_failure(self) -> None:
        with pytest.raises(AssertionFailedError):
            expect("hello").to_contain("hello").to_contain("missing")

    def test_results_accumulated(self) -> None:
        result = expect("hello").to_contain("hello")
        assert len(result.results) == 1
        assert result.results[0].assertion_type == "contain"
        assert result.results[0].passed is True


class TestToolCallExpectation:
    """Tests for ToolCallExpectation assertions."""

    @pytest.fixture
    def tool_calls(self) -> list[ToolCall]:
        return [
            ToolCall(tool_name="search", tool_input={"query": "test"}),
            ToolCall(tool_name="calculate", tool_input={"expr": "1+1"}),
            ToolCall(tool_name="search", tool_input={"query": "more"}),
        ]

    def test_to_contain_passes(self, tool_calls: list[ToolCall]) -> None:
        result = expect_tool_calls(tool_calls).to_contain("search")
        assert result.all_passed()

    def test_to_contain_fails(self, tool_calls: list[ToolCall]) -> None:
        with pytest.raises(AssertionFailedError, match="Expected tool"):
            expect_tool_calls(tool_calls).to_contain("email")

    def test_to_have_sequence_passes(self, tool_calls: list[ToolCall]) -> None:
        result = expect_tool_calls(tool_calls).to_have_sequence(["search", "calculate"])
        assert result.all_passed()

    def test_to_have_sequence_fails(self, tool_calls: list[ToolCall]) -> None:
        with pytest.raises(AssertionFailedError, match="Expected sequence"):
            expect_tool_calls(tool_calls).to_have_sequence(["calculate", "search", "calculate"])

    def test_to_have_count_passes(self, tool_calls: list[ToolCall]) -> None:
        result = expect_tool_calls(tool_calls).to_have_count(3)
        assert result.all_passed()

    def test_to_have_count_fails(self, tool_calls: list[ToolCall]) -> None:
        with pytest.raises(AssertionFailedError, match="Expected 5 tool calls"):
            expect_tool_calls(tool_calls).to_have_count(5)

    def test_chaining(self, tool_calls: list[ToolCall]) -> None:
        result = (
            expect_tool_calls(tool_calls)
            .to_contain("search")
            .to_have_count(3)
            .to_have_sequence(["search", "calculate"])
        )
        assert result.all_passed()

    def test_empty_tool_calls(self) -> None:
        result = expect_tool_calls([]).to_have_count(0)
        assert result.all_passed()

    def test_empty_sequence_check(self, tool_calls: list[ToolCall]) -> None:
        with pytest.raises(AssertionFailedError):
            expect_tool_calls([]).to_contain("search")


class TestParametrizedAssertions:
    """Parametrized boundary tests for assertions."""

    @pytest.mark.parametrize(
        "text,substring,should_pass",
        [
            ("hello world", "hello", True),
            ("hello world", "HELLO", False),
            ("", "", True),
            ("abc", "abc", True),
            ("abc", "abcd", False),
        ],
    )
    def test_contain_boundaries(self, text: str, substring: str, should_pass: bool) -> None:
        if should_pass:
            result = expect(text).to_contain(substring)
            assert result.all_passed()
        else:
            with pytest.raises(AssertionFailedError):
                expect(text).to_contain(substring)

    @pytest.mark.parametrize(
        "text,max_len,should_pass",
        [
            ("", 1, True),
            ("a", 1, True),
            ("ab", 1, False),
            ("hello", 5, True),
            ("hello!", 5, False),
        ],
    )
    def test_length_boundaries(self, text: str, max_len: int, should_pass: bool) -> None:
        if should_pass:
            result = expect(text).to_have_length_less_than(max_len + 1)
            assert result.all_passed()
        else:
            with pytest.raises(AssertionFailedError):
                expect(text).to_have_length_less_than(max_len)

    @pytest.mark.parametrize(
        "text,is_valid",
        [
            ('{"a": 1}', True),
            ("[1, 2, 3]", True),
            ('"string"', True),
            ("42", True),
            ("{invalid}", False),
            ("", False),
        ],
    )
    def test_json_validation_boundaries(self, text: str, is_valid: bool) -> None:
        if is_valid:
            result = expect(text).to_be_valid_json()
            assert result.all_passed()
        else:
            with pytest.raises(AssertionFailedError):
                expect(text).to_be_valid_json()
