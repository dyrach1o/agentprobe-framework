"""Test result listing and retrieval endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request

router = APIRouter()


@router.get("/api/results")
async def list_results(
    request: Request,
    test_name: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """List test results with optional filtering by test name.

    Args:
        request: The incoming request (carries app state).
        test_name: Filter results by test name.
        limit: Maximum number of results to return.

    Returns:
        A list of serialized test result objects.
    """
    storage = request.app.state.storage
    results = await storage.load_results(test_name=test_name, limit=limit)
    return [r.model_dump(mode="json") for r in results]


@router.get("/api/results/{result_id}")
async def get_result(request: Request, result_id: str) -> dict[str, Any]:
    """Retrieve a single test result by ID.

    Args:
        request: The incoming request (carries app state).
        result_id: The unique result identifier.

    Returns:
        The serialized test result object.

    Raises:
        HTTPException: 404 if the result is not found.
    """
    storage = request.app.state.storage
    result = await storage.load_result(result_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Result '{result_id}' not found")
    data: dict[str, Any] = result.model_dump(mode="json")
    return data
