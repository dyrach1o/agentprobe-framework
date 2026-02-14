"""Tests for the HTMLReporter."""

from __future__ import annotations

from pathlib import Path

from agentprobe.core.models import AgentRun, RunStatus, TestStatus
from agentprobe.reporting.html import HTMLReporter
from tests.fixtures.results import make_test_result


class TestHTMLReporter:
    """Tests for HTMLReporter HTML output."""

    def _make_run(self, **kwargs: object) -> AgentRun:
        defaults = {
            "agent_name": "test-agent",
            "status": RunStatus.COMPLETED,
            "total_tests": 2,
            "passed": 1,
            "failed": 1,
            "duration_ms": 500,
            "test_results": (
                make_test_result(test_name="test_pass", status=TestStatus.PASSED),
                make_test_result(
                    test_name="test_fail",
                    status=TestStatus.FAILED,
                    score=0.2,
                    error_message="assertion failed",
                ),
            ),
        }
        defaults.update(kwargs)
        return AgentRun(**defaults)

    async def test_creates_html_file(self, tmp_path: Path) -> None:
        reporter = HTMLReporter(output_dir=tmp_path)
        run = self._make_run()
        await reporter.report(run)

        files = list(tmp_path.glob("report-*.html"))
        assert len(files) == 1

    async def test_html_contains_agent_name(self, tmp_path: Path) -> None:
        reporter = HTMLReporter(output_dir=tmp_path)
        run = self._make_run()
        await reporter.report(run)

        files = list(tmp_path.glob("report-*.html"))
        content = files[0].read_text(encoding="utf-8")
        assert "test-agent" in content

    async def test_html_contains_test_results(self, tmp_path: Path) -> None:
        reporter = HTMLReporter(output_dir=tmp_path)
        run = self._make_run()
        await reporter.report(run)

        files = list(tmp_path.glob("report-*.html"))
        content = files[0].read_text(encoding="utf-8")
        assert "test_pass" in content
        assert "test_fail" in content

    async def test_html_contains_summary(self, tmp_path: Path) -> None:
        reporter = HTMLReporter(output_dir=tmp_path)
        run = self._make_run()
        await reporter.report(run)

        files = list(tmp_path.glob("report-*.html"))
        content = files[0].read_text(encoding="utf-8")
        assert "500ms" in content

    async def test_html_has_css(self, tmp_path: Path) -> None:
        reporter = HTMLReporter(output_dir=tmp_path)
        run = self._make_run()
        await reporter.report(run)

        files = list(tmp_path.glob("report-*.html"))
        content = files[0].read_text(encoding="utf-8")
        assert "<style>" in content

    async def test_html_is_valid_structure(self, tmp_path: Path) -> None:
        reporter = HTMLReporter(output_dir=tmp_path)
        run = self._make_run()
        await reporter.report(run)

        files = list(tmp_path.glob("report-*.html"))
        content = files[0].read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in content
        assert "<html" in content
        assert "</html>" in content
        assert "<table>" in content

    async def test_empty_run(self, tmp_path: Path) -> None:
        reporter = HTMLReporter(output_dir=tmp_path)
        run = AgentRun(
            agent_name="empty",
            status=RunStatus.COMPLETED,
            total_tests=0,
        )
        await reporter.report(run)

        files = list(tmp_path.glob("report-*.html"))
        content = files[0].read_text(encoding="utf-8")
        assert "empty" in content

    def test_name_property(self) -> None:
        reporter = HTMLReporter()
        assert reporter.name == "html"
