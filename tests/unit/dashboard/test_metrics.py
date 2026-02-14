"""Tests for the dashboard metrics endpoints."""

from __future__ import annotations

from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from agentprobe.dashboard.app import create_app
from agentprobe.storage.sqlite import SQLiteStorage
from tests.fixtures.traces import make_metric_value


@pytest.fixture
async def seeded_client(tmp_path: Path) -> AsyncClient:
    """Create a test client with pre-seeded metric data."""
    db = str(tmp_path / "test.db")
    storage = SQLiteStorage(db_path=db)
    await storage.setup()
    metrics = [
        make_metric_value(metric_name="latency_ms", value=100.0),
        make_metric_value(metric_name="latency_ms", value=200.0),
        make_metric_value(metric_name="cost_usd", value=0.05),
    ]
    await storage.save_metrics(metrics)
    await storage.close()

    app = create_app(db_path=db)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


class TestListMetrics:
    """Tests for GET /api/metrics."""

    @pytest.mark.asyncio
    async def test_empty_database(self, empty_client: AsyncClient) -> None:
        resp = await empty_client.get("/api/metrics")
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_returns_all_metrics(self, seeded_client: AsyncClient) -> None:
        resp = await seeded_client.get("/api/metrics")
        assert resp.status_code == 200
        assert len(resp.json()) == 3

    @pytest.mark.asyncio
    async def test_filter_by_metric_name(self, seeded_client: AsyncClient) -> None:
        resp = await seeded_client.get("/api/metrics", params={"metric_name": "latency_ms"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert all(m["metric_name"] == "latency_ms" for m in data)

    @pytest.mark.asyncio
    async def test_limit_parameter(self, seeded_client: AsyncClient) -> None:
        resp = await seeded_client.get("/api/metrics", params={"limit": 1})
        assert resp.status_code == 200
        assert len(resp.json()) == 1


class TestMetricsSummary:
    """Tests for GET /api/metrics/summary."""

    @pytest.mark.asyncio
    async def test_empty_database(self, empty_client: AsyncClient) -> None:
        resp = await empty_client.get("/api/metrics/summary")
        assert resp.status_code == 200
        assert resp.json() == {}

    @pytest.mark.asyncio
    async def test_returns_aggregations(self, seeded_client: AsyncClient) -> None:
        resp = await seeded_client.get("/api/metrics/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert "latency_ms" in data
        assert "cost_usd" in data
        assert data["latency_ms"]["count"] == 2
        assert data["cost_usd"]["count"] == 1

    @pytest.mark.asyncio
    async def test_aggregation_mean(self, seeded_client: AsyncClient) -> None:
        resp = await seeded_client.get("/api/metrics/summary")
        data = resp.json()
        assert data["latency_ms"]["mean"] == pytest.approx(150.0)
