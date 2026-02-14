"""Tests for the JUnitReporter."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from agentprobe.core.models import AgentRun, EvalVerdict, RunStatus, TestStatus
from agentprobe.reporting.junit import JUnitReporter
from tests.fixtures.results import make_eval_result, make_test_result


class TestJUnitReporter:
    """Tests for JUnitReporter XML output."""

    def _make_run(
        self,
        results: list[tuple[str, TestStatus]] | None = None,
    ) -> AgentRun:
        test_results = []
        passed = 0
        failed = 0
        errors = 0
        skipped = 0

        for name, status in results or []:
            kwargs = {"test_name": name, "status": status}
            if status == TestStatus.FAILED:
                kwargs["error_message"] = f"{name} failed"
                kwargs["score"] = 0.3
                kwargs["eval_results"] = [
                    make_eval_result(verdict=EvalVerdict.FAIL, score=0.3, reason="low score")
                ]
                failed += 1
            elif status == TestStatus.ERROR:
                kwargs["error_message"] = f"{name} error"
                errors += 1
            elif status == TestStatus.SKIPPED:
                skipped += 1
            else:
                passed += 1
            test_results.append(make_test_result(**kwargs))

        return AgentRun(
            agent_name="test-agent",
            status=RunStatus.COMPLETED,
            test_results=tuple(test_results),
            total_tests=len(test_results),
            passed=passed,
            failed=failed,
            errors=errors,
            skipped=skipped,
            duration_ms=500,
        )

    async def test_creates_xml_file(self, tmp_path: Path) -> None:
        reporter = JUnitReporter(output_dir=tmp_path)
        run = self._make_run([("test_a", TestStatus.PASSED)])
        await reporter.report(run)

        files = list(tmp_path.glob("report-*.xml"))
        assert len(files) == 1

    async def test_xml_structure(self, tmp_path: Path) -> None:
        reporter = JUnitReporter(output_dir=tmp_path)
        run = self._make_run(
            [
                ("test_a", TestStatus.PASSED),
                ("test_b", TestStatus.FAILED),
            ]
        )
        await reporter.report(run)

        files = list(tmp_path.glob("report-*.xml"))
        tree = ET.parse(str(files[0]))
        root = tree.getroot()

        assert root.tag == "testsuite"
        assert root.get("name") == "test-agent"
        assert root.get("tests") == "2"
        assert root.get("failures") == "1"
        testcases = root.findall("testcase")
        assert len(testcases) == 2

    async def test_failed_test_has_failure_element(self, tmp_path: Path) -> None:
        reporter = JUnitReporter(output_dir=tmp_path)
        run = self._make_run([("test_fail", TestStatus.FAILED)])
        await reporter.report(run)

        files = list(tmp_path.glob("report-*.xml"))
        tree = ET.parse(str(files[0]))
        tc = tree.getroot().find("testcase")
        assert tc is not None
        failure = tc.find("failure")
        assert failure is not None
        assert "test_fail failed" in (failure.get("message") or "")

    async def test_error_test_has_error_element(self, tmp_path: Path) -> None:
        reporter = JUnitReporter(output_dir=tmp_path)
        run = self._make_run([("test_err", TestStatus.ERROR)])
        await reporter.report(run)

        files = list(tmp_path.glob("report-*.xml"))
        tree = ET.parse(str(files[0]))
        tc = tree.getroot().find("testcase")
        assert tc is not None
        error = tc.find("error")
        assert error is not None

    async def test_skipped_test_has_skipped_element(self, tmp_path: Path) -> None:
        reporter = JUnitReporter(output_dir=tmp_path)
        run = self._make_run([("test_skip", TestStatus.SKIPPED)])
        await reporter.report(run)

        files = list(tmp_path.glob("report-*.xml"))
        tree = ET.parse(str(files[0]))
        tc = tree.getroot().find("testcase")
        assert tc is not None
        skipped = tc.find("skipped")
        assert skipped is not None

    async def test_empty_run(self, tmp_path: Path) -> None:
        reporter = JUnitReporter(output_dir=tmp_path)
        run = self._make_run([])
        await reporter.report(run)

        files = list(tmp_path.glob("report-*.xml"))
        tree = ET.parse(str(files[0]))
        root = tree.getroot()
        assert root.get("tests") == "0"
        assert len(root.findall("testcase")) == 0

    def test_name_property(self) -> None:
        reporter = JUnitReporter()
        assert reporter.name == "junit"

    async def test_duration_in_seconds(self, tmp_path: Path) -> None:
        reporter = JUnitReporter(output_dir=tmp_path)
        run = self._make_run([("test_a", TestStatus.PASSED)])
        await reporter.report(run)

        files = list(tmp_path.glob("report-*.xml"))
        tree = ET.parse(str(files[0]))
        root = tree.getroot()
        assert root.get("time") == "0.500"
