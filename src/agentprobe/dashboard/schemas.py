"""Pydantic response and request schemas for the dashboard API."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    """Response for the health check endpoint."""

    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")

    status: str = "ok"
    version: str = ""


class TraceListParams(BaseModel):
    """Query parameters for listing traces."""

    model_config = ConfigDict(strict=True, extra="forbid")

    agent_name: str | None = None
    limit: int = 100


class ResultListParams(BaseModel):
    """Query parameters for listing results."""

    model_config = ConfigDict(strict=True, extra="forbid")

    test_name: str | None = None
    limit: int = 100


class MetricListParams(BaseModel):
    """Query parameters for listing metrics."""

    model_config = ConfigDict(strict=True, extra="forbid")

    metric_name: str | None = None
    limit: int = 1000
