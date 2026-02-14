"""CSV reporter for test results.

Writes test results as a CSV file for easy import into spreadsheets
and data analysis tools.
"""

from __future__ import annotations

import csv
import io
import logging
from pathlib import Path

from agentprobe.core.models import AgentRun

logger = logging.getLogger(__name__)

_CSV_HEADERS = [
    "test_name",
    "status",
    "score",
    "duration_ms",
    "error_message",
    "eval_verdicts",
]


class CSVReporter:
    """Reporter that writes results as a CSV file.

    Produces a CSV file with one row per test result, suitable for
    import into spreadsheets and data analysis pipelines.

    Attributes:
        output_dir: Directory to write report files to.
    """

    def __init__(self, output_dir: str | Path = "agentprobe-report") -> None:
        """Initialize the CSV reporter.

        Args:
            output_dir: Directory for report output.
        """
        self._output_dir = Path(output_dir)

    @property
    def name(self) -> str:
        """Return the reporter name."""
        return "csv"

    async def report(self, run: AgentRun) -> None:
        """Write the agent run as a CSV file.

        Args:
            run: The completed agent run.
        """
        self._output_dir.mkdir(parents=True, exist_ok=True)
        output_path = self._output_dir / f"report-{run.run_id}.csv"

        content = self._build_csv(run)
        output_path.write_text(content, encoding="utf-8")
        logger.info("CSV report written to %s", output_path)

    def _build_csv(self, run: AgentRun) -> str:
        """Build the CSV content as a string.

        Args:
            run: The completed agent run.

        Returns:
            The complete CSV string with headers and data rows.
        """
        output = io.StringIO(newline="")
        writer = csv.writer(output)
        writer.writerow(_CSV_HEADERS)

        for result in run.test_results:
            eval_verdicts = ""
            if result.eval_results:
                verdicts = [r.verdict.value for r in result.eval_results]
                eval_verdicts = "; ".join(verdicts)

            writer.writerow(
                [
                    result.test_name,
                    result.status.value,
                    f"{result.score:.4f}",
                    str(result.duration_ms),
                    result.error_message or "",
                    eval_verdicts,
                ]
            )

        return output.getvalue()
