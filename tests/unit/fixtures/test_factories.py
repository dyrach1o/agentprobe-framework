"""Validation tests for all test factory functions.

Each test verifies that calling a factory with defaults produces a
valid Pydantic model instance (no validation errors).
"""

from __future__ import annotations

from agentprobe.core.models import (
    AgentRun,
    BudgetCheckResult,
    ChaosOverride,
    ConversationResult,
    CostBreakdown,
    CostSummary,
    DiffItem,
    EvalResult,
    LLMCall,
    MetricDefinition,
    MetricValue,
    RegressionReport,
    ReplayDiff,
    SnapshotDiff,
    StatisticalSummary,
    TestComparison,
    TestResult,
    ToolCall,
    Trace,
    TraceStep,
    Turn,
    TurnResult,
)
from agentprobe.safety.scanner import SafetyScanResult, SafetySuiteResult
from tests.fixtures.regression import make_regression_report, make_test_comparison
from tests.fixtures.results import (
    make_agent_run,
    make_assertion_result,
    make_budget_check_result,
    make_cost_breakdown,
    make_cost_summary,
    make_eval_result,
    make_test_result,
)
from tests.fixtures.safety import make_safety_scan_result, make_safety_suite_result
from tests.fixtures.traces import (
    make_chaos_override,
    make_conversation_result,
    make_diff_item,
    make_llm_call,
    make_metric_definition,
    make_metric_value,
    make_replay_diff,
    make_snapshot_diff,
    make_statistical_summary,
    make_tool_call,
    make_trace,
    make_trace_step,
    make_turn,
    make_turn_result,
)


class TestTraceFactories:
    """Verify trace-related factories produce valid models."""

    def test_make_llm_call(self) -> None:
        obj = make_llm_call()
        assert isinstance(obj, LLMCall)

    def test_make_tool_call(self) -> None:
        obj = make_tool_call()
        assert isinstance(obj, ToolCall)

    def test_make_turn(self) -> None:
        obj = make_turn()
        assert isinstance(obj, Turn)

    def test_make_trace(self) -> None:
        obj = make_trace()
        assert isinstance(obj, Trace)

    def test_make_trace_with_calls(self) -> None:
        obj = make_trace(llm_calls=[make_llm_call()], tool_calls=[make_tool_call()])
        assert obj.total_input_tokens == 100
        assert obj.total_output_tokens == 50

    def test_make_turn_result(self) -> None:
        obj = make_turn_result()
        assert isinstance(obj, TurnResult)

    def test_make_conversation_result(self) -> None:
        obj = make_conversation_result()
        assert isinstance(obj, ConversationResult)

    def test_make_statistical_summary(self) -> None:
        obj = make_statistical_summary()
        assert isinstance(obj, StatisticalSummary)

    def test_make_metric_definition(self) -> None:
        obj = make_metric_definition()
        assert isinstance(obj, MetricDefinition)

    def test_make_metric_value(self) -> None:
        obj = make_metric_value()
        assert isinstance(obj, MetricValue)

    def test_make_diff_item(self) -> None:
        obj = make_diff_item()
        assert isinstance(obj, DiffItem)

    def test_make_snapshot_diff(self) -> None:
        obj = make_snapshot_diff()
        assert isinstance(obj, SnapshotDiff)

    def test_make_trace_step(self) -> None:
        obj = make_trace_step()
        assert isinstance(obj, TraceStep)

    def test_make_replay_diff(self) -> None:
        obj = make_replay_diff()
        assert isinstance(obj, ReplayDiff)

    def test_make_chaos_override(self) -> None:
        obj = make_chaos_override()
        assert isinstance(obj, ChaosOverride)


class TestResultFactories:
    """Verify result-related factories produce valid models."""

    def test_make_eval_result(self) -> None:
        obj = make_eval_result()
        assert isinstance(obj, EvalResult)

    def test_make_assertion_result(self) -> None:
        obj = make_assertion_result()
        assert obj.passed is True

    def test_make_test_result(self) -> None:
        obj = make_test_result()
        assert isinstance(obj, TestResult)

    def test_make_test_result_with_id(self) -> None:
        obj = make_test_result(result_id="custom-id")
        assert obj.result_id == "custom-id"

    def test_make_cost_breakdown(self) -> None:
        obj = make_cost_breakdown()
        assert isinstance(obj, CostBreakdown)

    def test_make_cost_summary(self) -> None:
        obj = make_cost_summary()
        assert isinstance(obj, CostSummary)

    def test_make_budget_check_result(self) -> None:
        obj = make_budget_check_result()
        assert isinstance(obj, BudgetCheckResult)
        assert obj.within_budget is True

    def test_make_agent_run(self) -> None:
        obj = make_agent_run()
        assert isinstance(obj, AgentRun)

    def test_make_agent_run_with_results(self) -> None:
        from agentprobe.core.models import TestStatus

        results = [make_test_result(), make_test_result(status=TestStatus.FAILED, score=0.0)]
        obj = make_agent_run(test_results=results)
        assert obj.total_tests == 2
        assert obj.passed == 1
        assert obj.failed == 1


class TestSafetyFactories:
    """Verify safety-related factories produce valid models."""

    def test_make_safety_suite_result(self) -> None:
        obj = make_safety_suite_result()
        assert isinstance(obj, SafetySuiteResult)

    def test_make_safety_scan_result(self) -> None:
        obj = make_safety_scan_result()
        assert isinstance(obj, SafetyScanResult)
        assert obj.total_suites == 1

    def test_make_safety_scan_result_multiple_suites(self) -> None:
        suites = [
            make_safety_suite_result(suite_name="injection"),
            make_safety_suite_result(suite_name="leakage", passed=10, failed=0),
        ]
        obj = make_safety_scan_result(suite_results=suites)
        assert obj.total_suites == 2
        assert obj.total_passed == 18


class TestRegressionFactories:
    """Verify regression-related factories produce valid models."""

    def test_make_test_comparison(self) -> None:
        obj = make_test_comparison()
        assert isinstance(obj, TestComparison)
        assert obj.is_regression is True

    def test_make_regression_report(self) -> None:
        obj = make_regression_report()
        assert isinstance(obj, RegressionReport)
        assert obj.regressions == 1

    def test_make_regression_report_mixed(self) -> None:
        comparisons = [
            make_test_comparison(is_regression=True, is_improvement=False),
            make_test_comparison(
                test_name="test_b",
                baseline_score=0.7,
                current_score=0.9,
                delta=0.2,
                is_regression=False,
                is_improvement=True,
            ),
            make_test_comparison(
                test_name="test_c",
                baseline_score=0.8,
                current_score=0.8,
                delta=0.0,
                is_regression=False,
                is_improvement=False,
            ),
        ]
        obj = make_regression_report(comparisons=comparisons)
        assert obj.regressions == 1
        assert obj.improvements == 1
        assert obj.unchanged == 1
