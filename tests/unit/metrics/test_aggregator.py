"""Tests for the MetricAggregator."""

from __future__ import annotations

import pytest

from agentprobe.core.exceptions import MetricsError
from agentprobe.metrics.aggregator import MetricAggregator
from tests.fixtures.traces import make_metric_value


class TestAggregate:
    """Test single-metric aggregation."""

    @pytest.fixture
    def aggregator(self) -> MetricAggregator:
        return MetricAggregator()

    def test_basic_aggregation(self, aggregator: MetricAggregator) -> None:
        values = [make_metric_value(value=v) for v in [100.0, 200.0, 300.0]]
        agg = aggregator.aggregate(values)

        assert agg.metric_name == "latency_ms"
        assert agg.count == 3
        assert agg.mean == pytest.approx(200.0)
        assert agg.median == pytest.approx(200.0)
        assert agg.min_value == pytest.approx(100.0)
        assert agg.max_value == pytest.approx(300.0)

    def test_single_value(self, aggregator: MetricAggregator) -> None:
        values = [make_metric_value(value=42.0)]
        agg = aggregator.aggregate(values)

        assert agg.count == 1
        assert agg.mean == pytest.approx(42.0)
        assert agg.std_dev == pytest.approx(0.0)
        assert agg.p95 == pytest.approx(42.0)
        assert agg.p99 == pytest.approx(42.0)

    def test_two_values(self, aggregator: MetricAggregator) -> None:
        values = [make_metric_value(value=10.0), make_metric_value(value=20.0)]
        agg = aggregator.aggregate(values)

        assert agg.count == 2
        assert agg.mean == pytest.approx(15.0)
        assert agg.median == pytest.approx(15.0)
        assert agg.std_dev > 0

    def test_std_dev_correctness(self, aggregator: MetricAggregator) -> None:
        values = [make_metric_value(value=v) for v in [2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0]]
        agg = aggregator.aggregate(values)
        assert agg.std_dev == pytest.approx(2.138, abs=0.01)

    def test_p95_ordering(self, aggregator: MetricAggregator) -> None:
        values = [make_metric_value(value=float(i)) for i in range(1, 101)]
        agg = aggregator.aggregate(values)

        assert agg.p95 == pytest.approx(95.05, abs=0.5)
        assert agg.p99 == pytest.approx(99.01, abs=0.5)
        assert agg.min_value == pytest.approx(1.0)
        assert agg.max_value == pytest.approx(100.0)

    def test_empty_raises(self, aggregator: MetricAggregator) -> None:
        with pytest.raises(MetricsError, match="empty"):
            aggregator.aggregate([])

    def test_mixed_names_raises(self, aggregator: MetricAggregator) -> None:
        values = [
            make_metric_value(metric_name="latency_ms"),
            make_metric_value(metric_name="cost_usd"),
        ]
        with pytest.raises(MetricsError, match="mixed"):
            aggregator.aggregate(values)

    def test_all_same_values(self, aggregator: MetricAggregator) -> None:
        values = [make_metric_value(value=5.0) for _ in range(10)]
        agg = aggregator.aggregate(values)

        assert agg.mean == pytest.approx(5.0)
        assert agg.std_dev == pytest.approx(0.0)
        assert agg.min_value == pytest.approx(5.0)
        assert agg.max_value == pytest.approx(5.0)

    def test_negative_values(self, aggregator: MetricAggregator) -> None:
        values = [make_metric_value(value=v) for v in [-10.0, -5.0, 0.0, 5.0, 10.0]]
        agg = aggregator.aggregate(values)

        assert agg.mean == pytest.approx(0.0)
        assert agg.min_value == pytest.approx(-10.0)
        assert agg.max_value == pytest.approx(10.0)


class TestAggregateByName:
    """Test multi-metric aggregation."""

    @pytest.fixture
    def aggregator(self) -> MetricAggregator:
        return MetricAggregator()

    def test_groups_by_name(self, aggregator: MetricAggregator) -> None:
        values = [
            make_metric_value(metric_name="latency_ms", value=100.0),
            make_metric_value(metric_name="latency_ms", value=200.0),
            make_metric_value(metric_name="cost_usd", value=0.01),
            make_metric_value(metric_name="cost_usd", value=0.02),
        ]
        result = aggregator.aggregate_by_name(values)

        assert "latency_ms" in result
        assert "cost_usd" in result
        assert result["latency_ms"].count == 2
        assert result["cost_usd"].count == 2

    def test_single_name(self, aggregator: MetricAggregator) -> None:
        values = [make_metric_value(value=10.0), make_metric_value(value=20.0)]
        result = aggregator.aggregate_by_name(values)

        assert len(result) == 1
        assert "latency_ms" in result

    def test_empty_raises(self, aggregator: MetricAggregator) -> None:
        with pytest.raises(MetricsError, match="empty"):
            aggregator.aggregate_by_name([])

    def test_many_names(self, aggregator: MetricAggregator) -> None:
        values = [
            make_metric_value(metric_name="a", value=1.0),
            make_metric_value(metric_name="b", value=2.0),
            make_metric_value(metric_name="c", value=3.0),
        ]
        result = aggregator.aggregate_by_name(values)
        assert len(result) == 3
