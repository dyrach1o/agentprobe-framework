"""Shared fixtures for dashboard tests."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from agentprobe.dashboard.app import create_app
from agentprobe.storage.sqlite import SQLiteStorage


@pytest.fixture
async def empty_client(tmp_path: Path) -> AsyncGenerator[AsyncClient, None]:
    """Test client with an empty but initialized database."""
    db = str(tmp_path / "test.db")
    storage = SQLiteStorage(db_path=db)
    await storage.setup()
    await storage.close()

    app = create_app(db_path=db)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
