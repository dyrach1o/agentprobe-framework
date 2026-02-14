"""Metric aggregation: computes statistical summaries from metric values.

Uses stdlib ``statistics`` module for calculations — no numpy dependency.
"""

from __future__ import annotations

import math
import statistics
from collections import defaultdict

from agentprobe.core.exceptions import MetricsError
from agentprobe.core.models import MetricAggregation, MetricValue

_MIN_STDEV_SAMPLES = 2


class MetricAggregator:
    """Computes statistical aggregations over collections of metric values.

    Supports mean, median, min, max, p95, p99, and standard deviation.
    All computations use the stdlib ``statistics`` module.
    """

    def aggregate(self, values: list[MetricValue]) -> MetricAggregation:
        """Aggregate a list of metric values into summary statistics.

        All values must share the same metric_name.

        Args:
            values: List of metric values to aggregate.

        Returns:
            A MetricAggregation with computed statistics.

        Raises:
            MetricsError: If values is empty or metric names are inconsistent.
        """
        if not values:
            raise MetricsError("Cannot aggregate empty metric list")

        names = {v.metric_name for v in values}
        if len(names) > 1:
            raise MetricsError(f"Cannot aggregate mixed metrics: {', '.join(sorted(names))}")

        metric_name = values[0].metric_name
        raw = [v.value for v in values]

        return self._compute_stats(metric_name, raw)

    def aggregate_by_name(self, values: list[MetricValue]) -> dict[str, MetricAggregation]:
        """Group metric values by name and aggregate each group.

        Args:
            values: List of metric values (may contain multiple metric names).

        Returns:
            A dictionary mapping metric names to their aggregations.

        Raises:
            MetricsError: If values is empty.
        """
        if not values:
            raise MetricsError("Cannot aggregate empty metric list")

        grouped: dict[str, list[float]] = defaultdict(list)
        for v in values:
            grouped[v.metric_name].append(v.value)

        return {name: self._compute_stats(name, raw_values) for name, raw_values in grouped.items()}

    def _compute_stats(self, metric_name: str, raw: list[float]) -> MetricAggregation:
        """Compute statistics for a list of numeric values.

        Args:
            metric_name: The metric name for the aggregation.
            raw: Raw numeric values to aggregate.

        Returns:
            A MetricAggregation with computed statistics.
        """
        n = len(raw)
        mean = statistics.mean(raw)
        median = statistics.median(raw)
        min_val = min(raw)
        max_val = max(raw)
        std_dev = statistics.stdev(raw) if n >= _MIN_STDEV_SAMPLES else 0.0

        sorted_raw = sorted(raw)
        p95 = self._percentile(sorted_raw, 0.95)
        p99 = self._percentile(sorted_raw, 0.99)

        return MetricAggregation(
            metric_name=metric_name,
            count=n,
            mean=mean,
            median=median,
            min_value=min_val,
            max_value=max_val,
            p95=p95,
            p99=p99,
            std_dev=std_dev,
        )

    @staticmethod
    def _percentile(sorted_data: list[float], pct: float) -> float:
        """Compute a percentile using linear interpolation.

        Args:
            sorted_data: Pre-sorted list of values.
            pct: Percentile as a fraction (e.g. 0.95 for 95th).

        Returns:
            The interpolated percentile value.
        """
        n = len(sorted_data)
        if n == 1:
            return sorted_data[0]

        idx = pct * (n - 1)
        lower = math.floor(idx)
        upper = math.ceil(idx)

        if lower == upper:
            return sorted_data[lower]

        frac = idx - lower
        return sorted_data[lower] * (1.0 - frac) + sorted_data[upper] * frac
