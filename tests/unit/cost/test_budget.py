"""Tests for the budget enforcer."""

from __future__ import annotations

from agentprobe.core.models import CostSummary
from agentprobe.cost.budget import BudgetEnforcer


class TestBudgetEnforcer:
    """Test BudgetEnforcer check methods."""

    def _make_cost_summary(self, total: float) -> CostSummary:
        return CostSummary(
            total_llm_cost_usd=total,
            total_tool_cost_usd=0.0,
            total_cost_usd=total,
        )

    def test_check_test_within_budget(self) -> None:
        enforcer = BudgetEnforcer(test_budget_usd=1.0)
        result = enforcer.check_test(self._make_cost_summary(0.50))
        assert result is not None
        assert result.within_budget is True
        assert result.remaining_usd == 0.50
        assert result.utilization_pct == 50.0

    def test_check_test_at_exact_limit(self) -> None:
        enforcer = BudgetEnforcer(test_budget_usd=1.0)
        result = enforcer.check_test(self._make_cost_summary(1.0))
        assert result is not None
        assert result.within_budget is True
        assert result.remaining_usd == 0.0
        assert result.utilization_pct == 100.0

    def test_check_test_exceeded(self) -> None:
        enforcer = BudgetEnforcer(test_budget_usd=0.50)
        result = enforcer.check_test(self._make_cost_summary(0.75))
        assert result is not None
        assert result.within_budget is False
        assert result.remaining_usd == -0.25
        assert result.utilization_pct == 150.0

    def test_check_test_no_budget(self) -> None:
        enforcer = BudgetEnforcer()
        result = enforcer.check_test(self._make_cost_summary(10.0))
        assert result is None

    def test_check_suite_within_budget(self) -> None:
        enforcer = BudgetEnforcer(suite_budget_usd=5.0)
        summaries = [self._make_cost_summary(1.0) for _ in range(3)]
        result = enforcer.check_suite(summaries)
        assert result is not None
        assert result.within_budget is True
        assert result.actual_cost_usd == 3.0
        assert result.remaining_usd == 2.0

    def test_check_suite_exceeded(self) -> None:
        enforcer = BudgetEnforcer(suite_budget_usd=2.0)
        summaries = [self._make_cost_summary(1.0) for _ in range(3)]
        result = enforcer.check_suite(summaries)
        assert result is not None
        assert result.within_budget is False
        assert result.actual_cost_usd == 3.0

    def test_check_suite_no_budget(self) -> None:
        enforcer = BudgetEnforcer()
        summaries = [self._make_cost_summary(100.0)]
        result = enforcer.check_suite(summaries)
        assert result is None

    def test_check_suite_empty(self) -> None:
        enforcer = BudgetEnforcer(suite_budget_usd=5.0)
        result = enforcer.check_suite([])
        assert result is not None
        assert result.within_budget is True
        assert result.actual_cost_usd == 0.0

    def test_zero_budget_limit(self) -> None:
        enforcer = BudgetEnforcer(test_budget_usd=0.0)
        result = enforcer.check_test(self._make_cost_summary(0.0))
        assert result is not None
        assert result.within_budget is True
        assert result.utilization_pct == 0.0

    def test_both_budgets_configured(self) -> None:
        enforcer = BudgetEnforcer(test_budget_usd=1.0, suite_budget_usd=3.0)
        summary = self._make_cost_summary(0.5)
        test_result = enforcer.check_test(summary)
        suite_result = enforcer.check_suite([summary, summary])
        assert test_result is not None
        assert test_result.within_budget is True
        assert suite_result is not None
        assert suite_result.within_budget is True
        assert suite_result.actual_cost_usd == 1.0
