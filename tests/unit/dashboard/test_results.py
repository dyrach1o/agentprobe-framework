"""Tests for the dashboard results endpoints."""

from __future__ import annotations

from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from agentprobe.dashboard.app import create_app
from agentprobe.storage.sqlite import SQLiteStorage
from tests.fixtures.results import make_test_result


@pytest.fixture
async def seeded_client(tmp_path: Path) -> AsyncClient:
    """Create a test client with pre-seeded result data."""
    db = str(tmp_path / "test.db")
    storage = SQLiteStorage(db_path=db)
    await storage.setup()
    results = [
        make_test_result(test_name="test_alpha", result_id="result-1"),
        make_test_result(test_name="test_beta", result_id="result-2"),
        make_test_result(test_name="test_alpha", result_id="result-3"),
    ]
    for r in results:
        await storage.save_result(r)
    await storage.close()

    app = create_app(db_path=db)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


class TestListResults:
    """Tests for GET /api/results."""

    @pytest.mark.asyncio
    async def test_empty_database(self, empty_client: AsyncClient) -> None:
        resp = await empty_client.get("/api/results")
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_returns_all_results(self, seeded_client: AsyncClient) -> None:
        resp = await seeded_client.get("/api/results")
        assert resp.status_code == 200
        assert len(resp.json()) == 3

    @pytest.mark.asyncio
    async def test_filter_by_test_name(self, seeded_client: AsyncClient) -> None:
        resp = await seeded_client.get("/api/results", params={"test_name": "test_alpha"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert all(r["test_name"] == "test_alpha" for r in data)

    @pytest.mark.asyncio
    async def test_limit_parameter(self, seeded_client: AsyncClient) -> None:
        resp = await seeded_client.get("/api/results", params={"limit": 1})
        assert resp.status_code == 200
        assert len(resp.json()) == 1


class TestGetResult:
    """Tests for GET /api/results/{result_id}."""

    @pytest.mark.asyncio
    async def test_existing_result(self, seeded_client: AsyncClient) -> None:
        resp = await seeded_client.get("/api/results/result-1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["result_id"] == "result-1"
        assert data["test_name"] == "test_alpha"

    @pytest.mark.asyncio
    async def test_not_found(self, empty_client: AsyncClient) -> None:
        resp = await empty_client.get("/api/results/nonexistent")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_not_found_detail_message(self, empty_client: AsyncClient) -> None:
        resp = await empty_client.get("/api/results/missing-id")
        assert "missing-id" in resp.json()["detail"]
