"""CLI commands for managing regression baselines."""

from __future__ import annotations

from pathlib import Path

import click

from agentprobe.regression.baseline import BaselineManager


@click.group("baseline")
def baseline_group() -> None:
    """Manage regression testing baselines."""


@baseline_group.command("list")
@click.option(
    "--dir",
    "-d",
    "baselines_dir",
    default=".agentprobe/baselines",
    help="Directory containing baselines.",
)
def baseline_list(baselines_dir: str) -> None:
    """List all saved baselines."""
    manager = BaselineManager(Path(baselines_dir))
    names = manager.list_baselines()

    if not names:
        click.echo("No baselines found.")
        return

    click.echo(f"Baselines ({len(names)}):")
    for name in sorted(names):
        click.echo(f"  - {name}")


@baseline_group.command("delete")
@click.argument("name")
@click.option(
    "--dir",
    "-d",
    "baselines_dir",
    default=".agentprobe/baselines",
    help="Directory containing baselines.",
)
@click.confirmation_option(prompt="Are you sure you want to delete this baseline?")
def baseline_delete(name: str, baselines_dir: str) -> None:
    """Delete a saved baseline."""
    manager = BaselineManager(Path(baselines_dir))
    deleted = manager.delete(name)

    if deleted:
        click.echo(f"Deleted baseline: {name}")
    else:
        click.echo(f"Baseline not found: {name}")


@baseline_group.command("create")
@click.argument("name")
@click.option(
    "--dir",
    "-d",
    "baselines_dir",
    default=".agentprobe/baselines",
    help="Directory for baselines.",
)
def baseline_create(name: str, baselines_dir: str) -> None:
    """Create a new baseline from the latest test run.

    This command creates the baseline entry. Populate it by running tests
    and saving results programmatically via the Python API.
    """
    manager = BaselineManager(Path(baselines_dir))
    manager.save(name, [])
    click.echo(f"Created empty baseline: {name}")
    click.echo("Run tests and save results via the Python API to populate it.")
