"""Integration test: CLI commands via Click CliRunner."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from agentprobe.cli.main import cli


@pytest.mark.integration
class TestCLIEndToEnd:
    """End-to-end CLI command tests."""

    def test_version(self) -> None:
        """agentprobe --version prints version."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "version" in result.output.lower() or "." in result.output

    def test_help(self) -> None:
        """agentprobe --help shows all commands."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "test" in result.output
        assert "trace" in result.output
        assert "safety" in result.output

    def test_init_creates_config(self, tmp_path: pytest.TempPathFactory) -> None:
        """agentprobe init creates a config file."""
        runner = CliRunner()
        config_path = str(tmp_path) + "/agentprobe.yaml"  # type: ignore[operator]
        result = runner.invoke(cli, ["init", "-o", config_path])
        assert result.exit_code == 0
        assert "Created" in result.output

    def test_init_existing_config_no_overwrite(self, tmp_path: pytest.TempPathFactory) -> None:
        """agentprobe init doesn't overwrite existing config."""
        runner = CliRunner()
        config_path = str(tmp_path) + "/agentprobe.yaml"  # type: ignore[operator]
        # Create first
        runner.invoke(cli, ["init", "-o", config_path])
        # Try again
        result = runner.invoke(cli, ["init", "-o", config_path])
        assert result.exit_code == 0
        assert "already exists" in result.output

    def test_test_help(self) -> None:
        """agentprobe test --help shows test command."""
        runner = CliRunner()
        result = runner.invoke(cli, ["test", "--help"])
        assert result.exit_code == 0

    def test_trace_help(self) -> None:
        """agentprobe trace --help shows trace subcommands."""
        runner = CliRunner()
        result = runner.invoke(cli, ["trace", "--help"])
        assert result.exit_code == 0

    def test_safety_help(self) -> None:
        """agentprobe safety --help shows safety subcommands."""
        runner = CliRunner()
        result = runner.invoke(cli, ["safety", "--help"])
        assert result.exit_code == 0

    def test_baseline_help(self) -> None:
        """agentprobe baseline --help shows baseline subcommands."""
        runner = CliRunner()
        result = runner.invoke(cli, ["baseline", "--help"])
        assert result.exit_code == 0

    def test_cost_help(self) -> None:
        """agentprobe cost --help shows cost subcommands."""
        runner = CliRunner()
        result = runner.invoke(cli, ["cost", "--help"])
        assert result.exit_code == 0

    def test_cost_report(self) -> None:
        """agentprobe cost report produces output."""
        runner = CliRunner()
        result = runner.invoke(cli, ["cost", "report"])
        assert result.exit_code == 0
        assert "Cost" in result.output

    def test_cost_budget(self) -> None:
        """agentprobe cost budget produces output."""
        runner = CliRunner()
        result = runner.invoke(cli, ["cost", "budget"])
        assert result.exit_code == 0
        assert "Budget" in result.output

    def test_snapshot_help(self) -> None:
        """agentprobe snapshot --help shows snapshot subcommands."""
        runner = CliRunner()
        result = runner.invoke(cli, ["snapshot", "--help"])
        assert result.exit_code == 0

    def test_unknown_command(self) -> None:
        """Unknown command produces error."""
        runner = CliRunner()
        result = runner.invoke(cli, ["nonexistent"])
        assert result.exit_code != 0
