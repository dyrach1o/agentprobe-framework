"""Metric trend analysis: detects improving, degrading, or stable trends.

Compares recent metric values against a historical window to determine
whether performance is changing over time.
"""

from __future__ import annotations

import statistics

from agentprobe.core.models import MetricValue, TrendDirection

_MIN_TREND_SAMPLES = 2


class MetricTrend:
    """Analyzes metric trends by comparing recent vs historical values.

    Uses a split-window approach: divides a time-ordered series of values
    into a historical window and a recent window, then compares means.

    Attributes:
        threshold: Minimum relative change to flag as improving/degrading.
    """

    def __init__(self, threshold: float = 0.1) -> None:
        """Initialize the trend analyzer.

        Args:
            threshold: Minimum relative change (fraction) to consider
                a trend as improving or degrading. Defaults to 0.1 (10%).
        """
        self._threshold = threshold

    def analyze(
        self,
        values: list[MetricValue],
        lower_is_better: bool = True,
    ) -> TrendDirection:
        """Analyze the trend direction for a series of metric values.

        Splits the values in half (by order) and compares means.

        Args:
            values: Time-ordered list of metric values (oldest first).
            lower_is_better: Whether lower values indicate improvement.

        Returns:
            The detected trend direction.

        Raises:
            MetricsError: If fewer than 2 values are provided.
        """
        if len(values) < _MIN_TREND_SAMPLES:
            return TrendDirection.INSUFFICIENT_DATA

        raw = [v.value for v in values]
        return self._analyze_raw(raw, lower_is_better)

    def analyze_series(
        self,
        raw_values: list[float],
        lower_is_better: bool = True,
    ) -> TrendDirection:
        """Analyze the trend from a raw numeric series.

        Args:
            raw_values: Time-ordered list of numeric values (oldest first).
            lower_is_better: Whether lower values indicate improvement.

        Returns:
            The detected trend direction.
        """
        if len(raw_values) < _MIN_TREND_SAMPLES:
            return TrendDirection.INSUFFICIENT_DATA

        return self._analyze_raw(raw_values, lower_is_better)

    def _analyze_raw(self, raw: list[float], lower_is_better: bool) -> TrendDirection:
        """Core trend analysis on raw numeric values.

        Args:
            raw: Ordered list of values.
            lower_is_better: Direction semantics.

        Returns:
            The trend direction.
        """
        midpoint = len(raw) // 2
        historical = raw[:midpoint]
        recent = raw[midpoint:]

        hist_mean = statistics.mean(historical)
        recent_mean = statistics.mean(recent)

        if hist_mean == 0.0:
            if recent_mean == 0.0:
                return TrendDirection.STABLE
            return TrendDirection.DEGRADING if lower_is_better else TrendDirection.IMPROVING

        relative_change = (recent_mean - hist_mean) / abs(hist_mean)

        if abs(relative_change) < self._threshold:
            return TrendDirection.STABLE

        value_decreased = relative_change < 0

        if lower_is_better:
            return TrendDirection.IMPROVING if value_decreased else TrendDirection.DEGRADING
        else:
            return TrendDirection.DEGRADING if value_decreased else TrendDirection.IMPROVING
