"""CLI commands for safety scanning."""

from __future__ import annotations

import click

from agentprobe.safety.scanner import get_registered_suites


@click.group("safety")
def safety_group() -> None:
    """Run safety scans against agents."""


@safety_group.command("scan")
@click.option(
    "--suite",
    "-s",
    "suite_names",
    multiple=True,
    help="Suite names to run (default: all registered suites).",
)
@click.option(
    "--severity",
    type=click.Choice(["low", "medium", "high", "critical"], case_sensitive=False),
    default=None,
    help="Filter suites by minimum severity level.",
)
def safety_scan(suite_names: tuple[str, ...], severity: str | None) -> None:
    """Run safety test suites against an agent."""
    registered = get_registered_suites()

    if not registered:
        click.echo("No safety suites registered.")
        return

    available_names = list(registered.keys())

    # Filter by suite names if specified
    if suite_names:
        selected = [name for name in suite_names if name in registered]
        if not selected:
            click.echo(f"No matching suites found for: {', '.join(suite_names)}")
            click.echo(f"Available: {', '.join(available_names)}")
            return
    else:
        selected = available_names

    click.echo(f"Running {len(selected)} safety suite(s):")
    for name in selected:
        click.echo(f"  - {name}")

    click.echo("\nSafety scan requires an adapter to test against.")
    click.echo("Use the Python API to run scans programmatically:")
    click.echo("  scanner = SafetyScanner()")
    click.echo("  results = await scanner.scan(adapter)")


@safety_group.command("list")
def safety_list() -> None:
    """List available safety test suites."""
    registered = get_registered_suites()

    if not registered:
        click.echo("No safety suites registered.")
        return

    click.echo(f"Available safety suites ({len(registered)}):")
    for name in registered:
        click.echo(f"  - {name}")
