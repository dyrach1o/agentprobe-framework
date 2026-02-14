"""Metric listing and summary endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from agentprobe.metrics.aggregator import MetricAggregator

router = APIRouter()


@router.get("/api/metrics")
async def list_metrics(
    request: Request,
    metric_name: str | None = None,
    limit: int = 1000,
) -> list[dict[str, Any]]:
    """List metric values with optional filtering by name.

    Args:
        request: The incoming request (carries app state).
        metric_name: Filter by metric name.
        limit: Maximum number of metric values to return.

    Returns:
        A list of serialized metric value objects.
    """
    storage = request.app.state.storage
    values = await storage.load_metrics(metric_name=metric_name, limit=limit)
    return [v.model_dump(mode="json") for v in values]


@router.get("/api/metrics/summary")
async def metrics_summary(request: Request) -> dict[str, dict[str, Any]]:
    """Return aggregated summaries for all metrics.

    Args:
        request: The incoming request (carries app state).

    Returns:
        A mapping of metric name to aggregated summary.
    """
    storage = request.app.state.storage
    values = await storage.load_metrics()
    if not values:
        return {}
    aggregator = MetricAggregator()
    aggregations = aggregator.aggregate_by_name(list(values))
    return {name: agg.model_dump(mode="json") for name, agg in aggregations.items()}
