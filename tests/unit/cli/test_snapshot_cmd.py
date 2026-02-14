"""Tests for the snapshot CLI commands."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from agentprobe.cli.main import cli
from agentprobe.core.snapshot import SnapshotManager
from tests.fixtures.traces import make_trace


class TestSnapshotCLI:
    """Tests for snapshot CLI commands."""

    def test_snapshot_help(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["snapshot", "--help"])
        assert result.exit_code == 0
        assert "snapshot" in result.output.lower()

    def test_snapshot_list_empty(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["snapshot", "list", "-d", str(tmp_path / "snapshots")])
        assert result.exit_code == 0
        assert "No snapshots" in result.output

    def test_snapshot_list_with_data(self, tmp_path: Path) -> None:
        snapshots_dir = tmp_path / "snapshots"
        manager = SnapshotManager(snapshots_dir)
        trace = make_trace(agent_name="test-agent")
        manager.save("snap-1", trace)

        runner = CliRunner()
        result = runner.invoke(cli, ["snapshot", "list", "-d", str(snapshots_dir)])
        assert result.exit_code == 0
        assert "snap-1" in result.output

    def test_snapshot_delete(self, tmp_path: Path) -> None:
        snapshots_dir = tmp_path / "snapshots"
        manager = SnapshotManager(snapshots_dir)
        trace = make_trace(agent_name="test-agent")
        manager.save("snap-1", trace)

        runner = CliRunner()
        result = runner.invoke(
            cli, ["snapshot", "delete", "snap-1", "-d", str(snapshots_dir), "--yes"]
        )
        assert result.exit_code == 0
        assert "Deleted" in result.output

    def test_snapshot_delete_not_found(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            cli, ["snapshot", "delete", "nonexistent", "-d", str(tmp_path), "--yes"]
        )
        assert result.exit_code == 0
        assert "not found" in result.output

    def test_snapshot_diff(self, tmp_path: Path) -> None:
        snapshots_dir = tmp_path / "snapshots"
        manager = SnapshotManager(snapshots_dir)
        trace = make_trace(agent_name="test-agent")
        manager.save("snap-1", trace)

        runner = CliRunner()
        result = runner.invoke(cli, ["snapshot", "diff", "snap-1", "-d", str(snapshots_dir)])
        assert result.exit_code == 0
        assert "test-agent" in result.output

    def test_snapshot_diff_not_found(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["snapshot", "diff", "missing", "-d", str(tmp_path)])
        assert result.exit_code == 0
        assert "not found" in result.output
