"""End-to-end test configuration and shared fixtures.

Provides skip logic for missing framework dependencies and API keys,
plus shared fixtures for model name and API key access.
"""

from __future__ import annotations

import os

import pytest

# ── Dependency detection ──

try:
    import langchain_anthropic  # noqa: F401

    HAS_LANGCHAIN = True
except ImportError:
    HAS_LANGCHAIN = False

try:
    import crewai  # noqa: F401

    HAS_CREWAI = True
except ImportError:
    HAS_CREWAI = False

try:
    import autogen  # noqa: F401

    HAS_AUTOGEN = True
except ImportError:
    HAS_AUTOGEN = False

# MCP tests use a local mock server — no package required
HAS_MCP = True

# ── Skip conditions ──

requires_langchain = pytest.mark.skipif(
    not HAS_LANGCHAIN,
    reason="langchain-anthropic not installed",
)
requires_crewai = pytest.mark.skipif(
    not HAS_CREWAI,
    reason="crewai not installed",
)
requires_autogen = pytest.mark.skipif(
    not HAS_AUTOGEN,
    reason="autogen-agentchat not installed",
)
requires_api_key = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set",
)


# ── Shared fixtures ──


@pytest.fixture
def api_key() -> str:
    """Return the Anthropic API key from the environment."""
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        pytest.skip("ANTHROPIC_API_KEY not set")
    return key


@pytest.fixture
def model_name() -> str:
    """Return the cheapest model to use for E2E tests."""
    return "claude-haiku-4-5-20251001"
