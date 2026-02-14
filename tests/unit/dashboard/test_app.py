"""Tests for the dashboard FastAPI application factory."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from agentprobe.dashboard.app import create_app

if TYPE_CHECKING:
    from httpx import AsyncClient


class TestCreateApp:
    """Tests for create_app and lifespan management."""

    def test_create_app_returns_fastapi_instance(self, tmp_path: Path) -> None:
        db = str(tmp_path / "test.db")
        app = create_app(db_path=db)
        assert app.title == "AgentProbe Dashboard"

    def test_create_app_has_routes(self, tmp_path: Path) -> None:
        db = str(tmp_path / "test.db")
        app = create_app(db_path=db)
        route_paths = [r.path for r in app.routes]
        assert "/api/health" in route_paths
        assert "/api/traces" in route_paths
        assert "/api/results" in route_paths
        assert "/api/metrics" in route_paths

    def test_create_app_stores_storage_in_state(self, tmp_path: Path) -> None:
        db = str(tmp_path / "test.db")
        app = create_app(db_path=db)
        assert hasattr(app.state, "storage")

    @pytest.mark.asyncio
    async def test_health_endpoint_via_client(self, empty_client: AsyncClient) -> None:
        resp = await empty_client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "version" in data

    @pytest.mark.asyncio
    async def test_health_includes_correct_version(self, empty_client: AsyncClient) -> None:
        import agentprobe

        resp = await empty_client.get("/api/health")
        assert resp.json()["version"] == agentprobe.__version__

    @pytest.mark.asyncio
    async def test_traces_empty_after_setup(self, empty_client: AsyncClient) -> None:
        resp = await empty_client.get("/api/traces")
        assert resp.status_code == 200
        assert resp.json() == []
