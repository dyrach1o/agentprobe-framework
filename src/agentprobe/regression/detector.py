"""Regression detection by comparing baseline and current test results.

Flags regressions (score decreases) and improvements (score increases)
based on configurable delta thresholds.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence

from agentprobe.core.models import (
    RegressionReport,
    TestComparison,
    TestResult,
)

logger = logging.getLogger(__name__)


class RegressionDetector:
    """Compares current test results against a baseline to detect regressions.

    Attributes:
        threshold: Minimum score delta to flag as regression/improvement.
    """

    def __init__(self, threshold: float = 0.05) -> None:
        """Initialize the regression detector.

        Args:
            threshold: Score delta threshold for flagging changes.
        """
        self._threshold = threshold

    def compare(
        self,
        baseline_name: str,
        baseline_results: Sequence[TestResult],
        current_results: Sequence[TestResult],
    ) -> RegressionReport:
        """Compare current results against a baseline.

        Tests are matched by name. Tests present in only one set are
        excluded from comparison.

        Args:
            baseline_name: Name of the baseline for reporting.
            baseline_results: Test results from the baseline run.
            current_results: Test results from the current run.

        Returns:
            A RegressionReport with per-test comparisons.
        """
        baseline_map = {r.test_name: r for r in baseline_results}
        current_map = {r.test_name: r for r in current_results}

        common_names = sorted(set(baseline_map) & set(current_map))
        comparisons: list[TestComparison] = []
        regressions = 0
        improvements = 0
        unchanged = 0

        for name in common_names:
            bl = baseline_map[name]
            cr = current_map[name]
            delta = round(cr.score - bl.score, 6)

            is_regression = delta < -self._threshold
            is_improvement = delta > self._threshold

            if is_regression:
                regressions += 1
                logger.warning(
                    "Regression detected: %s (%.3f -> %.3f, delta=%.3f)",
                    name,
                    bl.score,
                    cr.score,
                    delta,
                )
            elif is_improvement:
                improvements += 1
                logger.info(
                    "Improvement detected: %s (%.3f -> %.3f, delta=%.3f)",
                    name,
                    bl.score,
                    cr.score,
                    delta,
                )
            else:
                unchanged += 1

            comparisons.append(
                TestComparison(
                    test_name=name,
                    baseline_score=bl.score,
                    current_score=cr.score,
                    delta=delta,
                    is_regression=is_regression,
                    is_improvement=is_improvement,
                )
            )

        return RegressionReport(
            baseline_name=baseline_name,
            comparisons=tuple(comparisons),
            total_tests=len(comparisons),
            regressions=regressions,
            improvements=improvements,
            unchanged=unchanged,
            threshold=self._threshold,
        )
