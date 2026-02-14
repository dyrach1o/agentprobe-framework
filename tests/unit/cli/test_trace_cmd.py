"""Tests for the CLI trace commands."""

from __future__ import annotations

import asyncio
from pathlib import Path

from click.testing import CliRunner

from agentprobe.cli.main import cli
from agentprobe.storage.sqlite import SQLiteStorage
from tests.fixtures.traces import make_tool_call, make_trace


class TestTraceGroup:
    """Tests for the ``agentprobe trace`` CLI command group."""

    def test_help(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["trace", "--help"])

        assert result.exit_code == 0
        assert "trace" in result.output.lower()

    def test_list_subcommand_help(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["trace", "list", "--help"])

        assert result.exit_code == 0
        assert "list" in result.output.lower()

    def test_show_subcommand_help(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["trace", "show", "--help"])

        assert result.exit_code == 0
        assert "show" in result.output.lower()


class TestTraceList:
    """Tests for the ``agentprobe trace list`` command."""

    def _make_config(self, tmp_path: Path) -> Path:
        config = tmp_path / "agentprobe.yaml"
        config.write_text(
            f"trace:\n  database_path: {tmp_path / 'traces.db'}\n",
            encoding="utf-8",
        )
        return config

    def _seed_traces(self, db_path: Path, traces: list[object]) -> None:
        async def _run() -> None:
            storage = SQLiteStorage(db_path)
            await storage.setup()
            for trace in traces:
                await storage.save_trace(trace)  # type: ignore[arg-type]
            await storage.close()

        asyncio.run(_run())

    def test_empty_database_shows_no_traces(self, tmp_path: Path) -> None:
        config = self._make_config(tmp_path)
        runner = CliRunner()
        result = runner.invoke(cli, ["trace", "list", "-c", str(config)])

        assert result.exit_code == 0
        assert "No traces" in result.output

    def test_lists_stored_traces(self, tmp_path: Path) -> None:
        config = self._make_config(tmp_path)
        trace = make_trace(agent_name="my-agent", trace_id="abcdef1234567890")
        self._seed_traces(tmp_path / "traces.db", [trace])

        runner = CliRunner()
        result = runner.invoke(cli, ["trace", "list", "-c", str(config)])

        assert result.exit_code == 0
        assert "abcdef12" in result.output
        assert "my-agent" in result.output

    def test_filter_by_agent(self, tmp_path: Path) -> None:
        config = self._make_config(tmp_path)
        self._seed_traces(
            tmp_path / "traces.db",
            [make_trace(agent_name="agent-a"), make_trace(agent_name="agent-b")],
        )

        runner = CliRunner()
        result = runner.invoke(cli, ["trace", "list", "-c", str(config), "-a", "agent-a"])

        assert result.exit_code == 0
        assert "agent-a" in result.output

    def test_limit_option(self, tmp_path: Path) -> None:
        config = self._make_config(tmp_path)
        self._seed_traces(
            tmp_path / "traces.db",
            [make_trace(agent_name=f"agent-{i}") for i in range(5)],
        )

        runner = CliRunner()
        result = runner.invoke(cli, ["trace", "list", "-c", str(config), "-n", "2"])

        assert result.exit_code == 0
        lines = [line for line in result.output.strip().splitlines() if line.strip()]
        assert len(lines) == 2


class TestTraceShow:
    """Tests for the ``agentprobe trace show`` command."""

    def _make_config(self, tmp_path: Path) -> Path:
        config = tmp_path / "agentprobe.yaml"
        config.write_text(
            f"trace:\n  database_path: {tmp_path / 'traces.db'}\n",
            encoding="utf-8",
        )
        return config

    def _seed_trace(self, db_path: Path, trace: object) -> None:
        async def _run() -> None:
            storage = SQLiteStorage(db_path)
            await storage.setup()
            await storage.save_trace(trace)  # type: ignore[arg-type]
            await storage.close()

        asyncio.run(_run())

    def test_not_found(self, tmp_path: Path) -> None:
        config = self._make_config(tmp_path)
        runner = CliRunner()
        result = runner.invoke(cli, ["trace", "show", "nonexistent-id", "-c", str(config)])

        assert result.exit_code == 0
        assert "not found" in result.output

    def test_shows_trace_details(self, tmp_path: Path) -> None:
        config = self._make_config(tmp_path)
        trace = make_trace(
            agent_name="detail-agent",
            model="test-model",
            input_text="test input",
            output_text="test output",
            trace_id="deadbeef12345678",
            tags=["tag1", "tag2"],
        )
        self._seed_trace(tmp_path / "traces.db", trace)

        runner = CliRunner()
        result = runner.invoke(cli, ["trace", "show", "deadbeef12345678", "-c", str(config)])

        assert result.exit_code == 0
        assert "deadbeef12345678" in result.output
        assert "detail-agent" in result.output
        assert "test-model" in result.output
        assert "test input" in result.output
        assert "test output" in result.output
        assert "tag1" in result.output
        assert "tag2" in result.output

    def test_shows_tool_calls(self, tmp_path: Path) -> None:
        config = self._make_config(tmp_path)
        trace = make_trace(
            trace_id="toolcall12345678",
            tool_calls=[
                make_tool_call(tool_name="search_tool", success=True),
                make_tool_call(tool_name="broken_tool", success=False, error="timeout"),
            ],
        )
        self._seed_trace(tmp_path / "traces.db", trace)

        runner = CliRunner()
        result = runner.invoke(cli, ["trace", "show", "toolcall12345678", "-c", str(config)])

        assert result.exit_code == 0
        assert "Tool Calls:" in result.output
        assert "search_tool" in result.output
        assert "OK" in result.output
        assert "broken_tool" in result.output
        assert "FAIL" in result.output
        assert "timeout" in result.output

    def test_shows_no_model_as_na(self, tmp_path: Path) -> None:
        config = self._make_config(tmp_path)
        trace = make_trace(trace_id="nomodel123456789", model=None)
        self._seed_trace(tmp_path / "traces.db", trace)

        runner = CliRunner()
        result = runner.invoke(cli, ["trace", "show", "nomodel123456789", "-c", str(config)])

        assert result.exit_code == 0
        assert "N/A" in result.output
