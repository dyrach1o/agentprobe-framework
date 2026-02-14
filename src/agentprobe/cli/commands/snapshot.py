"""CLI commands for managing trace snapshots."""

from __future__ import annotations

from pathlib import Path

import click

from agentprobe.core.exceptions import SnapshotError
from agentprobe.core.snapshot import SnapshotManager


@click.group("snapshot")
def snapshot_group() -> None:
    """Manage trace snapshots for golden-file testing."""


@snapshot_group.command("list")
@click.option(
    "--dir",
    "-d",
    "snapshots_dir",
    default=".agentprobe/snapshots",
    help="Directory containing snapshots.",
)
def snapshot_list(snapshots_dir: str) -> None:
    """List all saved snapshots."""
    manager = SnapshotManager(Path(snapshots_dir))
    names = manager.list_snapshots()

    if not names:
        click.echo("No snapshots found.")
        return

    click.echo(f"Snapshots ({len(names)}):")
    for name in sorted(names):
        click.echo(f"  - {name}")


@snapshot_group.command("delete")
@click.argument("name")
@click.option(
    "--dir",
    "-d",
    "snapshots_dir",
    default=".agentprobe/snapshots",
    help="Directory containing snapshots.",
)
@click.confirmation_option(prompt="Are you sure you want to delete this snapshot?")
def snapshot_delete(name: str, snapshots_dir: str) -> None:
    """Delete a saved snapshot."""
    manager = SnapshotManager(Path(snapshots_dir))
    deleted = manager.delete(name)

    if deleted:
        click.echo(f"Deleted snapshot: {name}")
    else:
        click.echo(f"Snapshot not found: {name}")


@snapshot_group.command("diff")
@click.argument("name")
@click.option(
    "--dir",
    "-d",
    "snapshots_dir",
    default=".agentprobe/snapshots",
    help="Directory containing snapshots.",
)
def snapshot_diff(name: str, snapshots_dir: str) -> None:
    """Show diff information for a snapshot.

    Compares the current snapshot against its saved state.
    Requires running tests first to generate a current trace.
    """
    manager = SnapshotManager(Path(snapshots_dir))
    try:
        existing = manager.load(name)
    except SnapshotError:
        click.echo(f"Snapshot not found: {name}")
        return

    click.echo(f"Snapshot: {name}")
    click.echo(f"  Agent: {existing.agent_name}")
    click.echo(f"  Tool calls: {len(existing.tool_calls)}")
    click.echo(f"  Tokens: {existing.total_input_tokens} in / {existing.total_output_tokens} out")
    click.echo("\nRun tests to generate a new trace for comparison.")
