"""Tests for the CLI entry point."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

import agentprobe
from agentprobe.cli.main import cli


class TestCLI:
    """Tests for the CLI commands using Click's test runner."""

    def test_version(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "1.0.0" in result.output

    def test_help(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "AgentProbe" in result.output

    def test_init_creates_config(self, tmp_path: Path) -> None:
        output_path = tmp_path / "agentprobe.yaml"
        runner = CliRunner()
        result = runner.invoke(cli, ["init", "-o", str(output_path)])
        assert result.exit_code == 0
        assert output_path.exists()
        content = output_path.read_text()
        assert "project_name" in content

    def test_init_template_includes_all_config_sections(self, tmp_path: Path) -> None:
        output_path = tmp_path / "agentprobe.yaml"
        runner = CliRunner()
        runner.invoke(cli, ["init", "-o", str(output_path)])
        content = output_path.read_text()
        for section in [
            "runner:",
            "eval:",
            "judge:",
            "trace:",
            "cost:",
            "safety:",
            "reporting:",
            "chaos:",
            "snapshot:",
            "budget:",
            "regression:",
            "metrics:",
            "plugins:",
        ]:
            assert section in content, f"Missing config section: {section}"

    def test_version_module_matches_cli(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])
        assert agentprobe.__version__ in result.output

    def test_init_skips_existing(self, tmp_path: Path) -> None:
        output_path = tmp_path / "agentprobe.yaml"
        output_path.write_text("existing", encoding="utf-8")
        runner = CliRunner()
        result = runner.invoke(cli, ["init", "-o", str(output_path)])
        assert result.exit_code == 0
        assert "already exists" in result.output

    def test_test_command_no_tests(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["test", "-d", str(tmp_path)])
        assert result.exit_code == 0
        assert "No test cases" in result.output

    def test_trace_list_no_db(self, tmp_path: Path) -> None:
        config_file = tmp_path / "agentprobe.yaml"
        config_file.write_text(
            f"trace:\n  database_path: {tmp_path / 'traces.db'}\n",
            encoding="utf-8",
        )
        runner = CliRunner()
        result = runner.invoke(cli, ["trace", "list", "-c", str(config_file)])
        assert result.exit_code == 0
        assert "No traces" in result.output

    def test_trace_show_not_found(self, tmp_path: Path) -> None:
        config_file = tmp_path / "agentprobe.yaml"
        config_file.write_text(
            f"trace:\n  database_path: {tmp_path / 'traces.db'}\n",
            encoding="utf-8",
        )
        runner = CliRunner()
        result = runner.invoke(cli, ["trace", "show", "nonexistent-id", "-c", str(config_file)])
        assert result.exit_code == 0
        assert "not found" in result.output
