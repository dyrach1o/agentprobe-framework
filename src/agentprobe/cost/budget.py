"""Budget enforcement for test execution cost management.

Provides the BudgetEnforcer class for checking individual test
and suite-level costs against configured budget limits.
"""

from __future__ import annotations

import logging

from agentprobe.core.models import BudgetCheckResult, CostSummary

logger = logging.getLogger(__name__)


class BudgetEnforcer:
    """Enforces cost budgets for tests and suites.

    Checks actual costs against configured limits and returns
    verdict objects indicating whether budgets were exceeded.

    Attributes:
        test_budget_usd: Maximum cost per individual test.
        suite_budget_usd: Maximum cost per test suite run.
    """

    def __init__(
        self,
        *,
        test_budget_usd: float | None = None,
        suite_budget_usd: float | None = None,
    ) -> None:
        """Initialize the budget enforcer.

        Args:
            test_budget_usd: Maximum cost per test in USD.
            suite_budget_usd: Maximum cost per suite in USD.
        """
        self._test_budget = test_budget_usd
        self._suite_budget = suite_budget_usd

    @staticmethod
    def _check(actual: float, limit: float) -> BudgetCheckResult:
        """Compare actual cost against a budget limit.

        Args:
            actual: Actual cost in USD.
            limit: Budget limit in USD.

        Returns:
            A BudgetCheckResult with within_budget verdict.
        """
        remaining = limit - actual
        utilization = (actual / limit * 100.0) if limit > 0 else 0.0
        within = actual <= limit
        return BudgetCheckResult(
            within_budget=within,
            actual_cost_usd=actual,
            budget_limit_usd=limit,
            remaining_usd=remaining,
            utilization_pct=round(utilization, 2),
        )

    def check_test(self, cost_summary: CostSummary) -> BudgetCheckResult | None:
        """Check a single test's cost against the test budget.

        Args:
            cost_summary: Cost summary for the test.

        Returns:
            A BudgetCheckResult if a test budget is configured, else None.
        """
        if self._test_budget is None:
            return None
        result = self._check(cost_summary.total_cost_usd, self._test_budget)
        if not result.within_budget:
            logger.warning(
                "Test budget exceeded: $%.4f > $%.4f limit",
                cost_summary.total_cost_usd,
                self._test_budget,
            )
        return result

    def check_suite(self, cost_summaries: list[CostSummary]) -> BudgetCheckResult | None:
        """Check a suite's total cost against the suite budget.

        Args:
            cost_summaries: Cost summaries for all tests in the suite.

        Returns:
            A BudgetCheckResult if a suite budget is configured, else None.
        """
        if self._suite_budget is None:
            return None
        total = sum(cs.total_cost_usd for cs in cost_summaries)
        result = self._check(total, self._suite_budget)
        if not result.within_budget:
            logger.warning(
                "Suite budget exceeded: $%.4f > $%.4f limit",
                total,
                self._suite_budget,
            )
        return result
