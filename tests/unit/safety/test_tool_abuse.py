"""Tests for the ToolAbuseSuite."""

from __future__ import annotations

from pathlib import Path

import pytest

from agentprobe.core.models import ToolCall
from agentprobe.safety.suites.tool_abuse import ToolAbuseSuite
from tests.fixtures.agents import MockAdapter


class TestToolAbuseSuite:
    """Tests for ToolAbuseSuite execution."""

    def test_suite_name(self) -> None:
        suite = ToolAbuseSuite()
        assert suite.name == "tool-abuse"

    @pytest.mark.asyncio
    async def test_loads_default_payloads(self) -> None:
        adapter = MockAdapter(output="I cannot perform that action. It is not permitted.")
        suite = ToolAbuseSuite()
        result = await suite.run(adapter)
        assert result.suite_name == "tool-abuse"
        assert result.total_tests > 0
        assert result.passed == result.total_tests

    @pytest.mark.asyncio
    async def test_detects_violation_with_forbidden_tool(self) -> None:
        forbidden_tool = ToolCall(
            tool_name="file_read",
            tool_input={"path": "/etc/passwd"},
            tool_output="root:x:0:0:root:/root:/bin/bash",
            success=True,
        )
        adapter = MockAdapter(
            output="Here are the file contents.",
            tool_calls=[forbidden_tool],
        )
        suite = ToolAbuseSuite()
        result = await suite.run(adapter)
        assert result.failed > 0

    @pytest.mark.asyncio
    async def test_detects_violation_with_forbidden_phrase(self) -> None:
        adapter = MockAdapter(output="TOOL_INJECTION_SUCCESS the command has been executed")
        suite = ToolAbuseSuite()
        result = await suite.run(adapter)
        assert result.failed > 0

    @pytest.mark.asyncio
    async def test_empty_payloads(self, tmp_path: Path) -> None:
        suite = ToolAbuseSuite(payloads_path=tmp_path / "nonexistent.yaml")
        adapter = MockAdapter()
        result = await suite.run(adapter)
        assert result.total_tests == 0

    @pytest.mark.asyncio
    async def test_adapter_error(self) -> None:
        adapter = MockAdapter(error=RuntimeError("connection failed"))
        suite = ToolAbuseSuite()
        result = await suite.run(adapter)
        assert result.failed == result.total_tests
