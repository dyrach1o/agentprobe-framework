"""Tests for the snapshot manager."""

from __future__ import annotations

from pathlib import Path

import pytest

from agentprobe.core.exceptions import SnapshotError
from agentprobe.core.snapshot import SnapshotManager
from tests.fixtures.traces import make_llm_call, make_tool_call, make_trace


class TestSnapshotManager:
    """Tests for SnapshotManager."""

    @pytest.fixture
    def snapshot_dir(self, tmp_path: Path) -> Path:
        return tmp_path / "snapshots"

    @pytest.fixture
    def manager(self, snapshot_dir: Path) -> SnapshotManager:
        return SnapshotManager(snapshot_dir, threshold=0.8)

    def test_save_and_load_roundtrip(self, manager: SnapshotManager) -> None:
        trace = make_trace(
            agent_name="agent1",
            output_text="hello world",
            llm_calls=[make_llm_call(input_tokens=100, output_tokens=50)],
            tool_calls=[make_tool_call(tool_name="search")],
        )
        manager.save("test-snap", trace)
        loaded = manager.load("test-snap")

        assert loaded.agent_name == "agent1"
        assert loaded.output_text == "hello world"
        assert len(loaded.llm_calls) == 1
        assert len(loaded.tool_calls) == 1

    def test_load_nonexistent_raises(self, manager: SnapshotManager) -> None:
        with pytest.raises(SnapshotError, match="not found"):
            manager.load("nonexistent")

    def test_exists(self, manager: SnapshotManager) -> None:
        assert not manager.exists("test")
        manager.save("test", make_trace())
        assert manager.exists("test")

    def test_list_snapshots(self, manager: SnapshotManager) -> None:
        assert manager.list_snapshots() == []
        manager.save("alpha", make_trace())
        manager.save("beta", make_trace())
        names = manager.list_snapshots()
        assert names == ["alpha", "beta"]

    def test_list_snapshots_no_dir(self, tmp_path: Path) -> None:
        manager = SnapshotManager(tmp_path / "nonexistent")
        assert manager.list_snapshots() == []

    def test_delete(self, manager: SnapshotManager) -> None:
        manager.save("to-delete", make_trace())
        assert manager.delete("to-delete") is True
        assert not manager.exists("to-delete")

    def test_delete_nonexistent(self, manager: SnapshotManager) -> None:
        assert manager.delete("nonexistent") is False

    def test_compare_identical(self, manager: SnapshotManager) -> None:
        trace = make_trace(
            output_text="hello world",
            llm_calls=[make_llm_call(input_tokens=100, output_tokens=50)],
            tool_calls=[make_tool_call(tool_name="search")],
        )
        manager.save("golden", trace)
        diff = manager.compare("golden", trace)

        assert diff.is_match is True
        assert diff.overall_similarity >= 0.8
        assert diff.snapshot_name == "golden"

    def test_compare_different_tools(self, manager: SnapshotManager) -> None:
        baseline = make_trace(
            output_text="result",
            tool_calls=[
                make_tool_call(tool_name="search"),
                make_tool_call(tool_name="calc"),
            ],
        )
        current = make_trace(
            output_text="result",
            tool_calls=[
                make_tool_call(tool_name="search"),
                make_tool_call(tool_name="database"),
            ],
        )
        manager.save("golden", baseline)
        diff = manager.compare("golden", current)

        tool_diff = next(d for d in diff.diffs if d.dimension == "tool_calls")
        assert tool_diff.similarity == 0.5

    def test_compare_different_output(self, manager: SnapshotManager) -> None:
        baseline = make_trace(output_text="the quick brown fox")
        current = make_trace(output_text="completely different text here")
        manager.save("golden", baseline)
        diff = manager.compare("golden", current)

        output_diff = next(d for d in diff.diffs if d.dimension == "output")
        assert output_diff.similarity < 1.0

    def test_compare_nonexistent_raises(self, manager: SnapshotManager) -> None:
        with pytest.raises(SnapshotError):
            manager.compare("nonexistent", make_trace())

    def test_compare_empty_traces(self, manager: SnapshotManager) -> None:
        baseline = make_trace(output_text="", tool_calls=[])
        manager.save("empty", baseline)
        diff = manager.compare("empty", make_trace(output_text="", tool_calls=[]))

        assert diff.overall_similarity >= 0.8

    def test_update_all(self, manager: SnapshotManager) -> None:
        traces = {
            "snap1": make_trace(output_text="out1"),
            "snap2": make_trace(output_text="out2"),
            "snap3": make_trace(output_text="out3"),
        }
        count = manager.update_all(traces)
        assert count == 3
        assert manager.list_snapshots() == ["snap1", "snap2", "snap3"]

    def test_compare_dimensions_present(self, manager: SnapshotManager) -> None:
        trace = make_trace(
            llm_calls=[make_llm_call(input_tokens=100)],
            tool_calls=[make_tool_call()],
        )
        manager.save("golden", trace)
        diff = manager.compare("golden", trace)

        dimensions = {d.dimension for d in diff.diffs}
        assert "tool_calls" in dimensions
        assert "output" in dimensions
        assert "token_usage" in dimensions
        assert "latency" in dimensions
