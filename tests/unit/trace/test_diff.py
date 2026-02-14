"""Tests for the TraceDiffer."""

from __future__ import annotations

import pytest

from agentprobe.trace.diff import TraceDiffer
from tests.fixtures.traces import make_llm_call, make_tool_call, make_trace


class TestTraceDiffer:
    """Tests for TraceDiffer structural comparison."""

    @pytest.fixture
    def differ(self) -> TraceDiffer:
        return TraceDiffer()

    def test_identical_traces(self, differ: TraceDiffer) -> None:
        trace = make_trace(
            trace_id="t1",
            output_text="hello",
            tool_calls=[make_tool_call(tool_name="search")],
            llm_calls=[make_llm_call(input_tokens=100, output_tokens=50)],
        )
        report = differ.diff(trace, trace)
        assert report.output_matches is True
        assert report.token_delta == 0
        assert report.latency_delta_ms == 0
        assert report.overall_similarity == 1.0

    def test_different_outputs(self, differ: TraceDiffer) -> None:
        a = make_trace(trace_id="a", output_text="hello")
        b = make_trace(trace_id="b", output_text="goodbye")
        report = differ.diff(a, b)
        assert report.output_matches is False

    def test_different_tool_sequences(self, differ: TraceDiffer) -> None:
        a = make_trace(
            trace_id="a",
            tool_calls=[make_tool_call(tool_name="search"), make_tool_call(tool_name="calc")],
        )
        b = make_trace(
            trace_id="b",
            tool_calls=[make_tool_call(tool_name="calc"), make_tool_call(tool_name="search")],
        )
        report = differ.diff(a, b)
        assert len(report.tool_call_diffs) == 2
        # Names swapped, so similarities should be 2/3 each (input+output match, name differs)
        for d in report.tool_call_diffs:
            assert d.similarity < 1.0

    def test_different_tool_counts(self, differ: TraceDiffer) -> None:
        a = make_trace(
            trace_id="a",
            tool_calls=[make_tool_call(tool_name="search")],
        )
        b = make_trace(
            trace_id="b",
            tool_calls=[
                make_tool_call(tool_name="search"),
                make_tool_call(tool_name="calc"),
            ],
        )
        report = differ.diff(a, b)
        assert len(report.tool_call_diffs) == 2
        assert report.tool_call_diffs[1].expected is None
        assert report.tool_call_diffs[1].actual == "calc"

    def test_different_models_in_llm_calls(self, differ: TraceDiffer) -> None:
        a = make_trace(
            trace_id="a",
            llm_calls=[make_llm_call(model="model-a", input_tokens=100, output_tokens=50)],
        )
        b = make_trace(
            trace_id="b",
            llm_calls=[make_llm_call(model="model-b", input_tokens=200, output_tokens=100)],
        )
        report = differ.diff(a, b)
        total_a = 100 + 50
        total_b = 200 + 100
        assert report.token_delta == total_b - total_a

    def test_latency_delta(self, differ: TraceDiffer) -> None:
        a = make_trace(
            trace_id="a",
            llm_calls=[make_llm_call(latency_ms=100)],
        )
        b = make_trace(
            trace_id="b",
            llm_calls=[make_llm_call(latency_ms=300)],
        )
        report = differ.diff(a, b)
        assert report.latency_delta_ms == 200

    def test_empty_traces(self, differ: TraceDiffer) -> None:
        a = make_trace(trace_id="a", llm_calls=[], tool_calls=[], output_text="")
        b = make_trace(trace_id="b", llm_calls=[], tool_calls=[], output_text="")
        report = differ.diff(a, b)
        assert report.output_matches is True
        assert report.token_delta == 0
        assert report.overall_similarity == 1.0
        assert len(report.tool_call_diffs) == 0

    def test_overall_similarity_range(self, differ: TraceDiffer) -> None:
        a = make_trace(trace_id="a", output_text="hello")
        b = make_trace(trace_id="b", output_text="goodbye")
        report = differ.diff(a, b)
        assert 0.0 <= report.overall_similarity <= 1.0

    def test_similarity_threshold_default(self) -> None:
        differ = TraceDiffer()
        assert differ._threshold == 0.8

    def test_similarity_threshold_custom(self) -> None:
        differ = TraceDiffer(similarity_threshold=0.5)
        assert differ._threshold == 0.5

    def test_trace_ids_in_report(self, differ: TraceDiffer) -> None:
        a = make_trace(trace_id="trace-aaa")
        b = make_trace(trace_id="trace-bbb")
        report = differ.diff(a, b)
        assert report.trace_a_id == "trace-aaa"
        assert report.trace_b_id == "trace-bbb"
