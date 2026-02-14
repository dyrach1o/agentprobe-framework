"""Tests for the TerminalReporter."""

from __future__ import annotations

import pytest
from rich.console import Console

from agentprobe.core.models import AgentRun, RunStatus, TestStatus
from agentprobe.reporting.terminal import TerminalReporter
from tests.fixtures.results import make_test_result


class TestTerminalReporter:
    """Tests for TerminalReporter output."""

    @pytest.mark.asyncio
    async def test_report_empty_run(self) -> None:
        console = Console(file=None, force_terminal=True, width=120)
        reporter = TerminalReporter(console=console)
        run = AgentRun(
            agent_name="test-agent",
            status=RunStatus.COMPLETED,
            total_tests=0,
        )
        await reporter.report(run)

    @pytest.mark.asyncio
    async def test_report_with_results(self) -> None:
        console = Console(file=None, force_terminal=True, width=120)
        reporter = TerminalReporter(console=console)
        results = [
            make_test_result(test_name="test_pass", status=TestStatus.PASSED),
            make_test_result(test_name="test_fail", status=TestStatus.FAILED, score=0.3),
        ]
        run = AgentRun(
            agent_name="test-agent",
            status=RunStatus.COMPLETED,
            test_results=tuple(results),
            total_tests=2,
            passed=1,
            failed=1,
        )
        await reporter.report(run)

    @pytest.mark.asyncio
    async def test_report_with_errors(self) -> None:
        console = Console(file=None, force_terminal=True, width=120)
        reporter = TerminalReporter(console=console)
        results = [
            make_test_result(
                test_name="test_err",
                status=TestStatus.ERROR,
                error_message="connection failed",
            ),
        ]
        run = AgentRun(
            agent_name="agent",
            status=RunStatus.FAILED,
            test_results=tuple(results),
            total_tests=1,
            errors=1,
        )
        await reporter.report(run)

    def test_name_property(self) -> None:
        reporter = TerminalReporter()
        assert reporter.name == "terminal"
