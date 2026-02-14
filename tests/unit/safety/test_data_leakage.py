"""Tests for the DataLeakageSuite."""

from __future__ import annotations

from pathlib import Path

import pytest

from agentprobe.safety.suites.data_leakage import DataLeakageSuite
from tests.fixtures.agents import MockAdapter


class TestDataLeakageSuite:
    """Tests for DataLeakageSuite execution."""

    def test_suite_name(self) -> None:
        suite = DataLeakageSuite()
        assert suite.name == "data-leakage"

    @pytest.mark.asyncio
    async def test_loads_default_payloads(self) -> None:
        adapter = MockAdapter(output="I cannot share private or sensitive information.")
        suite = DataLeakageSuite()
        result = await suite.run(adapter)
        assert result.suite_name == "data-leakage"
        assert result.total_tests > 0
        assert result.passed == result.total_tests

    @pytest.mark.asyncio
    async def test_detects_violation(self) -> None:
        adapter = MockAdapter(output="Sure, your SSN is 123-45-6789. Let me confirm that for you.")
        suite = DataLeakageSuite()
        result = await suite.run(adapter)
        assert result.failed > 0

    @pytest.mark.asyncio
    async def test_empty_payloads(self, tmp_path: Path) -> None:
        suite = DataLeakageSuite(payloads_path=tmp_path / "nonexistent.yaml")
        adapter = MockAdapter()
        result = await suite.run(adapter)
        assert result.total_tests == 0

    @pytest.mark.asyncio
    async def test_adapter_error(self) -> None:
        adapter = MockAdapter(error=RuntimeError("connection failed"))
        suite = DataLeakageSuite()
        result = await suite.run(adapter)
        assert result.failed == result.total_tests
