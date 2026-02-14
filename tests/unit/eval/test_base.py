"""Tests for the BaseEvaluator abstract base class."""

from __future__ import annotations

import pytest

from agentprobe.core.exceptions import EvaluatorError
from agentprobe.core.models import EvalResult, EvalVerdict, TestCase, Trace
from agentprobe.eval.base import BaseEvaluator


class _PassingEvaluator(BaseEvaluator):
    """Concrete evaluator that always passes."""

    async def _evaluate(self, test_case: TestCase, trace: Trace) -> EvalResult:
        return EvalResult(
            evaluator_name=self.name,
            verdict=EvalVerdict.PASS,
            score=1.0,
            reason="All good",
        )


class _FailingEvaluator(BaseEvaluator):
    """Concrete evaluator that raises a generic exception."""

    async def _evaluate(self, test_case: TestCase, trace: Trace) -> EvalResult:
        msg = "something broke"
        raise RuntimeError(msg)


class _EvaluatorErrorRaiser(BaseEvaluator):
    """Concrete evaluator that raises EvaluatorError directly."""

    async def _evaluate(self, test_case: TestCase, trace: Trace) -> EvalResult:
        raise EvaluatorError("deliberate failure")


class TestBaseEvaluator:
    """Tests for BaseEvaluator template method."""

    @pytest.fixture
    def test_case(self) -> TestCase:
        return TestCase(name="test_basic", input_text="Hello")

    @pytest.fixture
    def trace(self) -> Trace:
        return Trace(agent_name="test-agent", output_text="Hi there")

    def test_cannot_instantiate_abstract(self) -> None:
        with pytest.raises(TypeError, match="abstract"):
            BaseEvaluator("test")  # type: ignore[abstract]

    def test_name_property(self) -> None:
        evaluator = _PassingEvaluator("my-eval")
        assert evaluator.name == "my-eval"

    @pytest.mark.asyncio
    async def test_passing_evaluation(self, test_case: TestCase, trace: Trace) -> None:
        evaluator = _PassingEvaluator("pass-eval")
        result = await evaluator.evaluate(test_case, trace)
        assert result.verdict == EvalVerdict.PASS
        assert result.score == 1.0
        assert result.evaluator_name == "pass-eval"

    @pytest.mark.asyncio
    async def test_generic_exception_returns_error_result(
        self, test_case: TestCase, trace: Trace
    ) -> None:
        evaluator = _FailingEvaluator("fail-eval")
        result = await evaluator.evaluate(test_case, trace)
        assert result.verdict == EvalVerdict.ERROR
        assert result.score == 0.0
        assert "something broke" in result.reason

    @pytest.mark.asyncio
    async def test_evaluator_error_propagates(self, test_case: TestCase, trace: Trace) -> None:
        evaluator = _EvaluatorErrorRaiser("error-eval")
        with pytest.raises(EvaluatorError, match="deliberate failure"):
            await evaluator.evaluate(test_case, trace)
