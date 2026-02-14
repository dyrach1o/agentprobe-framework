"""CLI entry point and command group for AgentProbe.

Registers all sub-commands and provides the ``agentprobe`` command.
"""

from __future__ import annotations

from pathlib import Path

import click

from agentprobe.cli.commands.baseline import baseline_group
from agentprobe.cli.commands.cost import cost_group
from agentprobe.cli.commands.dashboard import dashboard_cmd
from agentprobe.cli.commands.metrics import metrics_group
from agentprobe.cli.commands.safety import safety_group
from agentprobe.cli.commands.snapshot import snapshot_group
from agentprobe.cli.commands.test import test_cmd
from agentprobe.cli.commands.trace import trace_group


@click.group()
@click.version_option(package_name="agentprobe")
def cli() -> None:
    """AgentProbe — a testing and evaluation framework for software agents."""


@cli.command("init")
@click.option(
    "--output",
    "-o",
    default="agentprobe.yaml",
    help="Output file path for the config.",
)
def init_cmd(output: str) -> None:
    """Initialize a new AgentProbe configuration file."""
    path = Path(output)
    if path.exists():
        click.echo(f"Config file already exists: {path}")
        return

    template = """\
# AgentProbe Configuration
# See https://dyrach1o.github.io/agentprobe-framework/reference/config/ for full reference.

project_name: my-project
test_dir: tests

runner:
  parallel: false
  max_workers: 4
  default_timeout: 30.0

eval:
  default_evaluators: []

judge:
  model: claude-sonnet-4-5-20250929
  provider: anthropic
  temperature: 0.0
  max_tokens: 1024

trace:
  enabled: true
  storage_backend: sqlite
  database_path: .agentprobe/traces.db

cost:
  enabled: true

safety:
  enabled: true
  suites:
    - prompt-injection
    - data-exfiltration

reporting:
  formats:
    - terminal
  output_dir: agentprobe-report

chaos:
  enabled: false
  seed: null
  default_probability: 0.1

snapshot:
  enabled: false
  snapshot_dir: .agentprobe/snapshots
  update_on_first_run: true
  threshold: 0.8

budget:
  test_budget_usd: 1.00
  suite_budget_usd: 10.00

regression:
  enabled: false
  baseline_dir: .agentprobe/baselines
  threshold: 0.05

metrics:
  enabled: true
  builtin_metrics:
    - latency_ms
    - token_count
    - cost_usd
    - eval_score
    - tool_call_count
    - error_rate
  trend_window: 10

plugins:
  enabled: false
  directories: []
  entry_point_group: agentprobe.plugins
"""
    path.write_text(template, encoding="utf-8")
    click.echo(f"Created config file: {path}")


cli.add_command(test_cmd)
cli.add_command(trace_group)
cli.add_command(safety_group)
cli.add_command(baseline_group)
cli.add_command(snapshot_group)
cli.add_command(cost_group)
cli.add_command(metrics_group)
cli.add_command(dashboard_cmd)


def main() -> None:
    """Entry point for the CLI."""
    cli()
