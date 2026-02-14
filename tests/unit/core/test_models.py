"""Tests for the core Pydantic models."""

import pytest
from pydantic import ValidationError

from agentprobe.core.models import (
    AgentRun,
    AssertionResult,
    BudgetCheckResult,
    ChaosOverride,
    ChaosType,
    ConversationResult,
    ConversationTurn,
    CostBreakdown,
    CostSummary,
    DiffItem,
    EvalResult,
    EvalVerdict,
    LLMCall,
    MetricAggregation,
    MetricDefinition,
    MetricType,
    MetricValue,
    PluginType,
    RegressionReport,
    ReplayDiff,
    RunStatus,
    SnapshotDiff,
    StatisticalSummary,
    TestCase,
    TestComparison,
    TestStatus,
    ToolCall,
    Trace,
    TraceStep,
    TrendDirection,
    TurnResult,
    TurnType,
)
from tests.fixtures.results import make_eval_result, make_test_result
from tests.fixtures.traces import (
    make_conversation_result,
    make_llm_call,
    make_metric_definition,
    make_metric_value,
    make_statistical_summary,
    make_tool_call,
    make_trace,
    make_turn,
    make_turn_result,
)


class TestEnums:
    """Test enum values and string representation."""

    def test_test_status_values(self) -> None:
        assert TestStatus.PENDING == "pending"
        assert TestStatus.PASSED == "passed"
        assert TestStatus.FAILED == "failed"
        assert TestStatus.ERROR == "error"

    def test_run_status_values(self) -> None:
        assert RunStatus.COMPLETED == "completed"
        assert RunStatus.FAILED == "failed"

    def test_turn_type_values(self) -> None:
        assert TurnType.LLM_CALL == "llm_call"
        assert TurnType.TOOL_CALL == "tool_call"

    def test_eval_verdict_values(self) -> None:
        assert EvalVerdict.PASS == "pass"
        assert EvalVerdict.FAIL == "fail"
        assert EvalVerdict.PARTIAL == "partial"


class TestLLMCall:
    """Test LLMCall model construction and constraints."""

    def test_construction_with_defaults(self) -> None:
        call = LLMCall(model="test-model")
        assert call.model == "test-model"
        assert call.input_tokens == 0
        assert call.output_tokens == 0
        assert call.call_id  # auto-generated UUID
        assert call.timestamp.tzinfo is not None

    def test_construction_full(self) -> None:
        call = make_llm_call(
            model="claude-sonnet-4-5-20250929", input_tokens=500, output_tokens=200
        )
        assert call.model == "claude-sonnet-4-5-20250929"
        assert call.input_tokens == 500
        assert call.output_tokens == 200

    def test_negative_tokens_rejected(self) -> None:
        with pytest.raises(ValidationError, match="greater than or equal to 0"):
            LLMCall(model="test", input_tokens=-1)

    def test_frozen(self) -> None:
        call = make_llm_call()
        with pytest.raises(ValidationError):
            call.model = "changed"  # type: ignore[misc]

    def test_extra_fields_rejected(self) -> None:
        with pytest.raises(ValidationError, match="extra"):
            LLMCall(model="test", bogus_field="nope")  # type: ignore[call-arg]

    def test_serialization_roundtrip(self) -> None:
        call = make_llm_call(model="gpt-4o", input_tokens=42)
        json_str = call.model_dump_json()
        restored = LLMCall.model_validate_json(json_str)
        assert restored.model == "gpt-4o"
        assert restored.input_tokens == 42


class TestToolCall:
    """Test ToolCall model construction and constraints."""

    def test_construction_with_defaults(self) -> None:
        call = ToolCall(tool_name="search")
        assert call.tool_name == "search"
        assert call.success is True
        assert call.error is None

    def test_failed_tool_call(self) -> None:
        call = make_tool_call(success=False, error="timeout")
        assert call.success is False
        assert call.error == "timeout"

    def test_frozen(self) -> None:
        call = make_tool_call()
        with pytest.raises(ValidationError):
            call.tool_name = "changed"  # type: ignore[misc]


class TestTurn:
    """Test Turn model construction."""

    def test_llm_turn(self) -> None:
        llm = make_llm_call()
        turn = make_turn(turn_type=TurnType.LLM_CALL, llm_call=llm)
        assert turn.turn_type == TurnType.LLM_CALL
        assert turn.llm_call is not None
        assert turn.tool_call is None

    def test_tool_turn(self) -> None:
        tc = make_tool_call()
        turn = make_turn(turn_type=TurnType.TOOL_CALL, tool_call=tc)
        assert turn.turn_type == TurnType.TOOL_CALL
        assert turn.tool_call is not None


class TestTrace:
    """Test Trace model construction and constraints."""

    def test_minimal_trace(self) -> None:
        trace = Trace(agent_name="agent1")
        assert trace.agent_name == "agent1"
        assert trace.llm_calls == ()
        assert trace.tool_calls == ()
        assert trace.trace_id

    def test_full_trace(self) -> None:
        calls = [make_llm_call(input_tokens=100, output_tokens=50)]
        trace = make_trace(llm_calls=calls, tags=["integration"])
        assert len(trace.llm_calls) == 1
        assert trace.total_input_tokens == 100
        assert trace.total_output_tokens == 50
        assert "integration" in trace.tags

    def test_frozen(self) -> None:
        trace = make_trace()
        with pytest.raises(ValidationError):
            trace.agent_name = "changed"  # type: ignore[misc]

    def test_serialization_roundtrip(self) -> None:
        trace = make_trace(
            llm_calls=[make_llm_call()],
            tool_calls=[make_tool_call()],
        )
        json_str = trace.model_dump_json()
        restored = Trace.model_validate_json(json_str)
        assert restored.agent_name == trace.agent_name
        assert len(restored.llm_calls) == 1
        assert len(restored.tool_calls) == 1


class TestEvalResult:
    """Test EvalResult model."""

    def test_construction(self) -> None:
        result = make_eval_result(score=0.85, verdict=EvalVerdict.PASS)
        assert result.score == 0.85
        assert result.verdict == EvalVerdict.PASS

    def test_score_bounds(self) -> None:
        with pytest.raises(ValidationError, match="greater than or equal to 0"):
            EvalResult(evaluator_name="x", verdict=EvalVerdict.FAIL, score=-0.1)

        with pytest.raises(ValidationError, match="less than or equal to 1"):
            EvalResult(evaluator_name="x", verdict=EvalVerdict.PASS, score=1.1)

    def test_frozen(self) -> None:
        result = make_eval_result()
        with pytest.raises(ValidationError):
            result.score = 0.5  # type: ignore[misc]


class TestAssertionResult:
    """Test AssertionResult model."""

    def test_construction(self) -> None:
        result = AssertionResult(
            assertion_type="contain",
            passed=True,
            expected="hello",
            actual="hello world",
        )
        assert result.passed is True
        assert result.assertion_type == "contain"


class TestTestCase:
    """Test TestCase model (mutable)."""

    def test_construction(self) -> None:
        tc = TestCase(name="test_greeting", input_text="Hello")
        assert tc.name == "test_greeting"
        assert tc.timeout_seconds == 30.0

    def test_mutable(self) -> None:
        tc = TestCase(name="test_one")
        tc.description = "Updated description"
        assert tc.description == "Updated description"

    def test_name_validation_valid(self) -> None:
        tc = TestCase(name="test_foo-bar.baz 123")
        assert tc.name == "test_foo-bar.baz 123"

    def test_name_validation_invalid(self) -> None:
        with pytest.raises(ValidationError, match="alphanumeric"):
            TestCase(name="test@#$%")

    def test_name_min_length(self) -> None:
        with pytest.raises(ValidationError, match="at least 1"):
            TestCase(name="")

    def test_timeout_must_be_positive(self) -> None:
        with pytest.raises(ValidationError, match="greater than 0"):
            TestCase(name="test", timeout_seconds=0)


class TestTestResult:
    """Test TestResult model."""

    def test_construction(self) -> None:
        result = make_test_result(status=TestStatus.PASSED, score=0.95)
        assert result.status == TestStatus.PASSED
        assert result.score == 0.95

    def test_with_trace(self) -> None:
        trace = make_trace()
        result = make_test_result(trace=trace)
        assert result.trace is not None
        assert result.trace.agent_name == "test-agent"

    def test_with_eval_results(self) -> None:
        evals = [make_eval_result(), make_eval_result(verdict=EvalVerdict.FAIL, score=0.2)]
        result = make_test_result(eval_results=evals)
        assert len(result.eval_results) == 2

    def test_frozen(self) -> None:
        result = make_test_result()
        with pytest.raises(ValidationError):
            result.status = TestStatus.FAILED  # type: ignore[misc]


class TestCostModels:
    """Test CostBreakdown and CostSummary models."""

    def test_cost_breakdown(self) -> None:
        bd = CostBreakdown(
            model="claude-sonnet-4-5-20250929",
            input_tokens=1000,
            output_tokens=500,
            input_cost_usd=0.003,
            output_cost_usd=0.0075,
            total_cost_usd=0.0105,
            call_count=1,
        )
        assert bd.total_cost_usd == 0.0105

    def test_cost_summary(self) -> None:
        summary = CostSummary(
            total_llm_cost_usd=0.05,
            total_tool_cost_usd=0.01,
            total_cost_usd=0.06,
            total_input_tokens=5000,
            total_output_tokens=2500,
        )
        assert summary.total_cost_usd == 0.06


class TestAgentRun:
    """Test AgentRun model."""

    def test_construction(self) -> None:
        run = AgentRun(
            agent_name="support-agent",
            status=RunStatus.COMPLETED,
            total_tests=5,
            passed=4,
            failed=1,
        )
        assert run.agent_name == "support-agent"
        assert run.total_tests == 5
        assert run.passed == 4

    def test_with_results(self) -> None:
        results = [make_test_result(), make_test_result(test_name="test_two")]
        run = AgentRun(
            agent_name="agent",
            status=RunStatus.COMPLETED,
            test_results=tuple(results),
            total_tests=2,
            passed=2,
        )
        assert len(run.test_results) == 2

    def test_frozen(self) -> None:
        run = AgentRun(agent_name="x", status=RunStatus.PENDING)
        with pytest.raises(ValidationError):
            run.agent_name = "y"  # type: ignore[misc]


class TestChaosType:
    """Test ChaosType enum values."""

    def test_all_values(self) -> None:
        assert ChaosType.TIMEOUT == "timeout"
        assert ChaosType.ERROR == "error"
        assert ChaosType.MALFORMED == "malformed"
        assert ChaosType.RATE_LIMIT == "rate_limit"
        assert ChaosType.SLOW == "slow"
        assert ChaosType.EMPTY == "empty"

    def test_is_str_enum(self) -> None:
        assert isinstance(ChaosType.TIMEOUT, str)


class TestConversationTurn:
    """Test ConversationTurn model."""

    def test_construction(self) -> None:
        turn = ConversationTurn(input_text="Hello there")
        assert turn.input_text == "Hello there"
        assert turn.expected_output is None
        assert turn.evaluators == ()
        assert turn.turn_id

    def test_with_evaluators(self) -> None:
        turn = ConversationTurn(
            input_text="test",
            expected_output="response",
            evaluators=("rules", "judge"),
        )
        assert turn.expected_output == "response"
        assert len(turn.evaluators) == 2

    def test_frozen(self) -> None:
        turn = ConversationTurn(input_text="test")
        with pytest.raises(ValidationError):
            turn.input_text = "changed"  # type: ignore[misc]


class TestTurnResult:
    """Test TurnResult model."""

    def test_construction(self) -> None:
        result = make_turn_result()
        assert result.turn_index == 0
        assert result.input_text == "test turn input"
        assert result.duration_ms == 100

    def test_with_trace_and_evals(self) -> None:
        trace = make_trace()
        evals = [make_eval_result(score=0.9)]
        result = make_turn_result(
            turn_index=2,
            trace=trace,
            eval_results=evals,
        )
        assert result.turn_index == 2
        assert result.trace is not None
        assert len(result.eval_results) == 1

    def test_frozen(self) -> None:
        result = make_turn_result()
        with pytest.raises(ValidationError):
            result.turn_index = 5  # type: ignore[misc]

    def test_negative_index_rejected(self) -> None:
        with pytest.raises(ValidationError, match="greater than or equal to 0"):
            TurnResult(turn_index=-1)


class TestConversationResult:
    """Test ConversationResult model."""

    def test_construction(self) -> None:
        result = make_conversation_result()
        assert result.agent_name == "test-agent"
        assert result.total_turns == 0
        assert result.aggregate_score == 0.8

    def test_with_turns(self) -> None:
        turns = [make_turn_result(turn_index=0), make_turn_result(turn_index=1)]
        result = make_conversation_result(turn_results=turns, total_turns=2)
        assert result.total_turns == 2
        assert len(result.turn_results) == 2

    def test_frozen(self) -> None:
        result = make_conversation_result()
        with pytest.raises(ValidationError):
            result.agent_name = "changed"  # type: ignore[misc]

    def test_serialization_roundtrip(self) -> None:
        result = make_conversation_result(turn_results=[make_turn_result()], total_turns=1)
        json_str = result.model_dump_json()
        restored = ConversationResult.model_validate_json(json_str)
        assert restored.total_turns == 1
        assert restored.agent_name == "test-agent"


class TestStatisticalSummary:
    """Test StatisticalSummary model."""

    def test_construction(self) -> None:
        summary = make_statistical_summary()
        assert summary.evaluator_name == "test-evaluator"
        assert summary.sample_count == 5
        assert len(summary.scores) == 5
        assert summary.mean == 0.836

    def test_min_sample_count(self) -> None:
        with pytest.raises(ValidationError, match="greater than or equal to 1"):
            StatisticalSummary(evaluator_name="x", sample_count=0)

    def test_frozen(self) -> None:
        summary = make_statistical_summary()
        with pytest.raises(ValidationError):
            summary.mean = 0.5  # type: ignore[misc]

    def test_serialization_roundtrip(self) -> None:
        summary = make_statistical_summary()
        json_str = summary.model_dump_json()
        restored = StatisticalSummary.model_validate_json(json_str)
        assert restored.scores == summary.scores
        assert restored.mean == summary.mean


class TestTestComparison:
    """Test TestComparison model."""

    def test_no_change(self) -> None:
        comp = TestComparison(
            test_name="test_a",
            baseline_score=0.8,
            current_score=0.8,
            delta=0.0,
        )
        assert not comp.is_regression
        assert not comp.is_improvement

    def test_regression(self) -> None:
        comp = TestComparison(
            test_name="test_b",
            baseline_score=0.9,
            current_score=0.7,
            delta=-0.2,
            is_regression=True,
        )
        assert comp.is_regression
        assert comp.delta == -0.2

    def test_improvement(self) -> None:
        comp = TestComparison(
            test_name="test_c",
            baseline_score=0.6,
            current_score=0.9,
            delta=0.3,
            is_improvement=True,
        )
        assert comp.is_improvement
        assert comp.delta == 0.3


class TestRegressionReport:
    """Test RegressionReport model."""

    def test_empty_report(self) -> None:
        report = RegressionReport(baseline_name="v1.0")
        assert report.total_tests == 0
        assert report.regressions == 0

    def test_with_comparisons(self) -> None:
        comparisons = (
            TestComparison(
                test_name="t1",
                baseline_score=0.8,
                current_score=0.6,
                delta=-0.2,
                is_regression=True,
            ),
            TestComparison(
                test_name="t2",
                baseline_score=0.7,
                current_score=0.9,
                delta=0.2,
                is_improvement=True,
            ),
        )
        report = RegressionReport(
            baseline_name="v1.0",
            comparisons=comparisons,
            total_tests=2,
            regressions=1,
            improvements=1,
        )
        assert report.total_tests == 2
        assert report.regressions == 1
        assert report.improvements == 1

    def test_frozen(self) -> None:
        report = RegressionReport(baseline_name="v1")
        with pytest.raises(ValidationError):
            report.baseline_name = "v2"  # type: ignore[misc]


class TestBudgetCheckResult:
    """Test BudgetCheckResult model."""

    def test_within_budget(self) -> None:
        result = BudgetCheckResult(
            within_budget=True,
            actual_cost_usd=0.05,
            budget_limit_usd=0.10,
            remaining_usd=0.05,
            utilization_pct=50.0,
        )
        assert result.within_budget
        assert result.remaining_usd == 0.05

    def test_exceeded_budget(self) -> None:
        result = BudgetCheckResult(
            within_budget=False,
            actual_cost_usd=0.15,
            budget_limit_usd=0.10,
            remaining_usd=-0.05,
            utilization_pct=150.0,
        )
        assert not result.within_budget
        assert result.remaining_usd == -0.05


class TestDiffItem:
    """Test DiffItem model."""

    def test_construction(self) -> None:
        item = DiffItem(
            dimension="tool_calls",
            expected=["search", "calc"],
            actual=["search"],
            similarity=0.5,
        )
        assert item.dimension == "tool_calls"
        assert item.similarity == 0.5


class TestSnapshotDiff:
    """Test SnapshotDiff model."""

    def test_match(self) -> None:
        diff = SnapshotDiff(
            snapshot_name="golden-test",
            overall_similarity=0.95,
            is_match=True,
        )
        assert diff.is_match
        assert diff.overall_similarity == 0.95

    def test_no_match(self) -> None:
        items = (DiffItem(dimension="output", similarity=0.3),)
        diff = SnapshotDiff(
            snapshot_name="golden-test",
            overall_similarity=0.3,
            diffs=items,
            is_match=False,
        )
        assert not diff.is_match
        assert len(diff.diffs) == 1


class TestTraceStep:
    """Test TraceStep model."""

    def test_construction(self) -> None:
        turn = make_turn()
        step = TraceStep(
            step_index=0,
            turn=turn,
            cumulative_input_tokens=100,
            cumulative_output_tokens=50,
        )
        assert step.step_index == 0
        assert step.cumulative_input_tokens == 100

    def test_negative_index_rejected(self) -> None:
        turn = make_turn()
        with pytest.raises(ValidationError, match="greater than or equal to 0"):
            TraceStep(step_index=-1, turn=turn)


class TestReplayDiff:
    """Test ReplayDiff model."""

    def test_matching(self) -> None:
        diff = ReplayDiff(
            original_trace_id="abc",
            replay_trace_id="def",
            output_matches=True,
            original_output="hello",
            replay_output="hello",
        )
        assert diff.output_matches

    def test_not_matching(self) -> None:
        diff = ReplayDiff(
            original_trace_id="abc",
            replay_trace_id="def",
            output_matches=False,
            original_output="hello",
            replay_output="goodbye",
            tool_call_diffs=(DiffItem(dimension="tool_calls", similarity=0.5),),
        )
        assert not diff.output_matches
        assert len(diff.tool_call_diffs) == 1


class TestChaosOverride:
    """Test ChaosOverride model."""

    def test_construction(self) -> None:
        override = ChaosOverride(chaos_type=ChaosType.ERROR)
        assert override.chaos_type == ChaosType.ERROR
        assert override.probability == 1.0
        assert override.target_tool is None

    def test_targeted(self) -> None:
        override = ChaosOverride(
            chaos_type=ChaosType.SLOW,
            probability=0.3,
            target_tool="search",
            delay_ms=2000,
        )
        assert override.target_tool == "search"
        assert override.delay_ms == 2000

    def test_probability_bounds(self) -> None:
        with pytest.raises(ValidationError, match="less than or equal to 1"):
            ChaosOverride(chaos_type=ChaosType.ERROR, probability=1.5)

        with pytest.raises(ValidationError, match="greater than or equal to 0"):
            ChaosOverride(chaos_type=ChaosType.ERROR, probability=-0.1)

    def test_frozen(self) -> None:
        override = ChaosOverride(chaos_type=ChaosType.TIMEOUT)
        with pytest.raises(ValidationError):
            override.probability = 0.5  # type: ignore[misc]


class TestMetricEnums:
    """Test new metric-related enums."""

    def test_metric_type_values(self) -> None:
        assert MetricType.LATENCY == "latency"
        assert MetricType.COST == "cost"
        assert MetricType.TOKENS == "tokens"
        assert MetricType.SCORE == "score"
        assert MetricType.COUNT == "count"
        assert MetricType.RATE == "rate"

    def test_metric_type_is_str(self) -> None:
        assert isinstance(MetricType.LATENCY, str)

    def test_trend_direction_values(self) -> None:
        assert TrendDirection.IMPROVING == "improving"
        assert TrendDirection.DEGRADING == "degrading"
        assert TrendDirection.STABLE == "stable"
        assert TrendDirection.INSUFFICIENT_DATA == "insufficient_data"

    def test_plugin_type_values(self) -> None:
        assert PluginType.EVALUATOR == "evaluator"
        assert PluginType.ADAPTER == "adapter"
        assert PluginType.REPORTER == "reporter"
        assert PluginType.STORAGE == "storage"

    def test_plugin_type_is_str(self) -> None:
        assert isinstance(PluginType.EVALUATOR, str)


class TestMetricDefinition:
    """Test MetricDefinition model."""

    def test_construction(self) -> None:
        defn = make_metric_definition()
        assert defn.name == "latency_ms"
        assert defn.metric_type == MetricType.LATENCY
        assert defn.unit == "ms"
        assert defn.lower_is_better is True

    def test_higher_is_better(self) -> None:
        defn = make_metric_definition(
            name="pass_rate",
            metric_type=MetricType.RATE,
            unit="%",
            lower_is_better=False,
        )
        assert defn.lower_is_better is False

    def test_frozen(self) -> None:
        defn = make_metric_definition()
        with pytest.raises(ValidationError):
            defn.name = "changed"  # type: ignore[misc]

    def test_extra_fields_rejected(self) -> None:
        with pytest.raises(ValidationError, match="extra"):
            MetricDefinition(
                name="x",
                metric_type=MetricType.COST,
                bogus="nope",  # type: ignore[call-arg]
            )

    def test_empty_name_rejected(self) -> None:
        with pytest.raises(ValidationError, match="at least 1"):
            MetricDefinition(name="", metric_type=MetricType.COST)

    def test_serialization_roundtrip(self) -> None:
        defn = make_metric_definition()
        json_str = defn.model_dump_json()
        restored = MetricDefinition.model_validate_json(json_str)
        assert restored.name == defn.name
        assert restored.metric_type == defn.metric_type


class TestMetricValue:
    """Test MetricValue model."""

    def test_construction(self) -> None:
        mv = make_metric_value()
        assert mv.metric_name == "latency_ms"
        assert mv.value == 150.0
        assert mv.timestamp.tzinfo is not None

    def test_with_tags(self) -> None:
        mv = make_metric_value(tags=["production", "fast"])
        assert "production" in mv.tags
        assert len(mv.tags) == 2

    def test_frozen(self) -> None:
        mv = make_metric_value()
        with pytest.raises(ValidationError):
            mv.value = 999.0  # type: ignore[misc]

    def test_negative_value_allowed(self) -> None:
        mv = make_metric_value(value=-10.0)
        assert mv.value == -10.0

    def test_serialization_roundtrip(self) -> None:
        mv = make_metric_value(metric_name="cost_usd", value=0.05)
        json_str = mv.model_dump_json()
        restored = MetricValue.model_validate_json(json_str)
        assert restored.metric_name == "cost_usd"
        assert restored.value == 0.05


class TestMetricAggregation:
    """Test MetricAggregation model."""

    def test_construction(self) -> None:
        agg = MetricAggregation(
            metric_name="latency_ms",
            count=10,
            mean=150.5,
            median=145.0,
            min_value=80.0,
            max_value=300.0,
            p95=280.0,
            p99=295.0,
            std_dev=45.2,
        )
        assert agg.count == 10
        assert agg.mean == 150.5
        assert agg.p95 == 280.0

    def test_min_count(self) -> None:
        with pytest.raises(ValidationError, match="greater than or equal to 1"):
            MetricAggregation(metric_name="x", count=0)

    def test_frozen(self) -> None:
        agg = MetricAggregation(metric_name="x", count=1)
        with pytest.raises(ValidationError):
            agg.mean = 99.0  # type: ignore[misc]

    def test_serialization_roundtrip(self) -> None:
        agg = MetricAggregation(
            metric_name="cost_usd", count=5, mean=0.05, median=0.04, std_dev=0.01
        )
        json_str = agg.model_dump_json()
        restored = MetricAggregation.model_validate_json(json_str)
        assert restored.metric_name == "cost_usd"
        assert restored.count == 5


class TestParametrizedModelValidation:
    """Parametrized boundary validation for model fields."""

    @pytest.mark.parametrize(
        "score,should_pass",
        [
            (0.0, True),
            (0.5, True),
            (1.0, True),
            (-0.1, False),
            (1.1, False),
        ],
    )
    def test_eval_result_score_boundaries(self, score: float, should_pass: bool) -> None:
        if should_pass:
            result = EvalResult(
                evaluator_name="test",
                verdict=EvalVerdict.PASS,
                score=score,
            )
            assert result.score == score
        else:
            with pytest.raises(ValidationError):
                EvalResult(
                    evaluator_name="test",
                    verdict=EvalVerdict.PASS,
                    score=score,
                )

    @pytest.mark.parametrize(
        "tokens,should_pass",
        [
            (0, True),
            (1, True),
            (1000000, True),
            (-1, False),
        ],
    )
    def test_llm_call_token_boundaries(self, tokens: int, should_pass: bool) -> None:
        if should_pass:
            call = LLMCall(model="test", input_tokens=tokens)
            assert call.input_tokens == tokens
        else:
            with pytest.raises(ValidationError):
                LLMCall(model="test", input_tokens=tokens)

    @pytest.mark.parametrize(
        "name,should_pass",
        [
            ("valid-test", True),
            ("test_name", True),
            ("test.name", True),
            ("a", True),
            ("", False),
            ("x" * 201, False),
        ],
    )
    def test_test_case_name_boundaries(self, name: str, should_pass: bool) -> None:
        if should_pass:
            tc = TestCase(name=name)
            assert tc.name == name
        else:
            with pytest.raises(ValidationError):
                TestCase(name=name)
