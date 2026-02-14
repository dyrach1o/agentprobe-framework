"""Optional dashboard: FastAPI REST API for browsing traces, results, and metrics."""

from agentprobe.dashboard.app import create_app
from agentprobe.dashboard.schemas import HealthResponse

__all__ = [
    "HealthResponse",
    "create_app",
]
