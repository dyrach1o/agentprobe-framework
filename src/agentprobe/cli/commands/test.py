"""CLI command for running agent tests."""

from __future__ import annotations

import click

from agentprobe.core.config import load_config
from agentprobe.core.discovery import extract_test_cases


@click.command("test")
@click.option(
    "--config",
    "-c",
    "config_path",
    default=None,
    help="Path to agentprobe.yaml config file.",
)
@click.option(
    "--test-dir",
    "-d",
    default=None,
    help="Directory containing test files.",
)
@click.option(
    "--pattern",
    "-p",
    default="test_*.py",
    help="Glob pattern for test files.",
)
@click.option(
    "--parallel/--sequential",
    default=None,
    help="Run tests in parallel or sequentially.",
)
def test_cmd(
    config_path: str | None,
    test_dir: str | None,
    pattern: str,
    parallel: bool | None,
) -> None:
    """Discover and run agent test scenarios."""
    config = load_config(config_path)

    if test_dir:
        config.test_dir = test_dir
    if parallel is not None:
        config.runner.parallel = parallel

    test_cases = extract_test_cases(config.test_dir, pattern)

    if not test_cases:
        click.echo("No test cases found.")
        return

    click.echo(f"Discovered {len(test_cases)} test case(s)")

    for tc in test_cases:
        tags = ", ".join(tc.tags) if tc.tags else "none"
        click.echo(f"  - {tc.name} [tags: {tags}]")
