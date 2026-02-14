"""Tests for dashboard Pydantic schemas."""

from __future__ import annotations

from agentprobe.dashboard.schemas import (
    HealthResponse,
    MetricListParams,
    ResultListParams,
    TraceListParams,
)


class TestHealthResponse:
    """Tests for the HealthResponse schema."""

    def test_defaults(self) -> None:
        resp = HealthResponse()
        assert resp.status == "ok"
        assert resp.version == ""

    def test_custom_values(self) -> None:
        resp = HealthResponse(status="ok", version="0.4.0")
        assert resp.version == "0.4.0"

    def test_frozen(self) -> None:
        resp = HealthResponse()
        try:
            resp.status = "bad"  # type: ignore[misc]
            raised = False
        except Exception:
            raised = True
        assert raised


class TestTraceListParams:
    """Tests for the TraceListParams schema."""

    def test_defaults(self) -> None:
        params = TraceListParams()
        assert params.agent_name is None
        assert params.limit == 100

    def test_custom(self) -> None:
        params = TraceListParams(agent_name="my-agent", limit=50)
        assert params.agent_name == "my-agent"
        assert params.limit == 50


class TestResultListParams:
    """Tests for the ResultListParams schema."""

    def test_defaults(self) -> None:
        params = ResultListParams()
        assert params.test_name is None
        assert params.limit == 100


class TestMetricListParams:
    """Tests for the MetricListParams schema."""

    def test_defaults(self) -> None:
        params = MetricListParams()
        assert params.metric_name is None
        assert params.limit == 1000
