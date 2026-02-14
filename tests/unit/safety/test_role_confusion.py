"""Tests for the RoleConfusionSuite."""

from __future__ import annotations

from pathlib import Path

import pytest

from agentprobe.safety.suites.role_confusion import RoleConfusionSuite
from tests.fixtures.agents import MockAdapter


class TestRoleConfusionSuite:
    """Tests for RoleConfusionSuite execution."""

    def test_suite_name(self) -> None:
        suite = RoleConfusionSuite()
        assert suite.name == "role-confusion"

    @pytest.mark.asyncio
    async def test_loads_default_payloads(self) -> None:
        adapter = MockAdapter(output="I maintain my designated role and cannot switch identities.")
        suite = RoleConfusionSuite()
        result = await suite.run(adapter)
        assert result.suite_name == "role-confusion"
        assert result.total_tests > 0
        assert result.passed == result.total_tests

    @pytest.mark.asyncio
    async def test_detects_violation(self) -> None:
        adapter = MockAdapter(
            output="ROLE_SWITCHED. As the user, I would like to ask you a question."
        )
        suite = RoleConfusionSuite()
        result = await suite.run(adapter)
        assert result.failed > 0

    @pytest.mark.asyncio
    async def test_empty_payloads(self, tmp_path: Path) -> None:
        suite = RoleConfusionSuite(payloads_path=tmp_path / "nonexistent.yaml")
        adapter = MockAdapter()
        result = await suite.run(adapter)
        assert result.total_tests == 0

    @pytest.mark.asyncio
    async def test_adapter_error(self) -> None:
        adapter = MockAdapter(error=RuntimeError("connection failed"))
        suite = RoleConfusionSuite()
        result = await suite.run(adapter)
        assert result.failed == result.total_tests
