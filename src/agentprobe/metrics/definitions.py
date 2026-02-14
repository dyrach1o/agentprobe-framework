"""Built-in metric definitions for common agent performance measurements.

Provides a registry of standard metrics that can be collected automatically
during test execution, covering latency, cost, token usage, and scores.
"""

from __future__ import annotations

from agentprobe.core.models import MetricDefinition, MetricType

BUILTIN_METRICS: dict[str, MetricDefinition] = {
    "latency_ms": MetricDefinition(
        name="latency_ms",
        metric_type=MetricType.LATENCY,
        description="Total execution latency in milliseconds",
        unit="ms",
        lower_is_better=True,
    ),
    "token_cost_usd": MetricDefinition(
        name="token_cost_usd",
        metric_type=MetricType.COST,
        description="Estimated token cost in USD",
        unit="usd",
        lower_is_better=True,
    ),
    "tool_call_count": MetricDefinition(
        name="tool_call_count",
        metric_type=MetricType.COUNT,
        description="Number of tool calls made during execution",
        unit="count",
        lower_is_better=True,
    ),
    "response_length": MetricDefinition(
        name="response_length",
        metric_type=MetricType.COUNT,
        description="Character length of the agent response",
        unit="chars",
        lower_is_better=False,
    ),
    "eval_score": MetricDefinition(
        name="eval_score",
        metric_type=MetricType.SCORE,
        description="Average evaluator score across all evaluators",
        unit="score",
        lower_is_better=False,
    ),
    "pass_rate": MetricDefinition(
        name="pass_rate",
        metric_type=MetricType.RATE,
        description="Proportion of tests that passed",
        unit="ratio",
        lower_is_better=False,
    ),
}


def get_builtin_definitions() -> dict[str, MetricDefinition]:
    """Return all built-in metric definitions.

    Returns:
        A dictionary mapping metric names to their definitions.
    """
    return dict(BUILTIN_METRICS)


def get_definition(name: str) -> MetricDefinition | None:
    """Look up a built-in metric definition by name.

    Args:
        name: The metric name to look up.

    Returns:
        The metric definition if found, otherwise None.
    """
    return BUILTIN_METRICS.get(name)
