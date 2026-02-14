"""Tests for the multi-turn conversation runner."""

from __future__ import annotations

import pytest

from agentprobe.core.conversation import ConversationRunner
from agentprobe.core.models import (
    ConversationTurn,
    EvalResult,
    EvalVerdict,
    TestCase,
    Trace,
)
from agentprobe.eval.base import BaseEvaluator
from tests.fixtures.agents import MockAdapter


class _AlwaysPassEvaluator(BaseEvaluator):
    """Evaluator that always returns a passing result."""

    async def _evaluate(self, test_case: TestCase, trace: Trace) -> EvalResult:
        return EvalResult(
            evaluator_name=self.name,
            verdict=EvalVerdict.PASS,
            score=1.0,
            reason="pass",
        )


class _AlwaysFailEvaluator(BaseEvaluator):
    """Evaluator that always returns a failing result."""

    async def _evaluate(self, test_case: TestCase, trace: Trace) -> EvalResult:
        return EvalResult(
            evaluator_name=self.name,
            verdict=EvalVerdict.FAIL,
            score=0.2,
            reason="fail",
        )


class TestConversationRunner:
    """Tests for ConversationRunner."""

    @pytest.fixture
    def adapter(self) -> MockAdapter:
        return MockAdapter(output="mock reply")

    @pytest.fixture
    def pass_evaluator(self) -> _AlwaysPassEvaluator:
        return _AlwaysPassEvaluator("pass-eval")

    @pytest.fixture
    def fail_evaluator(self) -> _AlwaysFailEvaluator:
        return _AlwaysFailEvaluator("fail-eval")

    async def test_single_turn(self, adapter: MockAdapter) -> None:
        runner = ConversationRunner()
        turns = [ConversationTurn(input_text="Hello")]
        result = await runner.run(adapter, turns)

        assert result.total_turns == 1
        assert result.passed_turns == 1
        assert result.aggregate_score == 1.0
        assert adapter.call_count == 1

    async def test_multi_turn(self, adapter: MockAdapter) -> None:
        runner = ConversationRunner()
        turns = [
            ConversationTurn(input_text="Turn 1"),
            ConversationTurn(input_text="Turn 2"),
            ConversationTurn(input_text="Turn 3"),
        ]
        result = await runner.run(adapter, turns)

        assert result.total_turns == 3
        assert result.passed_turns == 3
        assert adapter.call_count == 3

    async def test_context_passing(self, adapter: MockAdapter) -> None:
        runner = ConversationRunner()
        turns = [
            ConversationTurn(input_text="First"),
            ConversationTurn(input_text="Second"),
        ]
        await runner.run(adapter, turns, pass_context=True)

        # Second call should include previous output
        assert adapter.last_input is not None
        assert "mock reply" in adapter.last_input
        assert "Second" in adapter.last_input

    async def test_no_context_passing(self, adapter: MockAdapter) -> None:
        runner = ConversationRunner()
        turns = [
            ConversationTurn(input_text="First"),
            ConversationTurn(input_text="Second"),
        ]
        await runner.run(adapter, turns, pass_context=False)

        assert adapter.last_input == "Second"

    async def test_per_turn_evaluators_pass(
        self,
        adapter: MockAdapter,
        pass_evaluator: _AlwaysPassEvaluator,
    ) -> None:
        runner = ConversationRunner(evaluators={"pass-eval": pass_evaluator})
        turns = [
            ConversationTurn(input_text="Test", evaluators=("pass-eval",)),
        ]
        result = await runner.run(adapter, turns)

        assert result.passed_turns == 1
        assert result.aggregate_score == 1.0
        assert len(result.turn_results[0].eval_results) == 1

    async def test_per_turn_evaluators_fail(
        self,
        adapter: MockAdapter,
        fail_evaluator: _AlwaysFailEvaluator,
    ) -> None:
        runner = ConversationRunner(evaluators={"fail-eval": fail_evaluator})
        turns = [
            ConversationTurn(input_text="Test", evaluators=("fail-eval",)),
        ]
        result = await runner.run(adapter, turns)

        assert result.passed_turns == 0
        assert result.aggregate_score == 0.2

    async def test_missing_evaluator_skipped(self, adapter: MockAdapter) -> None:
        runner = ConversationRunner(evaluators={})
        turns = [
            ConversationTurn(input_text="Test", evaluators=("nonexistent",)),
        ]
        result = await runner.run(adapter, turns)

        # No evals run, but trace exists -> pass
        assert result.passed_turns == 1
        assert len(result.turn_results[0].eval_results) == 0

    async def test_adapter_error_handled(self) -> None:
        adapter = MockAdapter(error=RuntimeError("boom"))
        runner = ConversationRunner()
        turns = [ConversationTurn(input_text="Test")]
        result = await runner.run(adapter, turns)

        assert result.total_turns == 1
        assert result.passed_turns == 0
        assert result.turn_results[0].trace is None
        assert result.aggregate_score == 0.0

    async def test_empty_turns(self, adapter: MockAdapter) -> None:
        runner = ConversationRunner()
        result = await runner.run(adapter, [])

        assert result.total_turns == 0
        assert result.aggregate_score == 0.0

    async def test_agent_name_in_result(self, adapter: MockAdapter) -> None:
        runner = ConversationRunner()
        turns = [ConversationTurn(input_text="test")]
        result = await runner.run(adapter, turns)

        assert result.agent_name == "mock"

    async def test_duration_tracking(self, adapter: MockAdapter) -> None:
        runner = ConversationRunner()
        turns = [ConversationTurn(input_text="Test")]
        result = await runner.run(adapter, turns)

        assert result.total_duration_ms >= 0
        assert result.turn_results[0].duration_ms >= 0
