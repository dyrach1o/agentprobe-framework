"""Tests for the dashboard traces endpoints."""

from __future__ import annotations

from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from agentprobe.dashboard.app import create_app
from agentprobe.storage.sqlite import SQLiteStorage
from tests.fixtures.traces import make_trace


@pytest.fixture
async def seeded_client(tmp_path: Path) -> AsyncClient:
    """Create a test client with pre-seeded trace data."""
    db = str(tmp_path / "test.db")
    storage = SQLiteStorage(db_path=db)
    await storage.setup()
    traces = [
        make_trace(agent_name="agent-a", trace_id="trace-1"),
        make_trace(agent_name="agent-b", trace_id="trace-2"),
        make_trace(agent_name="agent-a", trace_id="trace-3"),
    ]
    for t in traces:
        await storage.save_trace(t)
    await storage.close()

    app = create_app(db_path=db)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


class TestListTraces:
    """Tests for GET /api/traces."""

    @pytest.mark.asyncio
    async def test_empty_database(self, empty_client: AsyncClient) -> None:
        resp = await empty_client.get("/api/traces")
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_returns_all_traces(self, seeded_client: AsyncClient) -> None:
        resp = await seeded_client.get("/api/traces")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 3

    @pytest.mark.asyncio
    async def test_filter_by_agent_name(self, seeded_client: AsyncClient) -> None:
        resp = await seeded_client.get("/api/traces", params={"agent_name": "agent-a"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert all(t["agent_name"] == "agent-a" for t in data)

    @pytest.mark.asyncio
    async def test_limit_parameter(self, seeded_client: AsyncClient) -> None:
        resp = await seeded_client.get("/api/traces", params={"limit": 1})
        assert resp.status_code == 200
        assert len(resp.json()) == 1


class TestGetTrace:
    """Tests for GET /api/traces/{trace_id}."""

    @pytest.mark.asyncio
    async def test_existing_trace(self, seeded_client: AsyncClient) -> None:
        resp = await seeded_client.get("/api/traces/trace-1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["trace_id"] == "trace-1"
        assert data["agent_name"] == "agent-a"

    @pytest.mark.asyncio
    async def test_not_found(self, empty_client: AsyncClient) -> None:
        resp = await empty_client.get("/api/traces/nonexistent")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_not_found_detail_message(self, empty_client: AsyncClient) -> None:
        resp = await empty_client.get("/api/traces/missing-id")
        assert "missing-id" in resp.json()["detail"]
