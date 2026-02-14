"""CLI commands for metrics listing and summary."""

from __future__ import annotations

import click

from agentprobe.metrics.definitions import get_builtin_definitions


@click.group("metrics")
def metrics_group() -> None:
    """View and manage metrics."""


@metrics_group.command("list")
def metrics_list() -> None:
    """List all built-in metric definitions.

    Shows the name, type, unit, and description of each metric.
    """
    definitions = get_builtin_definitions()
    click.echo("Built-in Metrics")
    click.echo("=" * 60)

    for defn in sorted(definitions.values(), key=lambda d: d.name):
        direction = "lower is better" if defn.lower_is_better else "higher is better"
        unit = defn.unit or "—"
        click.echo(f"\n  {defn.name}")
        click.echo(f"    Type:        {defn.metric_type.value}")
        click.echo(f"    Unit:        {unit}")
        click.echo(f"    Direction:   {direction}")
        click.echo(f"    Description: {defn.description}")

    click.echo(f"\nTotal: {len(definitions)} metrics")


@metrics_group.command("summary")
@click.option(
    "--metric",
    "-m",
    default=None,
    help="Filter by metric name.",
)
def metrics_summary(metric: str | None) -> None:
    """Show a summary of collected metrics.

    Displays aggregated statistics for collected metric values.
    """
    click.echo("Metrics Summary")
    click.echo("=" * 40)

    if metric:
        click.echo(f"Filter: {metric}")

    click.echo("\nRun tests first to generate metric data.")
    click.echo("Use the Python API for programmatic metrics:")
    click.echo("  from agentprobe.metrics.collector import MetricCollector")
    click.echo("  from agentprobe.metrics.aggregator import MetricAggregator")
    click.echo("  collector = MetricCollector()")
    click.echo("  metrics = collector.collect_from_run(run)")
