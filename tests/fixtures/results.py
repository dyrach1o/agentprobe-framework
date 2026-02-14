"""Factory functions for creating test results and evaluation results."""

from __future__ import annotations

from typing import Any

from agentprobe.core.models import (
    AgentRun,
    AssertionResult,
    BudgetCheckResult,
    CostBreakdown,
    CostSummary,
    EvalResult,
    EvalVerdict,
    RunStatus,
    TestResult,
    TestStatus,
    Trace,
)


def make_eval_result(
    *,
    evaluator_name: str = "test-evaluator",
    verdict: EvalVerdict = EvalVerdict.PASS,
    score: float = 1.0,
    reason: str = "Test evaluation passed",
    metadata: dict[str, Any] | None = None,
) -> EvalResult:
    """Create an EvalResult with sensible defaults for testing."""
    return EvalResult(
        evaluator_name=evaluator_name,
        verdict=verdict,
        score=score,
        reason=reason,
        metadata=metadata or {},
    )


def make_assertion_result(
    *,
    assertion_type: str = "contain",
    passed: bool = True,
    expected: Any = "expected",
    actual: Any = "actual",
    message: str = "",
) -> AssertionResult:
    """Create an AssertionResult with sensible defaults for testing."""
    return AssertionResult(
        assertion_type=assertion_type,
        passed=passed,
        expected=expected,
        actual=actual,
        message=message,
    )


def make_test_result(
    *,
    test_name: str = "test_example",
    status: TestStatus = TestStatus.PASSED,
    score: float = 1.0,
    duration_ms: int = 150,
    trace: Trace | None = None,
    eval_results: list[EvalResult] | None = None,
    assertion_results: list[AssertionResult] | None = None,
    error_message: str | None = None,
    result_id: str | None = None,
) -> TestResult:
    """Create a TestResult with sensible defaults for testing."""
    kwargs: dict[str, Any] = {
        "test_name": test_name,
        "status": status,
        "score": score,
        "duration_ms": duration_ms,
        "trace": trace,
        "eval_results": tuple(eval_results or []),
        "assertion_results": tuple(assertion_results or []),
        "error_message": error_message,
    }
    if result_id is not None:
        kwargs["result_id"] = result_id
    return TestResult(**kwargs)


def make_cost_breakdown(
    *,
    model: str = "test-model",
    input_tokens: int = 1000,
    output_tokens: int = 500,
    input_cost_usd: float = 0.003,
    output_cost_usd: float = 0.0075,
    total_cost_usd: float = 0.0105,
    call_count: int = 1,
) -> CostBreakdown:
    """Create a CostBreakdown with sensible defaults for testing."""
    return CostBreakdown(
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        input_cost_usd=input_cost_usd,
        output_cost_usd=output_cost_usd,
        total_cost_usd=total_cost_usd,
        call_count=call_count,
    )


def make_cost_summary(
    *,
    total_llm_cost_usd: float = 0.0105,
    total_tool_cost_usd: float = 0.0,
    total_cost_usd: float = 0.0105,
    breakdown_by_model: dict[str, CostBreakdown] | None = None,
    total_input_tokens: int = 1000,
    total_output_tokens: int = 500,
) -> CostSummary:
    """Create a CostSummary with sensible defaults for testing."""
    return CostSummary(
        total_llm_cost_usd=total_llm_cost_usd,
        total_tool_cost_usd=total_tool_cost_usd,
        total_cost_usd=total_cost_usd,
        breakdown_by_model=breakdown_by_model or {},
        total_input_tokens=total_input_tokens,
        total_output_tokens=total_output_tokens,
    )


def make_budget_check_result(
    *,
    within_budget: bool = True,
    actual_cost_usd: float = 5.0,
    budget_limit_usd: float = 10.0,
    remaining_usd: float = 5.0,
    utilization_pct: float = 50.0,
) -> BudgetCheckResult:
    """Create a BudgetCheckResult with sensible defaults for testing."""
    return BudgetCheckResult(
        within_budget=within_budget,
        actual_cost_usd=actual_cost_usd,
        budget_limit_usd=budget_limit_usd,
        remaining_usd=remaining_usd,
        utilization_pct=utilization_pct,
    )


def make_agent_run(
    *,
    agent_name: str = "test-agent",
    status: RunStatus = RunStatus.COMPLETED,
    test_results: list[TestResult] | None = None,
    cost_summary: CostSummary | None = None,
    duration_ms: int = 5000,
    tags: list[str] | None = None,
) -> AgentRun:
    """Create an AgentRun with sensible defaults for testing.

    Automatically computes pass/fail/error/skip counts from results.
    """
    resolved_results = test_results or []
    passed = sum(1 for r in resolved_results if r.status == TestStatus.PASSED)
    failed = sum(1 for r in resolved_results if r.status == TestStatus.FAILED)
    errors = sum(1 for r in resolved_results if r.status == TestStatus.ERROR)
    skipped = sum(1 for r in resolved_results if r.status == TestStatus.SKIPPED)
    return AgentRun(
        agent_name=agent_name,
        status=status,
        test_results=tuple(resolved_results),
        total_tests=len(resolved_results),
        passed=passed,
        failed=failed,
        errors=errors,
        skipped=skipped,
        cost_summary=cost_summary,
        duration_ms=duration_ms,
        tags=tuple(tags or []),
    )
