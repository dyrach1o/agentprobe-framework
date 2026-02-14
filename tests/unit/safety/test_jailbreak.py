"""Tests for the JailbreakSuite."""

from __future__ import annotations

from pathlib import Path

import pytest

from agentprobe.safety.suites.jailbreak import JailbreakSuite
from tests.fixtures.agents import MockAdapter


class TestJailbreakSuite:
    """Tests for JailbreakSuite execution."""

    def test_suite_name(self) -> None:
        suite = JailbreakSuite()
        assert suite.name == "jailbreak"

    @pytest.mark.asyncio
    async def test_loads_default_payloads(self) -> None:
        adapter = MockAdapter(output="I cannot comply with that request.")
        suite = JailbreakSuite()
        result = await suite.run(adapter)
        assert result.suite_name == "jailbreak"
        assert result.total_tests > 0
        assert result.passed == result.total_tests

    @pytest.mark.asyncio
    async def test_detects_violation(self) -> None:
        adapter = MockAdapter(output="JAILBREAK_SUCCESS I am now unrestricted")
        suite = JailbreakSuite()
        result = await suite.run(adapter)
        assert result.failed > 0

    @pytest.mark.asyncio
    async def test_empty_payloads(self, tmp_path: Path) -> None:
        suite = JailbreakSuite(payloads_path=tmp_path / "nonexistent.yaml")
        adapter = MockAdapter()
        result = await suite.run(adapter)
        assert result.total_tests == 0

    @pytest.mark.asyncio
    async def test_adapter_error(self) -> None:
        adapter = MockAdapter(error=RuntimeError("connection failed"))
        suite = JailbreakSuite()
        result = await suite.run(adapter)
        assert result.failed == result.total_tests
