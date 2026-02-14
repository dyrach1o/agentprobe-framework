"""Tests for the trace replay engine."""

from __future__ import annotations

from agentprobe.trace.replay import ReplayEngine
from tests.fixtures.traces import make_tool_call, make_trace


class TestReplayEngine:
    """Test ReplayEngine replay and diff operations."""

    def test_pure_replay_no_mocks(self) -> None:
        trace = make_trace(
            output_text="original",
            tool_calls=[make_tool_call(tool_name="search", tool_output="found")],
        )
        engine = ReplayEngine()
        replayed = engine.replay(trace)

        assert replayed.output_text == "original"
        assert replayed is trace  # No modification needed

    def test_mock_tool_override(self) -> None:
        trace = make_trace(
            tool_calls=[make_tool_call(tool_name="search", tool_output="found")],
        )
        engine = ReplayEngine(mock_tools={"search": lambda _: "mocked result"})
        replayed = engine.replay(trace)

        assert replayed.tool_calls[0].tool_output == "mocked result"
        assert replayed.tool_calls[0].success is True

    def test_mock_tool_error(self) -> None:
        trace = make_trace(
            tool_calls=[make_tool_call(tool_name="search")],
        )

        def _fail(_: object) -> str:
            msg = "mock failure"
            raise ValueError(msg)

        engine = ReplayEngine(mock_tools={"search": _fail})
        replayed = engine.replay(trace)

        assert replayed.tool_calls[0].success is False
        assert "Mock error" in (replayed.tool_calls[0].error or "")

    def test_mock_output_override(self) -> None:
        trace = make_trace(output_text="original output")
        engine = ReplayEngine(mock_output="overridden output")
        replayed = engine.replay(trace)

        assert replayed.output_text == "overridden output"

    def test_unmatched_tools_unchanged(self) -> None:
        trace = make_trace(
            tool_calls=[
                make_tool_call(tool_name="search", tool_output="found"),
                make_tool_call(tool_name="calc", tool_output="42"),
            ],
        )
        engine = ReplayEngine(mock_tools={"search": lambda _: "mocked"})
        replayed = engine.replay(trace)

        assert replayed.tool_calls[0].tool_output == "mocked"
        assert replayed.tool_calls[1].tool_output == "42"

    def test_empty_trace(self) -> None:
        trace = make_trace(tool_calls=[], output_text="")
        engine = ReplayEngine(mock_output="new")
        replayed = engine.replay(trace)
        assert replayed.output_text == "new"

    def test_diff_identical_traces(self) -> None:
        trace = make_trace(
            output_text="result",
            tool_calls=[make_tool_call(tool_name="search", tool_output="found")],
        )
        engine = ReplayEngine()
        diff = engine.diff(trace, trace)

        assert diff.output_matches is True
        assert len(diff.tool_call_diffs) == 1
        assert diff.tool_call_diffs[0].similarity == 1.0

    def test_diff_different_outputs(self) -> None:
        original = make_trace(output_text="original")
        replay = make_trace(output_text="different")
        engine = ReplayEngine()
        diff = engine.diff(original, replay)

        assert diff.output_matches is False
        assert diff.original_output == "original"
        assert diff.replay_output == "different"

    def test_diff_different_tool_counts(self) -> None:
        original = make_trace(
            tool_calls=[
                make_tool_call(tool_name="a"),
                make_tool_call(tool_name="b"),
            ],
        )
        replay = make_trace(tool_calls=[make_tool_call(tool_name="a")])
        engine = ReplayEngine()
        diff = engine.diff(original, replay)

        assert len(diff.tool_call_diffs) == 2
        assert diff.tool_call_diffs[1].similarity == 0.0

    def test_diff_empty_traces(self) -> None:
        trace = make_trace(tool_calls=[], output_text="out")
        engine = ReplayEngine()
        diff = engine.diff(trace, trace)

        assert diff.output_matches is True
        assert len(diff.tool_call_diffs) == 0

    def test_diff_partial_tool_match(self) -> None:
        original = make_trace(
            tool_calls=[make_tool_call(tool_name="search", tool_output="a")],
        )
        replay = make_trace(
            tool_calls=[make_tool_call(tool_name="search", tool_output="b")],
        )
        engine = ReplayEngine()
        diff = engine.diff(original, replay)

        # Same name, same input, different output -> 2/3 similarity
        assert diff.tool_call_diffs[0].similarity > 0.0
        assert diff.tool_call_diffs[0].similarity < 1.0
