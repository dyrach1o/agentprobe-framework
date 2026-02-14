"""Tests for the CSVReporter."""

from __future__ import annotations

import csv
from pathlib import Path

from agentprobe.core.models import AgentRun, EvalVerdict, RunStatus, TestStatus
from agentprobe.reporting.csv_reporter import CSVReporter
from tests.fixtures.results import make_eval_result, make_test_result


def _read_csv(path: Path) -> list[list[str]]:
    """Read a CSV file and return non-empty rows."""
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        return [row for row in reader if row]


class TestCSVReporter:
    """Tests for CSVReporter CSV output."""

    def _make_run(self) -> AgentRun:
        return AgentRun(
            agent_name="test-agent",
            status=RunStatus.COMPLETED,
            total_tests=3,
            passed=2,
            failed=1,
            duration_ms=500,
            test_results=(
                make_test_result(test_name="test_a", status=TestStatus.PASSED, score=1.0),
                make_test_result(
                    test_name="test_b",
                    status=TestStatus.FAILED,
                    score=0.3,
                    error_message="low score",
                    eval_results=[
                        make_eval_result(verdict=EvalVerdict.FAIL, score=0.3),
                    ],
                ),
                make_test_result(test_name="test_c", status=TestStatus.PASSED, score=0.9),
            ),
        )

    async def test_creates_csv_file(self, tmp_path: Path) -> None:
        reporter = CSVReporter(output_dir=tmp_path)
        run = self._make_run()
        await reporter.report(run)

        files = list(tmp_path.glob("report-*.csv"))
        assert len(files) == 1

    async def test_csv_headers(self, tmp_path: Path) -> None:
        reporter = CSVReporter(output_dir=tmp_path)
        run = self._make_run()
        await reporter.report(run)

        files = list(tmp_path.glob("report-*.csv"))
        rows = _read_csv(files[0])
        headers = rows[0]
        assert "test_name" in headers
        assert "status" in headers
        assert "score" in headers
        assert "duration_ms" in headers

    async def test_csv_row_count(self, tmp_path: Path) -> None:
        reporter = CSVReporter(output_dir=tmp_path)
        run = self._make_run()
        await reporter.report(run)

        files = list(tmp_path.glob("report-*.csv"))
        rows = _read_csv(files[0])
        assert len(rows) == 4  # 1 header + 3 data rows

    async def test_csv_values(self, tmp_path: Path) -> None:
        reporter = CSVReporter(output_dir=tmp_path)
        run = self._make_run()
        await reporter.report(run)

        files = list(tmp_path.glob("report-*.csv"))
        rows = _read_csv(files[0])

        # First data row
        assert rows[1][0] == "test_a"
        assert rows[1][1] == "passed"
        assert rows[1][2] == "1.0000"

        # Second data row (failed)
        assert rows[2][0] == "test_b"
        assert rows[2][1] == "failed"
        assert rows[2][4] == "low score"

    async def test_csv_eval_verdicts(self, tmp_path: Path) -> None:
        reporter = CSVReporter(output_dir=tmp_path)
        run = self._make_run()
        await reporter.report(run)

        files = list(tmp_path.glob("report-*.csv"))
        rows = _read_csv(files[0])

        # Second data row should have eval verdicts
        assert "fail" in rows[2][5]

    async def test_empty_run(self, tmp_path: Path) -> None:
        reporter = CSVReporter(output_dir=tmp_path)
        run = AgentRun(
            agent_name="empty",
            status=RunStatus.COMPLETED,
            total_tests=0,
        )
        await reporter.report(run)

        files = list(tmp_path.glob("report-*.csv"))
        rows = _read_csv(files[0])
        assert len(rows) == 1  # Only header

    def test_name_property(self) -> None:
        reporter = CSVReporter()
        assert reporter.name == "csv"
