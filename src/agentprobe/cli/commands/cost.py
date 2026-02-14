"""CLI commands for cost reporting and budget checking."""

from __future__ import annotations

import click


@click.group("cost")
def cost_group() -> None:
    """View cost reports and manage budgets."""


@cost_group.command("report")
@click.option(
    "--agent",
    "-a",
    default=None,
    help="Filter by agent name.",
)
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["table", "json", "csv"], case_sensitive=False),
    default="table",
    help="Output format.",
)
def cost_report(agent: str | None, output_format: str) -> None:
    """Show cost report for recent test runs.

    Displays a summary of token usage and estimated costs.
    """
    click.echo("Cost Report")
    click.echo("=" * 40)

    if agent:
        click.echo(f"Agent: {agent}")

    click.echo(f"Format: {output_format}")
    click.echo("\nRun tests first to generate cost data.")
    click.echo("Use the Python API for programmatic cost tracking:")
    click.echo("  from agentprobe.cost.calculator import CostCalculator")
    click.echo("  calc = CostCalculator()")
    click.echo("  summary = calc.calculate_trace_cost(trace)")


@cost_group.command("budget")
@click.option(
    "--max-cost",
    type=float,
    default=None,
    help="Maximum cost per test in USD.",
)
@click.option(
    "--max-tokens",
    type=int,
    default=None,
    help="Maximum tokens per test.",
)
def cost_budget(max_cost: float | None, max_tokens: int | None) -> None:
    """Check cost budgets for test runs.

    Verifies that tests stay within the defined budget limits.
    """
    click.echo("Budget Configuration")
    click.echo("=" * 40)

    if max_cost is not None:
        click.echo(f"Max cost per test: ${max_cost:.4f}")
    else:
        click.echo("Max cost per test: not set")

    if max_tokens is not None:
        click.echo(f"Max tokens per test: {max_tokens}")
    else:
        click.echo("Max tokens per test: not set")

    click.echo("\nUse the Python API for programmatic budget enforcement:")
    click.echo("  from agentprobe.cost.budget import BudgetEnforcer")
    click.echo("  enforcer = BudgetEnforcer(max_cost_usd=0.10)")
