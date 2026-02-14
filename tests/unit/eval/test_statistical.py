"""Tests for the statistical evaluator."""

from __future__ import annotations

import pytest

from agentprobe.core.models import (
    EvalResult,
    EvalVerdict,
    TestCase,
    Trace,
)
from agentprobe.eval.base import BaseEvaluator
from agentprobe.eval.statistical import StatisticalEvaluator, _percentile
from tests.fixtures.traces import make_trace


class _DeterministicEvaluator(BaseEvaluator):
    """Test evaluator that returns scores from a pre-defined list."""

    def __init__(self, scores: list[float]) -> None:
        super().__init__("deterministic")
        self._scores = list(scores)
        self._call_index = 0

    async def _evaluate(self, test_case: TestCase, trace: Trace) -> EvalResult:
        score = self._scores[self._call_index % len(self._scores)]
        self._call_index += 1
        verdict = EvalVerdict.PASS if score >= 0.7 else EvalVerdict.FAIL
        return EvalResult(
            evaluator_name=self.name,
            verdict=verdict,
            score=score,
            reason=f"Score: {score}",
        )


class _ConstantEvaluator(BaseEvaluator):
    """Test evaluator that always returns the same score."""

    def __init__(self, score: float = 0.9) -> None:
        super().__init__("constant")
        self._score = score

    async def _evaluate(self, test_case: TestCase, trace: Trace) -> EvalResult:
        return EvalResult(
            evaluator_name=self.name,
            verdict=EvalVerdict.PASS,
            score=self._score,
            reason="constant",
        )


class TestPercentile:
    """Test the percentile helper function."""

    def test_empty_data(self) -> None:
        assert _percentile([], 50) == 0.0

    def test_single_value(self) -> None:
        assert _percentile([0.5], 50) == 0.5

    def test_median_odd(self) -> None:
        assert _percentile([0.1, 0.5, 0.9], 50) == 0.5

    def test_p5_and_p95(self) -> None:
        data = sorted([float(i) / 100 for i in range(101)])
        assert abs(_percentile(data, 5) - 0.05) < 0.01
        assert abs(_percentile(data, 95) - 0.95) < 0.01


class TestStatisticalEvaluator:
    """Test statistical evaluator with deterministic inner evaluator."""

    @pytest.fixture
    def test_case(self) -> TestCase:
        return TestCase(name="stat_test", input_text="test input")

    @pytest.fixture
    def traces(self) -> list[Trace]:
        return [make_trace(output_text=f"output_{i}") for i in range(5)]

    async def test_single_trace_delegates(self, test_case: TestCase) -> None:
        inner = _ConstantEvaluator(score=0.85)
        evaluator = StatisticalEvaluator(inner)
        trace = make_trace()
        result = await evaluator.evaluate(test_case, trace)
        assert result.score == 0.85
        assert result.verdict == EvalVerdict.PASS

    async def test_default_name(self) -> None:
        inner = _ConstantEvaluator()
        evaluator = StatisticalEvaluator(inner)
        assert evaluator.name == "statistical-constant"

    async def test_custom_name(self) -> None:
        inner = _ConstantEvaluator()
        evaluator = StatisticalEvaluator(inner, name="my-stat")
        assert evaluator.name == "my-stat"

    async def test_inner_property(self) -> None:
        inner = _ConstantEvaluator()
        evaluator = StatisticalEvaluator(inner)
        assert evaluator.inner is inner

    async def test_evaluate_multiple_constant(
        self, test_case: TestCase, traces: list[Trace]
    ) -> None:
        inner = _ConstantEvaluator(score=0.8)
        evaluator = StatisticalEvaluator(inner)
        summary = await evaluator.evaluate_multiple(test_case, traces)

        assert summary.sample_count == 5
        assert summary.mean == 0.8
        assert summary.std_dev == 0.0
        assert summary.median == 0.8
        assert len(summary.scores) == 5

    async def test_evaluate_multiple_varying(
        self, test_case: TestCase, traces: list[Trace]
    ) -> None:
        scores = [0.6, 0.7, 0.8, 0.9, 1.0]
        inner = _DeterministicEvaluator(scores)
        evaluator = StatisticalEvaluator(inner)
        summary = await evaluator.evaluate_multiple(test_case, traces)

        assert summary.sample_count == 5
        assert summary.mean == 0.8
        assert summary.std_dev > 0
        assert summary.median == 0.8
        assert summary.p5 <= summary.p95
        assert summary.ci_lower <= summary.mean <= summary.ci_upper

    async def test_evaluate_multiple_single_trace(self, test_case: TestCase) -> None:
        inner = _ConstantEvaluator(score=0.75)
        evaluator = StatisticalEvaluator(inner)
        summary = await evaluator.evaluate_multiple(test_case, [make_trace()])

        assert summary.sample_count == 1
        assert summary.mean == 0.75
        assert summary.std_dev == 0.0
        assert summary.ci_lower == summary.mean
        assert summary.ci_upper == summary.mean

    async def test_evaluate_multiple_empty_traces(self, test_case: TestCase) -> None:
        inner = _ConstantEvaluator()
        evaluator = StatisticalEvaluator(inner)
        summary = await evaluator.evaluate_multiple(test_case, [])

        assert summary.sample_count == 1
        assert summary.mean == 0.0

    async def test_summary_to_eval_result_pass(
        self, test_case: TestCase, traces: list[Trace]
    ) -> None:
        inner = _ConstantEvaluator(score=0.85)
        evaluator = StatisticalEvaluator(inner, pass_threshold=0.7)
        summary = await evaluator.evaluate_multiple(test_case, traces)
        result = evaluator.summary_to_eval_result(summary)

        assert result.verdict == EvalVerdict.PASS
        assert result.score == 0.85
        assert "mean=0.850" in result.reason

    async def test_summary_to_eval_result_partial(
        self, test_case: TestCase, traces: list[Trace]
    ) -> None:
        inner = _ConstantEvaluator(score=0.6)
        evaluator = StatisticalEvaluator(inner, pass_threshold=0.7)
        summary = await evaluator.evaluate_multiple(test_case, traces)
        result = evaluator.summary_to_eval_result(summary)

        assert result.verdict == EvalVerdict.PARTIAL

    async def test_summary_to_eval_result_fail(
        self, test_case: TestCase, traces: list[Trace]
    ) -> None:
        inner = _ConstantEvaluator(score=0.3)
        evaluator = StatisticalEvaluator(inner, pass_threshold=0.7)
        summary = await evaluator.evaluate_multiple(test_case, traces)
        result = evaluator.summary_to_eval_result(summary)

        assert result.verdict == EvalVerdict.FAIL

    async def test_summary_to_eval_result_metadata(
        self, test_case: TestCase, traces: list[Trace]
    ) -> None:
        inner = _ConstantEvaluator(score=0.9)
        evaluator = StatisticalEvaluator(inner)
        summary = await evaluator.evaluate_multiple(test_case, traces)
        result = evaluator.summary_to_eval_result(summary)

        assert "sample_count" in result.metadata
        assert result.metadata["sample_count"] == 5
        assert "std_dev" in result.metadata
        assert "median" in result.metadata
