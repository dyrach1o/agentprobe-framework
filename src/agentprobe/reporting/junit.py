"""JUnit XML reporter for test results.

Generates JUnit-compatible XML output suitable for CI/CD systems
like Jenkins, GitHub Actions, and GitLab CI.
"""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from pathlib import Path

from agentprobe.core.models import AgentRun, TestResult, TestStatus

logger = logging.getLogger(__name__)


class JUnitReporter:
    """Reporter that writes results as JUnit XML.

    Produces a standard JUnit XML file that can be consumed by CI/CD
    pipelines for test reporting and status visualization.

    Attributes:
        output_dir: Directory to write report files to.
    """

    def __init__(self, output_dir: str | Path = "agentprobe-report") -> None:
        """Initialize the JUnit reporter.

        Args:
            output_dir: Directory for report output.
        """
        self._output_dir = Path(output_dir)

    @property
    def name(self) -> str:
        """Return the reporter name."""
        return "junit"

    async def report(self, run: AgentRun) -> None:
        """Write the agent run as a JUnit XML file.

        Args:
            run: The completed agent run.
        """
        self._output_dir.mkdir(parents=True, exist_ok=True)
        output_path = self._output_dir / f"report-{run.run_id}.xml"

        root = self._build_xml(run)
        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ")
        tree.write(str(output_path), encoding="unicode", xml_declaration=True)
        logger.info("JUnit XML report written to %s", output_path)

    def _build_xml(self, run: AgentRun) -> ET.Element:
        """Build the JUnit XML element tree.

        Args:
            run: The completed agent run.

        Returns:
            The root XML element.
        """
        testsuite = ET.Element("testsuite")
        testsuite.set("name", run.agent_name)
        testsuite.set("tests", str(run.total_tests))
        testsuite.set("failures", str(run.failed))
        testsuite.set("errors", str(run.errors))
        testsuite.set("skipped", str(run.skipped))
        testsuite.set("time", f"{run.duration_ms / 1000:.3f}")

        for result in run.test_results:
            testcase = self._build_testcase(result, run.agent_name)
            testsuite.append(testcase)

        return testsuite

    def _build_testcase(self, result: TestResult, suite_name: str) -> ET.Element:
        """Build a testcase XML element.

        Args:
            result: A single test result.
            suite_name: The parent test suite name.

        Returns:
            A testcase XML element.
        """
        testcase = ET.Element("testcase")
        testcase.set("name", result.test_name)
        testcase.set("classname", suite_name)
        testcase.set("time", f"{result.duration_ms / 1000:.3f}")

        if result.status == TestStatus.FAILED:
            failure = ET.SubElement(testcase, "failure")
            failure.set("message", result.error_message or "Test failed")
            failure.set("type", "AssertionError")
            if result.eval_results:
                failure.text = "\n".join(
                    f"{er.evaluator_name}: {er.verdict.value} ({er.score:.2f}) - {er.reason}"
                    for er in result.eval_results
                )

        elif result.status == TestStatus.ERROR:
            error = ET.SubElement(testcase, "error")
            error.set("message", result.error_message or "Test error")
            error.set("type", "RuntimeError")

        elif result.status == TestStatus.SKIPPED:
            skipped = ET.SubElement(testcase, "skipped")
            skipped.set("message", result.error_message or "Test skipped")

        return testcase
