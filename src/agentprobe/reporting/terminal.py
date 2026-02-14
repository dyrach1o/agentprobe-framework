"""Terminal reporter using Rich for formatted output.

Produces colored tables, progress summaries, and status panels
for agent test runs.
"""

from __future__ import annotations

import logging

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from agentprobe.core.models import AgentRun, TestStatus

logger = logging.getLogger(__name__)

_STATUS_COLORS: dict[TestStatus, str] = {
    TestStatus.PASSED: "green",
    TestStatus.FAILED: "red",
    TestStatus.ERROR: "red bold",
    TestStatus.TIMEOUT: "yellow",
    TestStatus.SKIPPED: "dim",
    TestStatus.PENDING: "dim",
    TestStatus.RUNNING: "cyan",
}


class TerminalReporter:
    """Reporter that outputs formatted results to the terminal.

    Uses Rich for colored tables, panels, and progress indicators.

    Attributes:
        console: Rich Console instance for output.
    """

    def __init__(self, console: Console | None = None) -> None:
        """Initialize the terminal reporter.

        Args:
            console: Rich Console to use. Creates a new one if None.
        """
        self._console = console or Console()

    @property
    def name(self) -> str:
        """Return the reporter name."""
        return "terminal"

    async def report(self, run: AgentRun) -> None:
        """Print a formatted test run report to the terminal.

        Args:
            run: The completed agent run.
        """
        self._print_header(run)
        self._print_results_table(run)
        self._print_summary(run)

    def _print_header(self, run: AgentRun) -> None:
        """Print the report header with agent name and status."""
        status_color = "green" if run.failed == 0 and run.errors == 0 else "red"
        self._console.print(
            Panel(
                f"[bold]{run.agent_name}[/bold] — {run.status.value}",
                title="AgentProbe Test Report",
                border_style=status_color,
            )
        )

    def _print_results_table(self, run: AgentRun) -> None:
        """Print a table of individual test results."""
        if not run.test_results:
            self._console.print("[dim]No test results.[/dim]")
            return

        table = Table(show_header=True, header_style="bold")
        table.add_column("Test", style="cyan", min_width=20)
        table.add_column("Status", justify="center", min_width=10)
        table.add_column("Score", justify="right", min_width=8)
        table.add_column("Duration", justify="right", min_width=10)
        table.add_column("Details", min_width=20)

        for result in run.test_results:
            color = _STATUS_COLORS.get(result.status, "white")
            details = ""
            if result.error_message:
                details = result.error_message[:50]
            elif result.eval_results:
                verdicts = [r.verdict.value for r in result.eval_results]
                details = ", ".join(verdicts)

            table.add_row(
                result.test_name,
                f"[{color}]{result.status.value}[/{color}]",
                f"{result.score:.2f}",
                f"{result.duration_ms}ms",
                details,
            )

        self._console.print(table)

    def _print_summary(self, run: AgentRun) -> None:
        """Print a summary panel with totals."""
        parts = [
            f"Total: {run.total_tests}",
            f"[green]Passed: {run.passed}[/green]",
            f"[red]Failed: {run.failed}[/red]",
        ]
        if run.errors > 0:
            parts.append(f"[red bold]Errors: {run.errors}[/red bold]")
        if run.skipped > 0:
            parts.append(f"[dim]Skipped: {run.skipped}[/dim]")
        parts.append(f"Duration: {run.duration_ms}ms")

        self._console.print()
        self._console.print(" | ".join(parts))
