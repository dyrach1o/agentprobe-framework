"""Shared fixtures for integration tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from agentprobe.core.models import TestCase
from tests.fixtures.agents import MockAdapter
from tests.fixtures.traces import make_llm_call, make_tool_call


@pytest.fixture
def tmp_db(tmp_path: Path) -> Path:
    """Return a temporary database path."""
    return tmp_path / "test.db"


@pytest.fixture
def adapter_with_tools() -> MockAdapter:
    """Adapter that returns traces with LLM calls and tool calls."""
    return MockAdapter(
        name="integration-agent",
        output="Hello! I found the answer using a tool.",
        llm_calls=[make_llm_call(model="test-model", input_tokens=200, output_tokens=100)],
        tool_calls=[make_tool_call(tool_name="search", tool_output="result data")],
    )


@pytest.fixture
def simple_test_cases() -> list[TestCase]:
    """A small set of test cases for integration testing."""
    return [
        TestCase(name="test_greeting", input_text="Hello, agent!"),
        TestCase(name="test_question", input_text="What is the capital of France?"),
        TestCase(name="test_tool_use", input_text="Search for recent news"),
    ]
