"""Markdown reporter for test results.

Generates a Markdown file with tables and summary sections suitable
for rendering in GitHub, GitLab, or documentation systems.
"""

from __future__ import annotations

import logging
from pathlib import Path

from agentprobe.core.models import AgentRun

logger = logging.getLogger(__name__)

_STATUS_EMOJI: dict[str, str] = {
    "passed": "PASS",
    "failed": "FAIL",
    "error": "ERR",
    "timeout": "TOUT",
    "skipped": "SKIP",
    "pending": "PEND",
    "running": "RUN",
}


class MarkdownReporter:
    """Reporter that writes results as a Markdown file.

    Produces a Markdown document with a summary section and a results
    table, compatible with GitHub, GitLab, and other renderers.

    Attributes:
        output_dir: Directory to write report files to.
    """

    def __init__(self, output_dir: str | Path = "agentprobe-report") -> None:
        """Initialize the Markdown reporter.

        Args:
            output_dir: Directory for report output.
        """
        self._output_dir = Path(output_dir)

    @property
    def name(self) -> str:
        """Return the reporter name."""
        return "markdown"

    async def report(self, run: AgentRun) -> None:
        """Write the agent run as a Markdown file.

        Args:
            run: The completed agent run.
        """
        self._output_dir.mkdir(parents=True, exist_ok=True)
        output_path = self._output_dir / f"report-{run.run_id}.md"

        content = self._build_markdown(run)
        output_path.write_text(content, encoding="utf-8")
        logger.info("Markdown report written to %s", output_path)

    def _build_markdown(self, run: AgentRun) -> str:
        """Build the complete Markdown content.

        Args:
            run: The completed agent run.

        Returns:
            The full Markdown string.
        """
        lines: list[str] = []

        lines.append(f"# AgentProbe Test Report — {run.agent_name}")
        lines.append("")
        lines.append(f"**Status:** {run.status.value}")
        lines.append("")

        # Summary
        lines.append("## Summary")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Total Tests | {run.total_tests} |")
        lines.append(f"| Passed | {run.passed} |")
        lines.append(f"| Failed | {run.failed} |")
        lines.append(f"| Errors | {run.errors} |")
        lines.append(f"| Skipped | {run.skipped} |")
        lines.append(f"| Duration | {run.duration_ms}ms |")
        lines.append("")

        # Results table
        if run.test_results:
            lines.append("## Results")
            lines.append("")
            lines.append("| Test | Status | Score | Duration | Details |")
            lines.append("|------|--------|-------|----------|---------|")

            for result in run.test_results:
                status_label = _STATUS_EMOJI.get(result.status.value, result.status.value)
                details = ""
                if result.error_message:
                    details = result.error_message[:80]
                elif result.eval_results:
                    verdicts = [r.verdict.value for r in result.eval_results]
                    details = ", ".join(verdicts)

                lines.append(
                    f"| {result.test_name} | {status_label} | {result.score:.2f} "
                    f"| {result.duration_ms}ms | {details} |"
                )
            lines.append("")

        return "\n".join(lines)
