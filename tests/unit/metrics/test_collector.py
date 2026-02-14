"""Tests for the MetricCollector."""

from __future__ import annotations

from agentprobe.core.models import AgentRun, RunStatus, TestStatus
from agentprobe.metrics.collector import MetricCollector
from tests.fixtures.results import make_test_result
from tests.fixtures.traces import make_llm_call, make_tool_call, make_trace


class TestCollectFromTrace:
    """Test metric collection from traces."""

    def test_collects_latency(self) -> None:
        trace = make_trace(llm_calls=[make_llm_call(latency_ms=500)])
        collector = MetricCollector()
        metrics = collector.collect_from_trace(trace)

        latency = [m for m in metrics if m.metric_name == "latency_ms"]
        assert len(latency) == 1
        assert latency[0].value == float(trace.total_latency_ms)

    def test_collects_tool_call_count(self) -> None:
        trace = make_trace(tool_calls=[make_tool_call(), make_tool_call(tool_name="calc")])
        collector = MetricCollector()
        metrics = collector.collect_from_trace(trace)

        tc_count = [m for m in metrics if m.metric_name == "tool_call_count"]
        assert len(tc_count) == 1
        assert tc_count[0].value == 2.0

    def test_collects_response_length(self) -> None:
        trace = make_trace(output_text="Hello, world!")
        collector = MetricCollector()
        metrics = collector.collect_from_trace(trace)

        resp_len = [m for m in metrics if m.metric_name == "response_length"]
        assert len(resp_len) == 1
        assert resp_len[0].value == 13.0

    def test_includes_trace_tags(self) -> None:
        trace = make_trace(tags=["prod", "fast"])
        collector = MetricCollector()
        metrics = collector.collect_from_trace(trace)

        assert all("prod" in m.tags for m in metrics)

    def test_includes_trace_metadata(self) -> None:
        trace = make_trace()
        collector = MetricCollector()
        metrics = collector.collect_from_trace(trace)

        for m in metrics:
            assert "trace_id" in m.metadata
            assert "agent_name" in m.metadata

    def test_empty_trace_returns_three_metrics(self) -> None:
        trace = make_trace(llm_calls=[], tool_calls=[], output_text="")
        collector = MetricCollector()
        metrics = collector.collect_from_trace(trace)

        assert len(metrics) == 3
        tc = [m for m in metrics if m.metric_name == "tool_call_count"]
        assert tc[0].value == 0.0

    def test_multiple_llm_calls(self) -> None:
        trace = make_trace(
            llm_calls=[
                make_llm_call(latency_ms=100),
                make_llm_call(latency_ms=200),
            ]
        )
        collector = MetricCollector()
        metrics = collector.collect_from_trace(trace)

        latency = [m for m in metrics if m.metric_name == "latency_ms"]
        assert latency[0].value == 300.0


class TestCollectFromResult:
    """Test metric collection from test results."""

    def test_collects_latency_and_score(self) -> None:
        result = make_test_result(duration_ms=250, score=0.85)
        collector = MetricCollector()
        metrics = collector.collect_from_result(result)

        latency = [m for m in metrics if m.metric_name == "latency_ms"]
        score = [m for m in metrics if m.metric_name == "eval_score"]
        assert len(latency) >= 1
        assert latency[0].value == 250.0
        assert len(score) == 1
        assert score[0].value == 0.85

    def test_includes_trace_metrics_when_present(self) -> None:
        trace = make_trace(tool_calls=[make_tool_call()])
        result = make_test_result(trace=trace)
        collector = MetricCollector()
        metrics = collector.collect_from_result(result)

        tc_count = [m for m in metrics if m.metric_name == "tool_call_count"]
        assert len(tc_count) == 1

    def test_no_trace_gives_only_result_metrics(self) -> None:
        result = make_test_result(trace=None)
        collector = MetricCollector()
        metrics = collector.collect_from_result(result)

        names = {m.metric_name for m in metrics}
        assert "latency_ms" in names
        assert "eval_score" in names
        assert "tool_call_count" not in names

    def test_metadata_includes_test_name(self) -> None:
        result = make_test_result(test_name="test_greeting")
        collector = MetricCollector()
        metrics = collector.collect_from_result(result)

        for m in metrics:
            if "test_name" in m.metadata:
                assert m.metadata["test_name"] == "test_greeting"


class TestCollectFromRun:
    """Test metric collection from agent runs."""

    def test_collects_pass_rate(self) -> None:
        results = [
            make_test_result(status=TestStatus.PASSED),
            make_test_result(test_name="test_b", status=TestStatus.FAILED, score=0.2),
        ]
        run = AgentRun(
            agent_name="agent",
            status=RunStatus.COMPLETED,
            test_results=tuple(results),
            total_tests=2,
            passed=1,
            failed=1,
        )
        collector = MetricCollector()
        metrics = collector.collect_from_run(run)

        pass_rate = [m for m in metrics if m.metric_name == "pass_rate"]
        assert len(pass_rate) == 1
        assert pass_rate[0].value == 0.5

    def test_empty_run_pass_rate_zero(self) -> None:
        run = AgentRun(
            agent_name="agent",
            status=RunStatus.COMPLETED,
            total_tests=0,
        )
        collector = MetricCollector()
        metrics = collector.collect_from_run(run)

        pass_rate = [m for m in metrics if m.metric_name == "pass_rate"]
        assert pass_rate[0].value == 0.0

    def test_includes_per_result_metrics(self) -> None:
        results = [make_test_result(), make_test_result(test_name="test_b")]
        run = AgentRun(
            agent_name="agent",
            status=RunStatus.COMPLETED,
            test_results=tuple(results),
            total_tests=2,
            passed=2,
        )
        collector = MetricCollector()
        metrics = collector.collect_from_run(run)

        eval_scores = [m for m in metrics if m.metric_name == "eval_score"]
        assert len(eval_scores) == 2

    def test_all_passed_gives_rate_one(self) -> None:
        results = [
            make_test_result(status=TestStatus.PASSED),
            make_test_result(test_name="test_b", status=TestStatus.PASSED),
        ]
        run = AgentRun(
            agent_name="agent",
            status=RunStatus.COMPLETED,
            test_results=tuple(results),
            total_tests=2,
            passed=2,
        )
        collector = MetricCollector()
        metrics = collector.collect_from_run(run)

        pass_rate = [m for m in metrics if m.metric_name == "pass_rate"]
        assert pass_rate[0].value == 1.0
