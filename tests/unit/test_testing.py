"""Tests for the assert helper module."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from agentprobe.core.models import (
    CostSummary,
    EvalResult,
    EvalVerdict,
    LLMCall,
    ToolCall,
    Trace,
)
from agentprobe.cost.calculator import CostCalculator, PricingConfig, PricingEntry
from agentprobe.eval.base import BaseEvaluator
from agentprobe.testing import TraceAssertion, assert_cost, assert_score, assert_trace


def _make_trace(
    output_text: str = "Hello world",
    llm_calls: tuple[LLMCall, ...] = (),
    tool_calls: tuple[ToolCall, ...] = (),
) -> Trace:
    """Create a minimal trace for testing."""
    return Trace(
        agent_name="test-agent",
        output_text=output_text,
        llm_calls=llm_calls,
        tool_calls=tool_calls,
    )


class TestTraceAssertion:
    """Tests for the TraceAssertion fluent chain."""

    def test_has_output_passes(self) -> None:
        trace = _make_trace(output_text="some output")
        result = assert_trace(trace).has_output()
        assert isinstance(result, TraceAssertion)

    def test_has_output_fails_empty(self) -> None:
        trace = _make_trace(output_text="")
        with pytest.raises(AssertionError, match="non-empty output"):
            assert_trace(trace).has_output()

    def test_contains_passes(self) -> None:
        trace = _make_trace(output_text="Hello world")
        assert_trace(trace).contains("Hello")

    def test_contains_fails(self) -> None:
        trace = _make_trace(output_text="Hello world")
        with pytest.raises(AssertionError, match="contain"):
            assert_trace(trace).contains("goodbye")

    def test_not_contains_passes(self) -> None:
        trace = _make_trace(output_text="Hello world")
        assert_trace(trace).not_contains("error")

    def test_not_contains_fails(self) -> None:
        trace = _make_trace(output_text="Hello world")
        with pytest.raises(AssertionError, match="NOT contain"):
            assert_trace(trace).not_contains("Hello")

    def test_matches_passes(self) -> None:
        trace = _make_trace(output_text="Temperature is 72 degrees")
        assert_trace(trace).matches(r"\d+ degrees")

    def test_matches_fails(self) -> None:
        trace = _make_trace(output_text="No numbers here")
        with pytest.raises(AssertionError, match="match pattern"):
            assert_trace(trace).matches(r"\d+")

    def test_has_tool_calls_passes(self) -> None:
        tc = ToolCall(tool_name="search", tool_input={})
        trace = _make_trace(tool_calls=(tc,))
        assert_trace(trace).has_tool_calls(min_count=1)

    def test_has_tool_calls_fails(self) -> None:
        trace = _make_trace(tool_calls=())
        with pytest.raises(AssertionError, match="at least 1 tool call"):
            assert_trace(trace).has_tool_calls()

    def test_has_tool_passes(self) -> None:
        tc = ToolCall(tool_name="calculator", tool_input={})
        trace = _make_trace(tool_calls=(tc,))
        assert_trace(trace).has_tool("calculator")

    def test_has_tool_fails(self) -> None:
        tc = ToolCall(tool_name="search", tool_input={})
        trace = _make_trace(tool_calls=(tc,))
        with pytest.raises(AssertionError, match="Expected tool call"):
            assert_trace(trace).has_tool("calculator")

    def test_has_llm_calls_passes(self) -> None:
        call = LLMCall(model="test-model", input_tokens=10, output_tokens=5)
        trace = _make_trace(llm_calls=(call,))
        assert_trace(trace).has_llm_calls()

    def test_has_llm_calls_fails(self) -> None:
        trace = _make_trace(llm_calls=())
        with pytest.raises(AssertionError, match="at least 1 LLM call"):
            assert_trace(trace).has_llm_calls()

    def test_output_length_less_than_passes(self) -> None:
        trace = _make_trace(output_text="short")
        assert_trace(trace).output_length_less_than(100)

    def test_output_length_less_than_fails(self) -> None:
        trace = _make_trace(output_text="a" * 50)
        with pytest.raises(AssertionError, match="output length < 10"):
            assert_trace(trace).output_length_less_than(10)

    def test_output_is_valid_json_passes(self) -> None:
        trace = _make_trace(output_text='{"key": "value"}')
        assert_trace(trace).output_is_valid_json()

    def test_output_is_valid_json_fails(self) -> None:
        trace = _make_trace(output_text="not json")
        with pytest.raises(AssertionError, match="valid JSON"):
            assert_trace(trace).output_is_valid_json()

    def test_chaining_multiple_assertions(self) -> None:
        tc = ToolCall(tool_name="search", tool_input={})
        call = LLMCall(model="m", input_tokens=1, output_tokens=1)
        trace = _make_trace(
            output_text="Hello world",
            llm_calls=(call,),
            tool_calls=(tc,),
        )
        result = (
            assert_trace(trace)
            .has_output()
            .contains("Hello")
            .not_contains("error")
            .matches(r"Hello \w+")
            .has_tool_calls()
            .has_tool("search")
            .has_llm_calls()
            .output_length_less_than(100)
        )
        assert isinstance(result, TraceAssertion)

    def test_assert_trace_returns_trace_assertion(self) -> None:
        trace = _make_trace()
        result = assert_trace(trace)
        assert isinstance(result, TraceAssertion)


class TestAssertScore:
    """Tests for the assert_score async helper."""

    async def test_passes_when_score_above_threshold(self) -> None:
        trace = _make_trace(output_text="good output")
        evaluator = AsyncMock(spec=BaseEvaluator)
        evaluator.name = "mock-eval"
        evaluator.evaluate = AsyncMock(
            return_value=EvalResult(
                evaluator_name="mock-eval",
                verdict=EvalVerdict.PASS,
                score=0.9,
            )
        )
        result = await assert_score(trace, evaluator, min_score=0.7)
        assert result.score == 0.9

    async def test_fails_when_score_below_threshold(self) -> None:
        trace = _make_trace(output_text="bad output")
        evaluator = AsyncMock(spec=BaseEvaluator)
        evaluator.name = "mock-eval"
        evaluator.evaluate = AsyncMock(
            return_value=EvalResult(
                evaluator_name="mock-eval",
                verdict=EvalVerdict.FAIL,
                score=0.3,
                reason="Low quality",
            )
        )
        with pytest.raises(AssertionError, match=r"Expected score >= 0\.7"):
            await assert_score(trace, evaluator, min_score=0.7)

    async def test_returns_eval_result(self) -> None:
        trace = _make_trace()
        evaluator = AsyncMock(spec=BaseEvaluator)
        evaluator.name = "mock-eval"
        evaluator.evaluate = AsyncMock(
            return_value=EvalResult(
                evaluator_name="mock-eval",
                verdict=EvalVerdict.PASS,
                score=1.0,
            )
        )
        result = await assert_score(trace, evaluator)
        assert isinstance(result, EvalResult)
        assert result.evaluator_name == "mock-eval"


class TestAssertCost:
    """Tests for the assert_cost sync helper."""

    def _make_calculator(self) -> CostCalculator:
        pricing = PricingConfig(
            entries={
                "test-model": PricingEntry(
                    model="test-model",
                    input_cost_per_1k=0.01,
                    output_cost_per_1k=0.03,
                )
            }
        )
        return CostCalculator(pricing=pricing)

    def test_passes_when_within_budget(self) -> None:
        call = LLMCall(model="test-model", input_tokens=100, output_tokens=50)
        trace = _make_trace(llm_calls=(call,))
        calc = self._make_calculator()
        result = assert_cost(trace, max_usd=1.0, calculator=calc)
        assert isinstance(result, CostSummary)
        assert result.total_cost_usd <= 1.0

    def test_fails_when_over_budget(self) -> None:
        call = LLMCall(model="test-model", input_tokens=100000, output_tokens=100000)
        trace = _make_trace(llm_calls=(call,))
        calc = self._make_calculator()
        with pytest.raises(AssertionError, match="Expected cost <="):
            assert_cost(trace, max_usd=0.0001, calculator=calc)

    def test_returns_cost_summary(self) -> None:
        call = LLMCall(model="test-model", input_tokens=10, output_tokens=10)
        trace = _make_trace(llm_calls=(call,))
        calc = self._make_calculator()
        result = assert_cost(trace, max_usd=10.0, calculator=calc)
        assert isinstance(result, CostSummary)
