"""Tests for the JSONReporter."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentprobe.core.models import AgentRun, RunStatus
from agentprobe.reporting.json_reporter import JSONReporter


class TestJSONReporter:
    """Tests for JSONReporter file output."""

    @pytest.mark.asyncio
    async def test_creates_report_file(self, tmp_path: Path) -> None:
        reporter = JSONReporter(output_dir=tmp_path / "reports")
        run = AgentRun(
            agent_name="test-agent",
            status=RunStatus.COMPLETED,
            total_tests=2,
            passed=2,
        )
        await reporter.report(run)

        report_dir = tmp_path / "reports"
        assert report_dir.exists()
        files = list(report_dir.glob("report-*.json"))
        assert len(files) == 1

        data = json.loads(files[0].read_text())
        assert data["agent_name"] == "test-agent"
        assert data["total_tests"] == 2

    @pytest.mark.asyncio
    async def test_report_content(self, tmp_path: Path) -> None:
        reporter = JSONReporter(output_dir=tmp_path)
        run = AgentRun(
            agent_name="agent",
            status=RunStatus.FAILED,
            total_tests=1,
            failed=1,
        )
        await reporter.report(run)
        files = list(tmp_path.glob("report-*.json"))
        data = json.loads(files[0].read_text())
        assert data["status"] == "failed"

    def test_name_property(self) -> None:
        reporter = JSONReporter()
        assert reporter.name == "json"
