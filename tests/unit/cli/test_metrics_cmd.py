"""Tests for the metrics CLI commands."""

from __future__ import annotations

from click.testing import CliRunner

from agentprobe.cli.main import cli


class TestMetricsCLI:
    """Tests for metrics CLI commands."""

    def test_metrics_help(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["metrics", "--help"])
        assert result.exit_code == 0
        assert "metrics" in result.output.lower()

    def test_metrics_list(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["metrics", "list"])
        assert result.exit_code == 0
        assert "Built-in Metrics" in result.output
        assert "latency_ms" in result.output
        assert "Total:" in result.output

    def test_metrics_list_shows_all_builtins(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["metrics", "list"])
        assert result.exit_code == 0
        for name in [
            "latency_ms",
            "token_cost_usd",
            "tool_call_count",
            "response_length",
            "eval_score",
            "pass_rate",
        ]:
            assert name in result.output

    def test_metrics_summary_default(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["metrics", "summary"])
        assert result.exit_code == 0
        assert "Metrics Summary" in result.output

    def test_metrics_summary_with_filter(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["metrics", "summary", "-m", "latency_ms"])
        assert result.exit_code == 0
        assert "latency_ms" in result.output
