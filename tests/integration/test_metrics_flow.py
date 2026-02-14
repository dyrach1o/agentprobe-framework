"""Integration test: MetricCollector → MetricAggregator → MetricTrend + SQLite storage."""

from __future__ import annotations

from pathlib import Path

import pytest

from agentprobe.core.models import (
    TestCase,
    TrendDirection,
)
from agentprobe.core.runner import TestRunner
from agentprobe.metrics.aggregator import MetricAggregator
from agentprobe.metrics.collector import MetricCollector
from agentprobe.metrics.trend import MetricTrend
from agentprobe.storage.sqlite import SQLiteStorage
from tests.fixtures.agents import MockAdapter
from tests.fixtures.traces import make_llm_call, make_metric_value, make_tool_call


@pytest.mark.integration
class TestMetricsFlow:
    """End-to-end metrics pipeline."""

    @pytest.mark.asyncio
    async def test_collect_from_trace_and_aggregate(self) -> None:
        """Collect metrics from a trace, then aggregate."""
        adapter = MockAdapter(
            name="metrics-agent",
            output="Hello world",
            llm_calls=[make_llm_call(input_tokens=200, output_tokens=100, latency_ms=300)],
            tool_calls=[make_tool_call(tool_name="search", latency_ms=50)],
        )
        trace = await adapter.invoke("test input")

        collector = MetricCollector()
        metrics = collector.collect_from_trace(trace)

        # Should have latency_ms, tool_call_count, response_length
        names = {m.metric_name for m in metrics}
        assert "latency_ms" in names
        assert "tool_call_count" in names
        assert "response_length" in names

        # Aggregate the latency values
        latency_values = [m for m in metrics if m.metric_name == "latency_ms"]
        if latency_values:
            aggregator = MetricAggregator()
            agg = aggregator.aggregate(latency_values)
            assert agg.metric_name == "latency_ms"
            assert agg.count == 1

    @pytest.mark.asyncio
    async def test_collect_from_run_and_aggregate_by_name(self) -> None:
        """Collect metrics from an entire run and aggregate by name."""
        adapter = MockAdapter(
            name="run-metrics",
            output="response",
            llm_calls=[make_llm_call(input_tokens=100, output_tokens=50, latency_ms=150)],
        )
        runner = TestRunner()
        cases = [
            TestCase(name="t1", input_text="input 1"),
            TestCase(name="t2", input_text="input 2"),
            TestCase(name="t3", input_text="input 3"),
        ]

        run = await runner.run(cases, adapter)

        collector = MetricCollector()
        metrics = collector.collect_from_run(run)

        # Should have pass_rate plus per-result metrics
        assert any(m.metric_name == "pass_rate" for m in metrics)

        # Aggregate by name
        aggregator = MetricAggregator()
        by_name = aggregator.aggregate_by_name(metrics)
        assert "pass_rate" in by_name
        assert by_name["pass_rate"].count >= 1

    @pytest.mark.asyncio
    async def test_metrics_trend_analysis(self) -> None:
        """Analyze trend direction from collected metrics."""
        # Simulate improving latency (decreasing values → improving for lower_is_better)
        values = [
            make_metric_value(metric_name="latency_ms", value=500.0),
            make_metric_value(metric_name="latency_ms", value=450.0),
            make_metric_value(metric_name="latency_ms", value=400.0),
            make_metric_value(metric_name="latency_ms", value=350.0),
            make_metric_value(metric_name="latency_ms", value=300.0),
            make_metric_value(metric_name="latency_ms", value=250.0),
        ]

        trend = MetricTrend(threshold=0.1)
        direction = trend.analyze(values, lower_is_better=True)
        assert direction == TrendDirection.IMPROVING

    @pytest.mark.asyncio
    async def test_metrics_persist_and_load(self, tmp_path: Path) -> None:
        """Save metrics to SQLite and load them back."""
        storage = SQLiteStorage(db_path=tmp_path / "metrics.db")
        await storage.setup()

        metrics = [
            make_metric_value(metric_name="latency_ms", value=100.0),
            make_metric_value(metric_name="latency_ms", value=150.0),
            make_metric_value(metric_name="token_cost_usd", value=0.005),
        ]
        await storage.save_metrics(metrics)

        # Load all
        loaded = await storage.load_metrics()
        assert len(loaded) == 3

        # Load by name
        latencies = await storage.load_metrics(metric_name="latency_ms")
        assert len(latencies) == 2

        costs = await storage.load_metrics(metric_name="token_cost_usd")
        assert len(costs) == 1

        await storage.close()

    @pytest.mark.asyncio
    async def test_full_metrics_pipeline(self, tmp_path: Path) -> None:
        """Full pipeline: run → collect → store → load → aggregate → trend."""
        adapter = MockAdapter(
            name="full-pipeline",
            output="result",
            llm_calls=[make_llm_call(input_tokens=100, output_tokens=50, latency_ms=200)],
        )
        runner = TestRunner()
        cases = [TestCase(name=f"test_{i}", input_text=f"input {i}") for i in range(5)]

        run = await runner.run(cases, adapter)
        assert run.status.value == "completed"

        # Collect
        collector = MetricCollector()
        metrics = collector.collect_from_run(run)
        assert len(metrics) > 0

        # Store
        storage = SQLiteStorage(db_path=tmp_path / "pipeline.db")
        await storage.setup()
        await storage.save_metrics(metrics)

        # Load back
        loaded = await storage.load_metrics()
        assert len(loaded) == len(metrics)

        # Aggregate
        aggregator = MetricAggregator()
        by_name = aggregator.aggregate_by_name(loaded)
        assert len(by_name) > 0

        await storage.close()
