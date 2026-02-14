"""FastAPI application factory for the AgentProbe dashboard.

Provides ``create_app`` which wires up storage, routes, and
lifespan management.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from agentprobe.dashboard.routes.health import router as health_router
from agentprobe.dashboard.routes.metrics import router as metrics_router
from agentprobe.dashboard.routes.results import router as results_router
from agentprobe.dashboard.routes.traces import router as traces_router
from agentprobe.storage.sqlite import SQLiteStorage


def create_app(db_path: str = ".agentprobe/traces.db") -> FastAPI:
    """Create a configured FastAPI application.

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        A FastAPI app with all routes and storage wired up.
    """
    storage = SQLiteStorage(db_path=db_path)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        await storage.setup()
        yield
        await storage.close()

    app = FastAPI(
        title="AgentProbe Dashboard",
        description="REST API for browsing traces, results, and metrics.",
        lifespan=lifespan,
    )

    app.state.storage = storage

    app.include_router(health_router)
    app.include_router(traces_router)
    app.include_router(results_router)
    app.include_router(metrics_router)

    return app
