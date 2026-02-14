"""Tests for the safety CLI commands."""

from __future__ import annotations

from click.testing import CliRunner

from agentprobe.cli.main import cli


class TestSafetyCLI:
    """Tests for safety CLI commands."""

    def test_safety_help(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["safety", "--help"])
        assert result.exit_code == 0
        assert "safety" in result.output.lower()

    def test_safety_scan_help(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["safety", "scan", "--help"])
        assert result.exit_code == 0
        assert "--suite" in result.output

    def test_safety_list(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["safety", "list"])
        assert result.exit_code == 0

    def test_safety_scan_default(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["safety", "scan"])
        assert result.exit_code == 0

    def test_safety_scan_with_suite_filter(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["safety", "scan", "-s", "nonexistent-suite"])
        assert result.exit_code == 0
