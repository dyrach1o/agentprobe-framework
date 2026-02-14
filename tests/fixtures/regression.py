"""Factory functions for creating regression test objects."""

from __future__ import annotations

from agentprobe.core.models import RegressionReport, TestComparison


def make_test_comparison(
    *,
    test_name: str = "test_example",
    baseline_score: float = 0.9,
    current_score: float = 0.85,
    delta: float = -0.05,
    is_regression: bool = True,
    is_improvement: bool = False,
) -> TestComparison:
    """Create a TestComparison with sensible defaults for testing."""
    return TestComparison(
        test_name=test_name,
        baseline_score=baseline_score,
        current_score=current_score,
        delta=delta,
        is_regression=is_regression,
        is_improvement=is_improvement,
    )


def make_regression_report(
    *,
    baseline_name: str = "baseline-v1",
    comparisons: list[TestComparison] | None = None,
    threshold: float = 0.05,
) -> RegressionReport:
    """Create a RegressionReport with sensible defaults for testing.

    Automatically computes aggregate counts from comparisons.
    """
    resolved = comparisons or [make_test_comparison()]
    regressions = sum(1 for c in resolved if c.is_regression)
    improvements = sum(1 for c in resolved if c.is_improvement)
    unchanged = len(resolved) - regressions - improvements
    return RegressionReport(
        baseline_name=baseline_name,
        comparisons=tuple(resolved),
        total_tests=len(resolved),
        regressions=regressions,
        improvements=improvements,
        unchanged=unchanged,
        threshold=threshold,
    )
