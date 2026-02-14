"""Pytest configuration and shared fixtures for AgentProbe tests."""

import pytest

from agentprobe.core.models import (
    TestCase,
    Trace,
)
from tests.fixtures.agents import MockAdapter
from tests.fixtures.traces import make_llm_call, make_tool_call, make_trace


@pytest.fixture
def mock_adapter() -> MockAdapter:
    """Provide a default MockAdapter instance."""
    return MockAdapter()


@pytest.fixture
def sample_trace() -> Trace:
    """Provide a sample trace for testing."""
    return make_trace(
        llm_calls=[make_llm_call()],
        tool_calls=[make_tool_call()],
    )


@pytest.fixture
def sample_test_case() -> TestCase:
    """Provide a sample test case for testing."""
    return TestCase(name="sample_test", input_text="Hello, agent!")
