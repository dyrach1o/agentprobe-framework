"""Tests for the HallucinationSuite."""

from __future__ import annotations

from pathlib import Path

import pytest

from agentprobe.safety.suites.hallucination import HallucinationSuite
from tests.fixtures.agents import MockAdapter


class TestHallucinationSuite:
    """Tests for HallucinationSuite execution."""

    def test_suite_name(self) -> None:
        suite = HallucinationSuite()
        assert suite.name == "hallucination"

    @pytest.mark.asyncio
    async def test_loads_default_payloads(self) -> None:
        adapter = MockAdapter(
            output="I'm not aware of that person. I cannot find any record of them."
        )
        suite = HallucinationSuite()
        result = await suite.run(adapter)
        assert result.suite_name == "hallucination"
        assert result.total_tests > 0
        assert result.passed == result.total_tests

    @pytest.mark.asyncio
    async def test_detects_violation(self) -> None:
        adapter = MockAdapter(
            output="Dr. Thorniton invented the quantum telescope and argues "
            "that 45 percent of light is refracted through the lens."
        )
        suite = HallucinationSuite()
        result = await suite.run(adapter)
        assert result.failed > 0

    @pytest.mark.asyncio
    async def test_empty_payloads(self, tmp_path: Path) -> None:
        suite = HallucinationSuite(payloads_path=tmp_path / "nonexistent.yaml")
        adapter = MockAdapter()
        result = await suite.run(adapter)
        assert result.total_tests == 0

    @pytest.mark.asyncio
    async def test_adapter_error(self) -> None:
        adapter = MockAdapter(error=RuntimeError("connection failed"))
        suite = HallucinationSuite()
        result = await suite.run(adapter)
        assert result.failed == result.total_tests
