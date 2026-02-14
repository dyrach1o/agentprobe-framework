"""Trace listing and retrieval endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request

router = APIRouter()


@router.get("/api/traces")
async def list_traces(
    request: Request,
    agent_name: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """List traces with optional filtering by agent name.

    Args:
        request: The incoming request (carries app state).
        agent_name: Filter traces by agent name.
        limit: Maximum number of traces to return.

    Returns:
        A list of serialized trace objects.
    """
    storage = request.app.state.storage
    traces = await storage.list_traces(agent_name=agent_name, limit=limit)
    return [t.model_dump(mode="json") for t in traces]


@router.get("/api/traces/{trace_id}")
async def get_trace(request: Request, trace_id: str) -> dict[str, Any]:
    """Retrieve a single trace by ID.

    Args:
        request: The incoming request (carries app state).
        trace_id: The unique trace identifier.

    Returns:
        The serialized trace object.

    Raises:
        HTTPException: 404 if the trace is not found.
    """
    storage = request.app.state.storage
    trace = await storage.load_trace(trace_id)
    if trace is None:
        raise HTTPException(status_code=404, detail=f"Trace '{trace_id}' not found")
    result: dict[str, Any] = trace.model_dump(mode="json")
    return result
