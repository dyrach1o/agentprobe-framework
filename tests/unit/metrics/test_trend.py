"""Tests for MetricTrend analyzer."""

from __future__ import annotations

from agentprobe.core.models import TrendDirection
from agentprobe.metrics.trend import MetricTrend
from tests.fixtures.traces import make_metric_value


class TestAnalyze:
    """Test trend analysis from MetricValue lists."""

    def test_improving_lower_is_better(self) -> None:
        values = [make_metric_value(value=v) for v in [200.0, 190.0, 150.0, 100.0]]
        trend = MetricTrend(threshold=0.1)
        result = trend.analyze(values, lower_is_better=True)
        assert result == TrendDirection.IMPROVING

    def test_degrading_lower_is_better(self) -> None:
        values = [make_metric_value(value=v) for v in [100.0, 110.0, 200.0, 250.0]]
        trend = MetricTrend(threshold=0.1)
        result = trend.analyze(values, lower_is_better=True)
        assert result == TrendDirection.DEGRADING

    def test_stable_values(self) -> None:
        values = [make_metric_value(value=v) for v in [100.0, 101.0, 99.0, 100.0]]
        trend = MetricTrend(threshold=0.1)
        result = trend.analyze(values, lower_is_better=True)
        assert result == TrendDirection.STABLE

    def test_improving_higher_is_better(self) -> None:
        values = [make_metric_value(value=v) for v in [0.5, 0.6, 0.8, 0.9]]
        trend = MetricTrend(threshold=0.1)
        result = trend.analyze(values, lower_is_better=False)
        assert result == TrendDirection.IMPROVING

    def test_degrading_higher_is_better(self) -> None:
        values = [make_metric_value(value=v) for v in [0.9, 0.85, 0.5, 0.4]]
        trend = MetricTrend(threshold=0.1)
        result = trend.analyze(values, lower_is_better=False)
        assert result == TrendDirection.DEGRADING

    def test_insufficient_data_single(self) -> None:
        values = [make_metric_value(value=100.0)]
        trend = MetricTrend()
        assert trend.analyze(values) == TrendDirection.INSUFFICIENT_DATA

    def test_insufficient_data_empty(self) -> None:
        trend = MetricTrend()
        assert trend.analyze([]) == TrendDirection.INSUFFICIENT_DATA

    def test_two_values_minimum(self) -> None:
        values = [make_metric_value(value=100.0), make_metric_value(value=50.0)]
        trend = MetricTrend(threshold=0.1)
        result = trend.analyze(values, lower_is_better=True)
        assert result == TrendDirection.IMPROVING

    def test_custom_threshold(self) -> None:
        values = [make_metric_value(value=v) for v in [100.0, 100.0, 105.0, 105.0]]
        loose = MetricTrend(threshold=0.1)
        assert loose.analyze(values, lower_is_better=True) == TrendDirection.STABLE

        tight = MetricTrend(threshold=0.01)
        assert tight.analyze(values, lower_is_better=True) == TrendDirection.DEGRADING


class TestAnalyzeSeries:
    """Test trend analysis from raw numeric series."""

    def test_improving_series(self) -> None:
        trend = MetricTrend(threshold=0.1)
        result = trend.analyze_series([200.0, 180.0, 100.0, 80.0], lower_is_better=True)
        assert result == TrendDirection.IMPROVING

    def test_degrading_series(self) -> None:
        trend = MetricTrend(threshold=0.1)
        result = trend.analyze_series([100.0, 110.0, 200.0, 250.0], lower_is_better=True)
        assert result == TrendDirection.DEGRADING

    def test_stable_series(self) -> None:
        trend = MetricTrend(threshold=0.1)
        result = trend.analyze_series([100.0, 102.0, 101.0, 99.0])
        assert result == TrendDirection.STABLE

    def test_insufficient_data(self) -> None:
        trend = MetricTrend()
        assert trend.analyze_series([]) == TrendDirection.INSUFFICIENT_DATA
        assert trend.analyze_series([1.0]) == TrendDirection.INSUFFICIENT_DATA

    def test_zero_historical_mean(self) -> None:
        trend = MetricTrend(threshold=0.1)
        result = trend.analyze_series([0.0, 0.0, 5.0, 10.0], lower_is_better=True)
        assert result == TrendDirection.DEGRADING

    def test_zero_both_means(self) -> None:
        trend = MetricTrend(threshold=0.1)
        result = trend.analyze_series([0.0, 0.0, 0.0, 0.0])
        assert result == TrendDirection.STABLE
