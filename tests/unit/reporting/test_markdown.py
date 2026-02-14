"""Tests for the MarkdownReporter."""

from __future__ import annotations

from pathlib import Path

from agentprobe.core.models import AgentRun, RunStatus, TestStatus
from agentprobe.reporting.markdown import MarkdownReporter
from tests.fixtures.results import make_test_result


class TestMarkdownReporter:
    """Tests for MarkdownReporter Markdown output."""

    def _make_run(self) -> AgentRun:
        return AgentRun(
            agent_name="test-agent",
            status=RunStatus.COMPLETED,
            total_tests=2,
            passed=1,
            failed=1,
            duration_ms=500,
            test_results=(
                make_test_result(test_name="test_pass", status=TestStatus.PASSED),
                make_test_result(
                    test_name="test_fail",
                    status=TestStatus.FAILED,
                    score=0.2,
                    error_message="something went wrong",
                ),
            ),
        )

    async def test_creates_md_file(self, tmp_path: Path) -> None:
        reporter = MarkdownReporter(output_dir=tmp_path)
        run = self._make_run()
        await reporter.report(run)

        files = list(tmp_path.glob("report-*.md"))
        assert len(files) == 1

    async def test_contains_title(self, tmp_path: Path) -> None:
        reporter = MarkdownReporter(output_dir=tmp_path)
        run = self._make_run()
        await reporter.report(run)

        files = list(tmp_path.glob("report-*.md"))
        content = files[0].read_text(encoding="utf-8")
        assert "# AgentProbe Test Report" in content
        assert "test-agent" in content

    async def test_contains_summary_table(self, tmp_path: Path) -> None:
        reporter = MarkdownReporter(output_dir=tmp_path)
        run = self._make_run()
        await reporter.report(run)

        files = list(tmp_path.glob("report-*.md"))
        content = files[0].read_text(encoding="utf-8")
        assert "## Summary" in content
        assert "Total Tests" in content
        assert "| 2 |" in content

    async def test_contains_results_table(self, tmp_path: Path) -> None:
        reporter = MarkdownReporter(output_dir=tmp_path)
        run = self._make_run()
        await reporter.report(run)

        files = list(tmp_path.glob("report-*.md"))
        content = files[0].read_text(encoding="utf-8")
        assert "## Results" in content
        assert "test_pass" in content
        assert "test_fail" in content
        assert "PASS" in content
        assert "FAIL" in content

    async def test_empty_run_no_results_section(self, tmp_path: Path) -> None:
        reporter = MarkdownReporter(output_dir=tmp_path)
        run = AgentRun(
            agent_name="empty",
            status=RunStatus.COMPLETED,
            total_tests=0,
        )
        await reporter.report(run)

        files = list(tmp_path.glob("report-*.md"))
        content = files[0].read_text(encoding="utf-8")
        assert "## Summary" in content
        assert "## Results" not in content

    def test_name_property(self) -> None:
        reporter = MarkdownReporter()
        assert reporter.name == "markdown"
