"""Tests for the baseline CLI commands."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from agentprobe.cli.main import cli


class TestBaselineCLI:
    """Tests for baseline CLI commands."""

    def test_baseline_help(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["baseline", "--help"])
        assert result.exit_code == 0
        assert "baseline" in result.output.lower()

    def test_baseline_list_empty(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["baseline", "list", "-d", str(tmp_path / "baselines")])
        assert result.exit_code == 0
        assert "No baselines" in result.output

    def test_baseline_create_and_list(self, tmp_path: Path) -> None:
        baselines_dir = str(tmp_path / "baselines")
        runner = CliRunner()

        # Create a baseline
        result = runner.invoke(cli, ["baseline", "create", "v1", "-d", baselines_dir])
        assert result.exit_code == 0
        assert "Created" in result.output

        # List should show it
        result = runner.invoke(cli, ["baseline", "list", "-d", baselines_dir])
        assert result.exit_code == 0
        assert "v1" in result.output

    def test_baseline_delete(self, tmp_path: Path) -> None:
        baselines_dir = str(tmp_path / "baselines")
        runner = CliRunner()

        # Create first
        runner.invoke(cli, ["baseline", "create", "v1", "-d", baselines_dir])

        # Delete with confirmation
        result = runner.invoke(cli, ["baseline", "delete", "v1", "-d", baselines_dir, "--yes"])
        assert result.exit_code == 0
        assert "Deleted" in result.output

    def test_baseline_delete_not_found(self, tmp_path: Path) -> None:
        baselines_dir = str(tmp_path / "baselines")
        runner = CliRunner()
        result = runner.invoke(
            cli, ["baseline", "delete", "nonexistent", "-d", baselines_dir, "--yes"]
        )
        assert result.exit_code == 0
        assert "not found" in result.output
