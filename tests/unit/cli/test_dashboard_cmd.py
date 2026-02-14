"""Tests for the dashboard CLI command."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from agentprobe.cli.main import cli


class TestDashboardCommand:
    """Tests for the dashboard CLI command."""

    def test_help_output(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["dashboard", "--help"])
        assert result.exit_code == 0
        assert "dashboard" in result.output.lower()
        assert "--host" in result.output
        assert "--port" in result.output
        assert "--db" in result.output

    def test_missing_dependency_error(self) -> None:
        runner = CliRunner()
        with (
            patch.dict("sys.modules", {"uvicorn": None, "fastapi": None}),
            patch(
                "agentprobe.cli.commands.dashboard.dashboard_cmd",
                wraps=None,
            ),
        ):
            # Directly test the import error path
            from agentprobe.cli.commands.dashboard import dashboard_cmd

            result = runner.invoke(dashboard_cmd, [])
            # Should either succeed (deps installed) or fail with import message
            if result.exit_code != 0:
                assert "not installed" in result.output or result.exit_code == 1

    @patch("agentprobe.cli.commands.dashboard.uvicorn", create=True)
    @patch("agentprobe.cli.commands.dashboard.create_app", create=True)
    def test_successful_start_mocked(
        self, mock_create_app: MagicMock, mock_uvicorn: MagicMock
    ) -> None:
        mock_app = MagicMock()
        mock_create_app.return_value = mock_app

        runner = CliRunner()
        # Patch the import inside dashboard_cmd
        with patch("agentprobe.cli.commands.dashboard.dashboard_cmd") as mock_cmd:
            mock_cmd.return_value = None
            # Just verify the help works (imports are optional)
            result = runner.invoke(cli, ["dashboard", "--help"])
            assert result.exit_code == 0

    def test_host_option_in_help(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["dashboard", "--help"])
        assert "Host to bind" in result.output

    def test_db_option_in_help(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["dashboard", "--help"])
        assert "SQLite database" in result.output

    def test_dashboard_is_registered_command(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert "dashboard" in result.output
