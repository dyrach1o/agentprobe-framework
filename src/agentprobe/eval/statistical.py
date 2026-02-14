"""Statistical evaluator for repeated evaluation with aggregated metrics.

Wraps an inner evaluator and runs it multiple times across pre-collected
traces, computing mean, standard deviation, percentiles, and confidence
intervals from the score distribution.
"""

from __future__ import annotations

import logging
import math
import statistics
from collections.abc import Sequence

from agentprobe.core.models import (
    EvalResult,
    EvalVerdict,
    StatisticalSummary,
    TestCase,
    Trace,
)
from agentprobe.eval.base import BaseEvaluator

logger = logging.getLogger(__name__)


def _percentile(sorted_data: list[float], pct: float) -> float:
    """Compute a percentile from pre-sorted data using linear interpolation."""
    if not sorted_data:
        return 0.0
    n = len(sorted_data)
    if n == 1:
        return sorted_data[0]
    k = (n - 1) * (pct / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_data[int(k)]
    return sorted_data[f] * (c - k) + sorted_data[c] * (k - f)


class StatisticalEvaluator(BaseEvaluator):
    """Evaluator that runs an inner evaluator multiple times and aggregates stats.

    Wraps another evaluator and runs it against multiple traces for the same
    test case, computing distributional statistics on the resulting scores.

    Attributes:
        inner: The wrapped evaluator instance.
        pass_threshold: Minimum mean score to consider a pass.
    """

    def __init__(
        self,
        inner: BaseEvaluator,
        *,
        name: str | None = None,
        pass_threshold: float = 0.7,
    ) -> None:
        """Initialize the statistical evaluator.

        Args:
            inner: The evaluator to wrap and run repeatedly.
            name: Optional name override. Defaults to 'statistical-{inner.name}'.
            pass_threshold: Minimum mean score for a pass verdict.
        """
        resolved_name = name or f"statistical-{inner.name}"
        super().__init__(resolved_name)
        self._inner = inner
        self._pass_threshold = pass_threshold

    @property
    def inner(self) -> BaseEvaluator:
        """Return the wrapped evaluator."""
        return self._inner

    async def _evaluate(self, test_case: TestCase, trace: Trace) -> EvalResult:
        """Run the inner evaluator once (single-trace mode).

        For statistical analysis, use ``evaluate_multiple()`` instead.

        Args:
            test_case: The test case.
            trace: A single trace to evaluate.

        Returns:
            The inner evaluator's result.
        """
        return await self._inner.evaluate(test_case, trace)

    async def evaluate_multiple(
        self,
        test_case: TestCase,
        traces: Sequence[Trace],
    ) -> StatisticalSummary:
        """Evaluate multiple traces and compute aggregate statistics.

        Runs the inner evaluator on each trace, collects scores, and
        computes mean, standard deviation, median, percentiles, and
        a 95% confidence interval.

        Args:
            test_case: The test case specification.
            traces: Pre-collected traces to evaluate.

        Returns:
            A statistical summary of the score distribution.
        """
        scores: list[float] = []
        for trace in traces:
            result = await self._inner.evaluate(test_case, trace)
            scores.append(result.score)

        if not scores:
            return StatisticalSummary(
                evaluator_name=self.name,
                sample_count=1,
                scores=(0.0,),
                mean=0.0,
                std_dev=0.0,
                median=0.0,
                p5=0.0,
                p95=0.0,
                ci_lower=0.0,
                ci_upper=0.0,
            )

        n = len(scores)
        mean = statistics.mean(scores)
        std_dev = statistics.stdev(scores) if n > 1 else 0.0

        sorted_scores = sorted(scores)
        median = statistics.median(sorted_scores)
        p5 = _percentile(sorted_scores, 5)
        p95 = _percentile(sorted_scores, 95)

        # 95% confidence interval using t-distribution approximation
        if n > 1:
            se = std_dev / math.sqrt(n)
            # Approximate t-value for 95% CI (use 1.96 for large n)
            t_val = 1.96
            ci_lower = max(0.0, mean - t_val * se)
            ci_upper = min(1.0, mean + t_val * se)
        else:
            ci_lower = mean
            ci_upper = mean

        return StatisticalSummary(
            evaluator_name=self.name,
            sample_count=n,
            scores=tuple(scores),
            mean=round(mean, 6),
            std_dev=round(std_dev, 6),
            median=round(median, 6),
            p5=round(p5, 6),
            p95=round(p95, 6),
            ci_lower=round(ci_lower, 6),
            ci_upper=round(ci_upper, 6),
        )

    def summary_to_eval_result(self, summary: StatisticalSummary) -> EvalResult:
        """Convert a statistical summary into a standard EvalResult.

        Args:
            summary: The summary to convert.

        Returns:
            An EvalResult with the mean score and appropriate verdict.
        """
        _partial_threshold = 0.5
        if summary.mean >= self._pass_threshold:
            verdict = EvalVerdict.PASS
        elif summary.mean >= _partial_threshold:
            verdict = EvalVerdict.PARTIAL
        else:
            verdict = EvalVerdict.FAIL

        return EvalResult(
            evaluator_name=self.name,
            verdict=verdict,
            score=summary.mean,
            reason=(
                f"Statistical: mean={summary.mean:.3f}, "
                f"std={summary.std_dev:.3f}, n={summary.sample_count}"
            ),
            metadata={
                "std_dev": summary.std_dev,
                "median": summary.median,
                "p5": summary.p5,
                "p95": summary.p95,
                "ci_lower": summary.ci_lower,
                "ci_upper": summary.ci_upper,
                "sample_count": summary.sample_count,
            },
        )
