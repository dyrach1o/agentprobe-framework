"""Metric definitions, aggregation, and trend analysis."""

from agentprobe.metrics.aggregator import MetricAggregator
from agentprobe.metrics.collector import MetricCollector
from agentprobe.metrics.definitions import (
    BUILTIN_METRICS,
    get_builtin_definitions,
    get_definition,
)
from agentprobe.metrics.trend import MetricTrend

__all__ = [
    "BUILTIN_METRICS",
    "MetricAggregator",
    "MetricCollector",
    "MetricTrend",
    "get_builtin_definitions",
    "get_definition",
]
