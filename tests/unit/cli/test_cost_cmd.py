"""Tests for the cost CLI commands."""

from __future__ import annotations

from click.testing import CliRunner

from agentprobe.cli.main import cli


class TestCostCLI:
    """Tests for cost CLI commands."""

    def test_cost_help(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["cost", "--help"])
        assert result.exit_code == 0
        assert "cost" in result.output.lower()

    def test_cost_report_default(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["cost", "report"])
        assert result.exit_code == 0
        assert "Cost Report" in result.output

    def test_cost_report_with_agent(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["cost", "report", "-a", "my-agent"])
        assert result.exit_code == 0
        assert "my-agent" in result.output

    def test_cost_report_json_format(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["cost", "report", "-f", "json"])
        assert result.exit_code == 0
        assert "json" in result.output.lower()

    def test_cost_budget_default(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["cost", "budget"])
        assert result.exit_code == 0
        assert "Budget" in result.output

    def test_cost_budget_with_limits(self) -> None:
        runner = CliRunner()
        result = runner.invoke(
            cli, ["cost", "budget", "--max-cost", "0.50", "--max-tokens", "1000"]
        )
        assert result.exit_code == 0
        assert "$0.5000" in result.output
        assert "1000" in result.output
