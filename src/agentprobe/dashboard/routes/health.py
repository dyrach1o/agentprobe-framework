"""Health check endpoint."""

from __future__ import annotations

from fastapi import APIRouter

import agentprobe
from agentprobe.dashboard.schemas import HealthResponse

router = APIRouter()


@router.get("/api/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Return service health status and version."""
    return HealthResponse(status="ok", version=agentprobe.__version__)
