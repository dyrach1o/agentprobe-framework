"""HTML reporter for test results.

Generates a standalone HTML file with embedded CSS for viewing
test results in a browser.
"""

from __future__ import annotations

import html
import logging
from pathlib import Path

from agentprobe.core.models import AgentRun, TestStatus

logger = logging.getLogger(__name__)

_STATUS_COLORS: dict[TestStatus, str] = {
    TestStatus.PASSED: "#22c55e",
    TestStatus.FAILED: "#ef4444",
    TestStatus.ERROR: "#dc2626",
    TestStatus.TIMEOUT: "#eab308",
    TestStatus.SKIPPED: "#9ca3af",
    TestStatus.PENDING: "#9ca3af",
    TestStatus.RUNNING: "#06b6d4",
}


class HTMLReporter:
    """Reporter that writes results as a standalone HTML file.

    Produces a single HTML file with embedded CSS, requiring no external
    dependencies for viewing.

    Attributes:
        output_dir: Directory to write report files to.
    """

    def __init__(self, output_dir: str | Path = "agentprobe-report") -> None:
        """Initialize the HTML reporter.

        Args:
            output_dir: Directory for report output.
        """
        self._output_dir = Path(output_dir)

    @property
    def name(self) -> str:
        """Return the reporter name."""
        return "html"

    async def report(self, run: AgentRun) -> None:
        """Write the agent run as an HTML file.

        Args:
            run: The completed agent run.
        """
        self._output_dir.mkdir(parents=True, exist_ok=True)
        output_path = self._output_dir / f"report-{run.run_id}.html"

        content = self._build_html(run)
        output_path.write_text(content, encoding="utf-8")
        logger.info("HTML report written to %s", output_path)

    def _build_html(self, run: AgentRun) -> str:
        """Build the complete HTML content.

        Args:
            run: The completed agent run.

        Returns:
            The full HTML string.
        """
        rows = self._build_rows(run)
        overall_color = "#22c55e" if run.failed == 0 and run.errors == 0 else "#ef4444"

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AgentProbe Report — {html.escape(run.agent_name)}</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
         max-width: 960px; margin: 2rem auto; padding: 0 1rem; background: #fafafa; color: #1a1a1a; }}
  h1 {{ margin-bottom: 0.5rem; }}
  .summary {{ display: flex; gap: 1.5rem; margin: 1rem 0; padding: 1rem;
              background: #fff; border-radius: 8px; border: 1px solid #e5e7eb; }}
  .summary .stat {{ text-align: center; }}
  .summary .stat .value {{ font-size: 1.5rem; font-weight: 700; }}
  .summary .stat .label {{ font-size: 0.8rem; color: #6b7280; text-transform: uppercase; }}
  table {{ width: 100%; border-collapse: collapse; background: #fff;
           border-radius: 8px; overflow: hidden; border: 1px solid #e5e7eb; }}
  th {{ background: #f9fafb; text-align: left; padding: 0.75rem 1rem;
       font-size: 0.8rem; text-transform: uppercase; color: #6b7280; border-bottom: 1px solid #e5e7eb; }}
  td {{ padding: 0.75rem 1rem; border-bottom: 1px solid #f3f4f6; }}
  .status {{ padding: 2px 8px; border-radius: 4px; color: #fff; font-size: 0.8rem; font-weight: 600; }}
</style>
</head>
<body>
<h1>AgentProbe Test Report</h1>
<p>Agent: <strong>{html.escape(run.agent_name)}</strong> —
   Status: <span style="color:{overall_color};font-weight:700">{html.escape(run.status.value)}</span></p>
<div class="summary">
  <div class="stat"><div class="value">{run.total_tests}</div><div class="label">Total</div></div>
  <div class="stat"><div class="value" style="color:#22c55e">{run.passed}</div><div class="label">Passed</div></div>
  <div class="stat"><div class="value" style="color:#ef4444">{run.failed}</div><div class="label">Failed</div></div>
  <div class="stat"><div class="value" style="color:#dc2626">{run.errors}</div><div class="label">Errors</div></div>
  <div class="stat"><div class="value">{run.duration_ms}ms</div><div class="label">Duration</div></div>
</div>
<table>
<thead><tr><th>Test</th><th>Status</th><th>Score</th><th>Duration</th><th>Details</th></tr></thead>
<tbody>
{rows}
</tbody>
</table>
</body>
</html>"""

    def _build_rows(self, run: AgentRun) -> str:
        """Build HTML table rows for test results.

        Args:
            run: The completed agent run.

        Returns:
            HTML string containing all table rows.
        """
        lines: list[str] = []
        for result in run.test_results:
            color = _STATUS_COLORS.get(result.status, "#6b7280")
            details = ""
            if result.error_message:
                details = html.escape(result.error_message[:100])
            elif result.eval_results:
                verdicts = [r.verdict.value for r in result.eval_results]
                details = html.escape(", ".join(verdicts))

            lines.append(
                f"<tr><td>{html.escape(result.test_name)}</td>"
                f'<td><span class="status" style="background:{color}">'
                f"{html.escape(result.status.value)}</span></td>"
                f"<td>{result.score:.2f}</td>"
                f"<td>{result.duration_ms}ms</td>"
                f"<td>{details}</td></tr>"
            )
        return "\n".join(lines)
